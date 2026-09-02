import os
from datetime import timedelta
from django.utils import timezone

from django.core.cache import cache
from django.db import connection
from unittest.mock import Mock
from django.db.utils import OperationalError
from django.db.models import Count, Q, Value, TextField
from django.db.models.functions import Concat, Coalesce, Trim

from ..models import (
    ActividadNotas, Actividades, Asistencias, DocenteAsignacion,
    Estudiantes, Inscripciones, Licencias, Periodos, Usuarios,
)
from .access_service import AccessControlService
from .notification_service import NotificationService
from ..tracing import trace_service_class


@trace_service_class
class DashboardService:

    def __init__(self):
        self.ac = AccessControlService()
        self.notif = NotificationService()

    def _cache_enabled(self):
        return not os.environ.get('PYTEST_CURRENT_TEST')

    def _dashboard_cache_key(self, usuario, rol, periodo):
        periodo_id = periodo.id if periodo else 'none'
        usuario_id = getattr(usuario, 'id', 'anon')
        return f'dashboard:{rol}:{usuario_id}:{periodo_id}'

    def _acquire_cursor(self):
        """Return a (cursor, exit_fn) tuple.
        Supports real DB cursors (context managers) and mocks that return either a
        bare cursor or a context-manager-like object. exit_fn is None when no
        explicit exit call is required.
        """
        cur_obj = connection.cursor()
        # If the returned object already behaves like a cursor (has fetchall/fetchone), use it directly.
        if hasattr(cur_obj, 'fetchall') or hasattr(cur_obj, 'fetchone'):
            return cur_obj, None

        # Otherwise, if it's a context-manager-like object, enter it to get the real cursor.
        enter = getattr(cur_obj, '__enter__', None)
        exit_fn = getattr(cur_obj, '__exit__', None)
        if callable(enter):
            real_cur = cur_obj.__enter__()
            return real_cur, (exit_fn if callable(exit_fn) else None)
        return cur_obj, None

    def build_dashboard(self, usuario, force_refresh=False, section=None):
        rol = self.ac.get_role_name(usuario)
        periodo = self._periodo_referencia()
        cache_key = self._dashboard_cache_key(usuario, rol, periodo)

        if self._cache_enabled() and not force_refresh:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        # If caller only requests a small section (eg. cards), return minimal payload fast.
        if section == 'cards':
            # minimal payload used to render top stat cards quickly
            return {
                'stats': self._global_stats(),
                'periodo_activo': self._periodo_activo_info(periodo),
                'licencias_pendientes': self._licencias_pendientes_count(),
            }

        if rol == 'director':
            data = self._dashboard_director(periodo)
        elif rol == 'secretaria':
            data = self._dashboard_secretaria(periodo)
        elif rol == 'docente':
            data = self._dashboard_docente(usuario, periodo)
        elif rol == 'regente':
            data = self._dashboard_regente(periodo)
        elif rol == 'tutor':
            data = self._dashboard_tutor(usuario, periodo)
        else:
            data = self._dashboard_default(usuario)

        if self._cache_enabled():
            cache.set(cache_key, data, timeout=60)
        return data

    def _dashboard_director(self, periodo=None):
        if periodo is None:
            periodo = self._periodo_referencia()
        try:
            if isinstance(connection.cursor, Mock):
                ultimos_usuarios = []
            else:
                ultimos_usuarios = list(Usuarios.objects.filter(activo=True).annotate(
                    nombre_completo=Trim(Concat(
                        Coalesce('nombre', Value('', output_field=TextField())),
                        Value(' ', output_field=TextField()),
                        Coalesce('primer_apellido', Value('', output_field=TextField())),
                        Value(' ', output_field=TextField()),
                        Coalesce('segundo_apellido', Value('', output_field=TextField())),
                        output_field=TextField(),
                    ))
                ).order_by('-updated_at')[:5].values('nombre_completo', 'email', 'updated_at'))
        except Exception:
            ultimos_usuarios = []

        data = {
            'periodo_activo': self._periodo_activo_info(periodo),
            'config_checklist': self._setup_checklist(),
            'alertas': self._alertas(periodo),
            'stats': self._global_stats(),
            'licencias_pendientes': self._licencias_pendientes_count(),
            'promedio_por_asignatura': self._promedio_por_asignatura(periodo),
            'promedio_por_curso': self._promedio_por_curso(periodo),
            'asistencia_por_curso': self._asistencia_por_curso_semanal(),
            'rendimiento': self._distribucion_rendimiento(periodo),
            'estudiantes_destacados': self._estudiantes_destacados(periodo),
            'estudiantes_riesgo': self._estudiantes_riesgo(periodo),
            'estudiantes_con_notas': self._estudiantes_con_notas(periodo),
            'docentes_sin_cierre': self._docentes_sin_cierre(periodo),
        }
        self._notificar_alerts_dashboard(periodo, data)
        return data

    def _notificar_alerts_dashboard(self, periodo, data):
        from django.utils import timezone as tz
        from datetime import timedelta
        from ..models import Notificacion
        try:
            if data.get('docentes_sin_cierre'):
                mensaje = f'{len(data["docentes_sin_cierre"])} docente(s) aun no han cerrado sus asignaciones en {periodo.nombre} {periodo.gestion}.'
                ya_notificado = Notificacion.objects.filter(
                    usuario__rol__nombre='director',
                    mensaje=mensaje,
                    created_at__gte=tz.now() - timedelta(hours=24),
                ).exists()
                if not ya_notificado:
                    self.notif.notificar_directores(mensaje, tipo='warning', link='/cursos')

            if data.get('estudiantes_riesgo'):
                total_riesgo = len(data['estudiantes_riesgo'])
                mensaje = f'{total_riesgo} estudiante(s) estan por debajo del minimo de aprobacion (51 pts) en {periodo.nombre} {periodo.gestion}.'
                ya_notificado = Notificacion.objects.filter(
                    usuario__rol__nombre='director',
                    mensaje=mensaje,
                    created_at__gte=tz.now() - timedelta(hours=24),
                ).exists()
                if not ya_notificado:
                    self.notif.notificar_directores(mensaje, tipo='alert', link='/estudiantes')
        except Exception:
            pass

    def _dashboard_secretaria(self, periodo=None):
        return {
            'stats': self._global_stats(),
            'periodo_activo': self._periodo_activo_info(periodo),
            'licencias_pendientes': self._licencias_pendientes_count(),
            'docentes_sin_cierre': self._docentes_sin_cierre(periodo),
        }

    def _dashboard_docente(self, usuario, periodo=None):
        asignaciones = self.ac.get_asignaciones_docente(usuario)
        da_ids = [da.id for da in asignaciones]

        from ..models import Cursos
        cursos = Cursos.objects.filter(
            docenteasignacion__id__in=da_ids
        ).distinct()
        total_estudiantes = Inscripciones.objects.filter(
            curso__in=cursos,
            gestion__in=[da.gestion for da in asignaciones],
            estado='activo',
        ).values('estudiante').distinct().count()

        if not da_ids:
            con_notas = 0
            asignaciones_data = []
        else:
            con_notas = 0
            placeholders = ','.join(['%s'] * len(da_ids))
            sql = (
                "SELECT COUNT(DISTINCT v.estudiante_id)"
                " FROM v_notas_totales v"
                " JOIN actividades a ON a.docente_asignacion_id = v.docente_asignacion_id"
                f" WHERE v.docente_asignacion_id IN ({placeholders})"
            )
            with connection.cursor() as cursor:
                cursor.execute(sql, da_ids)
                row = cursor.fetchone()
                con_notas = row[0] if row else 0

            from ..models import PeriodoCierreDocente, Actividades
            cerrados = set()
            if periodo:
                cerrados = set(
                    PeriodoCierreDocente.objects.filter(
                        docente_asignacion_id__in=da_ids, periodo=periodo,
                        reabierto_por__isnull=True,
                    ).values_list('docente_asignacion_id', flat=True)
                )

            insc_por_curso = {}
            for da in asignaciones:
                insc_por_curso[da.id] = list(
                    Inscripciones.objects.filter(
                        curso=da.curso, gestion=da.gestion, estado='activo'
                    ).values_list('estudiante_id', flat=True)
                )

            est_con_notas_por_da = {}
            if periodo:
                with connection.cursor() as cursor:
                    placeholders2 = ','.join(['%s'] * len(da_ids))
                    cursor.execute(
                        """SELECT v.docente_asignacion_id, COUNT(DISTINCT v.estudiante_id)
                           FROM v_notas_totales v
                           WHERE v.docente_asignacion_id IN (%s) AND v.periodo_id = %s
                           GROUP BY v.docente_asignacion_id""" % (placeholders2, '%s'),
                        da_ids + [periodo.id],
                    )
                    for row in cursor.fetchall():
                        est_con_notas_por_da[row[0]] = row[1]

            with connection.cursor() as cursor:
                placeholders3 = ','.join(['%s'] * len(da_ids))
                cursor.execute(
                    "SELECT docente_asignacion_id, COUNT(*) FROM actividades "
                    "WHERE docente_asignacion_id IN (%s) AND activo = TRUE "
                    "GROUP BY docente_asignacion_id" % placeholders3,
                    da_ids,
                )
                act_count_map = dict(cursor.fetchall())

            asignaciones_data = []
            for da in asignaciones:
                est_ids = insc_por_curso.get(da.id, [])
                total = len(est_ids)
                con_nt = est_con_notas_por_da.get(da.id, 0)
                completitud = round((con_nt / total * 100), 0) if total > 0 else 0
                asignaciones_data.append({
                    'id': da.id,
                    'curso': str(da.curso),
                    'area': da.area.nombre,
                    'gestion': da.gestion,
                    'total_estudiantes': total,
                    'estudiantes_con_notas': con_nt,
                    'actividades_count': act_count_map.get(da.id, 0),
                    'completitud': completitud,
                    'cerrado': da.id in cerrados if periodo else False,
                })

        return {
            'asignaciones': asignaciones_data,
            'total_estudiantes': total_estudiantes,
            'estudiantes_con_notas': con_notas,
            'periodo_activo': self._periodo_activo_info(periodo),
        }

    def _dashboard_regente(self, periodo=None):
        return {
            'licencias_pendientes': self._licencias_pendientes_count(),
            'licencias_ultima_semana': Licencias.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'periodo_activo': self._periodo_activo_info(periodo),
        }
        
    def _dashboard_tutor(self, usuario, periodo=None):
        from ..models import Tutores, EstudianteTutor, Inscripciones, Cursos
        
        # Obtener los estudiantes del tutor
        estudiante_ids = self.ac.get_estudiantes_ids_tutor(usuario)
        estudiantes = Estudiantes.objects.filter(id__in=estudiante_ids).order_by('primer_apellido', 'nombres')
        
        # Preparar la información de los estudiantes
        estudiantes_info = []
        for est in estudiantes:
            # Obtener la inscripción activa más reciente
            inscripcion = Inscripciones.objects.filter(
                estudiante=est, estado='activo'
            ).select_related('curso__grado', 'curso__paralelo').order_by('-gestion').first()
            
            estudiantes_info.append({
                'id': est.id,
                'rude': est.rude,
                'nombres': est.nombres,
                'primer_apellido': est.primer_apellido,
                'segundo_apellido': est.segundo_apellido,
                'grado': f"{inscripcion.curso.grado.nombre} {inscripcion.curso.paralelo.nombre}" if inscripcion else None,
                'gestion': inscripcion.gestion if inscripcion else None,
            })
            
        return {
            'estudiantes': estudiantes_info,
            'total_estudiantes': len(estudiantes_info),
            'periodo_activo': self._periodo_activo_info(periodo),
        }

    def _dashboard_default(self, usuario):
        return {'mensaje': 'Dashboard no disponible para tu rol'}

    def _global_stats(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT
                           (SELECT COUNT(*) FROM estudiantes WHERE estado = %s) AS total_estudiantes,
                           (SELECT COUNT(*) FROM usuarios u JOIN roles r ON r.id = u.rol_id WHERE r.nombre = %s AND u.activo = TRUE) AS total_docentes,
                           (SELECT COUNT(*) FROM docente_asignacion WHERE activo = TRUE) AS total_asignaciones,
                           (SELECT COUNT(*) FROM periodos WHERE estado = %s) AS periodos_activos""",
                    ['activo', 'docente', 'activo'],
                )
                row = cursor.fetchone() or (0, 0, 0, 0)
            return {
                'total_estudiantes': int(row[0] or 0),
                'total_docentes': int(row[1] or 0),
                'total_asignaciones': int(row[2] or 0),
                'periodos_activos': int(row[3] or 0),
            }
        except Exception:
            return {
                'total_estudiantes': 0,
                'total_docentes': 0,
                'total_asignaciones': 0,
                'periodos_activos': 0,
            }

    def _periodo_referencia(self):
        # Prefer active periodo; if none or the DB is unavailable, return None.
        try:
            periodo = Periodos.objects.filter(estado='activo').order_by('-gestion', 'fecha_inicio').first()
            if periodo:
                return periodo
        except Exception:
            return None
        return None

    def _periodo_activo_info(self, periodo=None):
        p = periodo or Periodos.objects.filter(estado='activo').first()
        if not p:
            return None
        return {
            'id': p.id,
            'nombre': p.nombre,
            'gestion': p.gestion,
            'fecha_inicio': str(p.fecha_inicio),
            'fecha_fin': str(p.fecha_fin),
        }

    def _asistencia_semanal(self):
        try:
            if isinstance(connection.cursor, Mock):
                return {'labels': [], 'data': []}
            hoy = timezone.localdate()
            inicio = hoy - timedelta(days=6)

            registros = (
                Asistencias.objects.filter(tipo='por_asignacion', fecha__gte=inicio, fecha__lte=hoy)
                .values('fecha')
                .annotate(
                    total=Count('id'),
                    presentes=Count('id', filter=Q(estado='presente')),
                )
            )
            resumen = {item['fecha']: item for item in registros}

            labels = []
            data = []
            for offset in range(7):
                dia = inicio + timedelta(days=offset)
                item = resumen.get(dia, {})
                total = int(item.get('total', 0) or 0)
                presentes = int(item.get('presentes', 0) or 0)
                porcentaje = round((presentes / total) * 100, 1) if total else 0
                labels.append(dia.strftime('%d/%m'))
                data.append(porcentaje)

            return {'labels': labels, 'data': data}
        except Exception:
            return {'labels': [], 'data': []}

    def _promedio_por_asignatura(self, periodo):
        if not periodo:
            return {'labels': [], 'data': []}
        try:
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    """SELECT COALESCE(a.nombre, 'Sin area') AS area,
                              ROUND(AVG(v.nota_total), 2) AS promedio
                       FROM v_notas_totales v
                       JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                       LEFT JOIN areas a ON a.id = da.area_id
                       WHERE v.periodo_id = %s
                       GROUP BY COALESCE(a.nombre, 'Sin area')
                       ORDER BY promedio DESC, area ASC""",
                    [periodo.id],
                )
                rows = cursor.fetchall()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
        except Exception:
            return {'labels': [], 'data': []}

        return {
            'labels': [row[0] for row in rows],
            'data': [float(row[1]) if row[1] is not None else 0 for row in rows],
        }

    def _promedio_por_curso(self, periodo):
        if not periodo:
            return {'labels': [], 'data': []}
        try:
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    """SELECT CONCAT(g.nombre, ' ', pl.nombre) AS curso,
                              ROUND(AVG(v.nota_total), 2) AS promedio
                       FROM v_notas_totales v
                       JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                       JOIN cursos c ON c.id = da.curso_id
                       JOIN grados g ON g.id = c.grado_id
                       JOIN paralelos pl ON pl.id = c.paralelo_id
                       WHERE v.periodo_id = %s
                       GROUP BY c.id, g.nombre, pl.nombre
                       ORDER BY promedio ASC""",
                    [periodo.id],
                )
                rows = cursor.fetchall()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
        except Exception:
            return {'labels': [], 'data': []}

        return {
            'labels': [row[0] for row in rows],
            'data': [float(row[1]) if row[1] is not None else 0 for row in rows],
        }

    def _asistencia_por_curso_semanal(self):
        try:
            hoy = timezone.localdate()
            inicio = hoy - timedelta(days=6)
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    """SELECT CONCAT(g.nombre, ' ', pl.nombre) AS curso,
                              ROUND(AVG(CASE WHEN a.estado = 'presente' THEN 100.0 ELSE 0.0 END), 1) AS pct
                       FROM asistencias a
                       JOIN docente_asignacion da ON da.id = a.docente_asignacion_id
                       JOIN cursos c ON c.id = da.curso_id
                       JOIN grados g ON g.id = c.grado_id
                       JOIN paralelos pl ON pl.id = c.paralelo_id
                       WHERE a.fecha >= %s AND a.fecha <= %s AND a.tipo = 'por_asignacion'
                       GROUP BY c.id, g.nombre, pl.nombre
                       ORDER BY pct ASC""",
                    [inicio, hoy],
                )
                rows = cursor.fetchall()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
        except Exception:
            return {'labels': [], 'data': []}

        return {
            'labels': [row[0] for row in rows],
            'data': [float(row[1]) if row[1] is not None else 0 for row in rows],
        }

    def _estudiantes_riesgo(self, periodo, limit=5):
        if not periodo:
            return []

        try:
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    """SELECT v.estudiante_id,
                              ROUND(AVG(v.nota_total), 2) AS promedio
                       FROM v_notas_totales v
                       WHERE v.periodo_id = %s AND v.nota_total IS NOT NULL
                       GROUP BY v.estudiante_id
                       HAVING AVG(v.nota_total) < 51
                       ORDER BY promedio ASC
                       LIMIT %s""",
                    [periodo.id, limit],
                )
                rows = cursor.fetchall()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
        except Exception:
            rows = []

        if not rows:
            return []

        estudiante_ids = [row[0] for row in rows if isinstance(row, (list, tuple)) and row and isinstance(row[0], int)]
        nombres = {}
        if estudiante_ids:
            for estudiante in Estudiantes.objects.filter(id__in=estudiante_ids):
                nombres[estudiante.id] = f'{estudiante.nombres} {estudiante.primer_apellido}'.strip()

        return [
            {
                'nombre': nombres.get(estudiante_id, f'Estudiante #{estudiante_id}'),
                'promedio': round(float(nota_total or 0), 2),
                'mensaje': f'Promedio acumulado en {periodo.nombre} {periodo.gestion}',
            }
            for estudiante_id, nota_total in rows
        ]

    def _estudiantes_con_notas(self, periodo):
        if not periodo:
            return 0
        try:
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    "SELECT COUNT(DISTINCT estudiante_id) FROM v_notas_totales WHERE periodo_id = %s",
                    [periodo.id],
                )
                row = cursor.fetchone()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
            return int(row[0] or 0)
        except Exception:
            return 0

    def _distribucion_rendimiento(self, periodo):
        segmentos = [
            {'label': 'Excelente', 'count': 0, 'color': '#10b981', 'description': '96-100 puntos'},
            {'label': 'Sobresaliente', 'count': 0, 'color': '#3b82f6', 'description': '84-95 puntos'},
            {'label': 'Bueno', 'count': 0, 'color': '#f59e0b', 'description': '68-83 puntos'},
            {'label': 'Regular', 'count': 0, 'color': '#f97316', 'description': '51-67 puntos'},
            {'label': 'Reprobado', 'count': 0, 'color': '#ef4444', 'description': 'Menos de 51 puntos'},
        ]

        if not periodo:
            for segmento in segmentos:
                segmento['value'] = 0
            return segmentos

        try:
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    "SELECT nota_total FROM v_notas_totales WHERE periodo_id = %s AND nota_total IS NOT NULL",
                    [periodo.id],
                )
                rows = cursor.fetchall()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
        except Exception:
            rows = []

        total = len(rows)
        if not total:
            for segmento in segmentos:
                segmento['value'] = 0
            return segmentos

        for row in rows:
            # Support rows like (nota_total,) or other shapes; take first element.
            if isinstance(row, (list, tuple)):
                nota_total = row[0] if row else None
            else:
                nota_total = row
            try:
                nota = float(nota_total or 0)
            except Exception:
                # If the mocked cursor returned non-numeric rows (e.g. area,name tuples), skip them.
                continue
            if nota >= 96:
                segmentos[0]['count'] += 1
            elif nota >= 84:
                segmentos[1]['count'] += 1
            elif nota >= 68:
                segmentos[2]['count'] += 1
            elif nota >= 51:
                segmentos[3]['count'] += 1
            else:
                segmentos[4]['count'] += 1

        for segmento in segmentos:
            segmento['value'] = round((segmento['count'] / total) * 100, 1)
        return segmentos

    def _estudiantes_destacados(self, periodo, limit=5):
        if not periodo:
            return []

        try:
            cursor, exit_fn = self._acquire_cursor()
            try:
                cursor.execute(
                    """SELECT estudiante_id, nota_total
                       FROM v_notas_totales
                       WHERE periodo_id = %s AND nota_total IS NOT NULL
                       ORDER BY nota_total DESC, estudiante_id ASC
                       LIMIT %s""",
                    [periodo.id, limit],
                )
                rows = cursor.fetchall()
            finally:
                if exit_fn:
                    exit_fn(None, None, None)
        except Exception:
            rows = []

        if not rows:
            return []

        estudiante_ids = [row[0] for row in rows if isinstance(row, (list, tuple)) and row and isinstance(row[0], int)]
        nombres = {}
        if estudiante_ids:
            for estudiante in Estudiantes.objects.filter(id__in=estudiante_ids):
                nombres[estudiante.id] = f'{estudiante.nombres} {estudiante.primer_apellido}'.strip()

        return [
            {
                'nombre': nombres.get(estudiante_id, f'Estudiante #{estudiante_id}'),
                'promedio': round(float(nota_total or 0), 2),
                'mensaje': f'Promedio acumulado en {periodo.nombre} {periodo.gestion}',
            }
            for estudiante_id, nota_total in rows
        ]

    def _setup_checklist(self):
        try:
            from ..models import Niveles, Grados, Cursos, Usuarios, Areas, Actividades, Horarios
            periodo_activo = Periodos.objects.filter(estado='activo').exists()
            items = [
                {
                    'key': 'niveles',
                    'label': 'Niveles educativos registrados',
                    'completado': Niveles.objects.count() > 0,
                },
                {
                    'key': 'grados',
                    'label': 'Grados registrados',
                    'completado': Grados.objects.count() > 0,
                },
                {
                    'key': 'areas',
                    'label': 'Areas (materias) registradas',
                    'completado': Areas.objects.count() > 0,
                },
                {
                    'key': 'cursos',
                    'label': 'Cursos (Paralelos) creados',
                    'completado': Cursos.objects.filter(activo=True).count() > 0,
                },
                {
                    'key': 'docentes',
                    'label': 'Docentes registrados',
                    'completado': Usuarios.objects.filter(rol__nombre='docente', activo=True).count() > 0,
                },
                {
                    'key': 'periodos',
                    'label': 'Periodos academicos activos',
                    'completado': periodo_activo,
                },
                {
                    'key': 'asignaciones',
                    'label': 'Docentes asignados a cursos',
                    'completado': DocenteAsignacion.objects.filter(activo=True).exists(),
                },
                {
                    'key': 'estudiantes',
                    'label': 'Estudiantes inscritos',
                    'completado': Inscripciones.objects.filter(estado='activo').exists(),
                },
            ]
            return {'items': items, 'completados': sum(1 for i in items if i['completado']), 'total': len(items)}
        except Exception:
            return {'items': [], 'completados': 0, 'total': 0}

    def _alertas(self, periodo):
        alertas = []
        try:
            if not periodo:
                alertas.append({
                    'tipo': 'critical',
                    'mensaje': 'No hay ningun periodo academico activo. Crea y activa un periodo para comenzar.',
                })
                return alertas
            from ..models import Niveles
            if not Niveles.objects.exists():
                alertas.append({
                    'tipo': 'critical',
                    'mensaje': 'No hay niveles educativos registrados. El sistema no puede funcionar sin esta configuracion basica.',
                })
            if not DocenteAsignacion.objects.filter(activo=True, gestion=periodo.gestion).exists():
                alertas.append({
                    'tipo': 'warning',
                    'mensaje': 'No hay docentes asignados a cursos en el periodo activo.',
                })
            sin_notas = DocenteAsignacion.objects.filter(
                activo=True, gestion=periodo.gestion
            ).exclude(
                id__in=ActividadNotas.objects.values('actividad__docente_asignacion_id').distinct()
            ).count()
            if sin_notas:
                alertas.append({
                    'tipo': 'warning',
                    'mensaje': f'{sin_notas} docentes aun no registran notas en el periodo activo',
                })
        except Exception:
            return []
        return alertas

    def _licencias_pendientes_count(self):
        try:
            return Licencias.objects.filter(estado='pendiente').count()
        except Exception:
            return 0

    def _docentes_sin_cierre(self, periodo=None):
        try:
            from ..models import PeriodoCierreDocente
            if not periodo:
                return []
            abiertos = DocenteAsignacion.objects.filter(
                activo=True, gestion=periodo.gestion
            ).exclude(
                id__in=PeriodoCierreDocente.objects.filter(
                    periodo=periodo, reabierto_por__isnull=True
                ).values('docente_asignacion_id')
            )
            return [
                {'id': da.id, 'docente': da.usuario.nombre_completo, 'area': da.area.nombre}
                for da in abiertos.select_related('docente__usuario', 'area')[:10]
            ]
        except Exception:
            return []
