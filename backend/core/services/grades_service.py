from django.db import connection
from django.db.models import Avg
from django.utils import timezone

from ..models import (
    Actividades, ActividadNotas, DimensionConfigPeriodo,
    DimensionesEvaluacion, DocenteAsignacion, Estudiantes,
    Grados, Inscripciones, Periodos, Asistencias,
)
from .access_service import AccessControlService
from ..tracing import trace_service_class


@trace_service_class
class GradesService:

    def __init__(self):
        self.ac = AccessControlService()

    def _ensure_auto_actividad(self, docente_asignacion_id, periodo_id):
        dimension = DimensionesEvaluacion.objects.filter(
            nombre__iexact='AUTOEVALUACION', activo=True
        ).first()
        if not dimension:
            return None
        config = DimensionConfigPeriodo.objects.filter(
            periodo_id=periodo_id, dimension=dimension
        ).first()
        puntaje_maximo = float(config.puntaje_maximo) if config and config.puntaje_maximo else (
            float(dimension.puntaje_maximo) if dimension.puntaje_maximo else 5
        )
        actividad, _ = Actividades.objects.get_or_create(
            docente_asignacion_id=docente_asignacion_id,
            periodo_id=periodo_id,
            dimension=dimension,
            defaults={
                'nombre': 'AUTOEVALUACION',
                'puntaje_maximo': puntaje_maximo,
                'fecha_actividad': timezone.now().date(),
            },
        )
        return actividad.id

    def get_course_detail(self, usuario, docente_asignacion_id, periodo_id=None):
        da = DocenteAsignacion.objects.select_related(
            'curso__grado__nivel', 'curso__paralelo', 'area'
        ).get(id=docente_asignacion_id)

        if not self.ac.puede_editar_notas(usuario, docente_asignacion_id):
            raise PermissionError('No tienes permisos para ver este curso')

        gestion = da.gestion
        estudiantes = self._get_estudiantes_curso(da.curso, gestion)
        periodos = self._list_periodos(gestion)
        if not periodo_id:
            periodo_activo = next((p for p in periodos if p['estado'] == 'activo'), periodos[0] if periodos else None)
            periodo_id = periodo_activo['id'] if periodo_activo else None
        dimensiones = self._list_dimensiones(periodo_id)
        if periodo_id:
            self._ensure_auto_actividad(docente_asignacion_id, periodo_id)
        from .activity_service import ActivityService
        actividades = ActivityService()._list_actividades(docente_asignacion_id)
        actividad_notas = self._get_actividad_notas_map(docente_asignacion_id)
        notas_dimension = self._get_notas_dimension(docente_asignacion_id, periodo_id)

        # Compute rendimiento (average of actividad notas) and asistencia (%) for this docente asignacion
        try:
            rendimiento_agg = ActividadNotas.objects.filter(actividad__docente_asignacion_id=docente_asignacion_id).aggregate(promedio=Avg('valor'))
            rendimiento = round(float(rendimiento_agg['promedio']), 1) if rendimiento_agg and rendimiento_agg['promedio'] is not None else None
        except Exception:
            rendimiento = None

        try:
            total_asist = Asistencias.objects.filter(docente_asignacion_id=docente_asignacion_id).count()
            presentes = Asistencias.objects.filter(docente_asignacion_id=docente_asignacion_id, estado='presente').count()
            asistencia = round(presentes / total_asist * 100, 1) if total_asist > 0 else None
        except Exception:
            asistencia = None

        asignaciones_curso = DocenteAsignacion.objects.filter(
            curso=da.curso, gestion=gestion, activo=True
        ).select_related('area', 'docente__usuario').order_by('area__nombre')

        from .cierre_service import CierreService
        cerrado_info = CierreService().obtener_estado(docente_asignacion_id, periodo_id) if periodo_id else {'cerrado': False}

        return {
            'curso': {
                'id': da.curso.id,
                'grado': da.curso.grado.nombre,
                'paralelo': da.curso.paralelo.nombre,
                'area': da.area.nombre,
                'area_id': da.area_id,
                'nivel': da.curso.grado.nivel.nombre,
            },
            'asignaciones': [
                {
                    'id': a.id,
                    'area': a.area.nombre,
                    'area_id': a.area_id,
                    'docente': a.docente.usuario.nombre_completo if a.docente and a.docente.usuario else None,
                }
                for a in asignaciones_curso
            ],
            'rendimiento': rendimiento,
            'asistencia': asistencia,
            'estudiantes': estudiantes,
            'periodos': periodos,
            'dimensiones': dimensiones,
            'actividades': actividades,
            'actividad_notas': actividad_notas,
            'notas_dimension': notas_dimension,
            'cerrado': cerrado_info['cerrado'],
        }

    def _get_estudiantes_curso(self, curso, gestion):
        inscripciones = Inscripciones.objects.filter(
            curso=curso, gestion=gestion, estado='activo'
        ).select_related('estudiante')
        return [
            {
                'id': ins.estudiante.id,
                'nombres': ins.estudiante.nombres,
                'primer_apellido': ins.estudiante.primer_apellido,
                'rude': ins.estudiante.rude,
            }
            for ins in inscripciones
        ]

    def _list_periodos(self, gestion):
        return [
            {'id': p.id, 'nombre': p.nombre, 'numero': p.numero, 'gestion': p.gestion, 'estado': p.estado}
            for p in Periodos.objects.filter(gestion=gestion, estado='activo').order_by('numero')
        ]

    def _list_dimensiones(self, periodo_id=None):
        config_map = {}
        gestion = None
        if periodo_id:
            config_map = {
                c.dimension_id: float(c.puntaje_maximo)
                for c in DimensionConfigPeriodo.objects.filter(periodo_id=periodo_id)
            }
            try:
                periodo = Periodos.objects.get(id=periodo_id)
                gestion = periodo.gestion
            except Periodos.DoesNotExist:
                pass
        qs = DimensionesEvaluacion.objects.all().order_by('orden')
        if gestion:
            qs = qs.filter(gestion=gestion)
        return [
            {
                'id': d.id,
                'nombre': d.nombre,
                'orden': d.orden,
                'gestion': d.gestion,
                'puntaje_maximo': config_map.get(d.id, float(d.puntaje_maximo) if d.puntaje_maximo is not None else 0),
            }
            for d in qs
        ]

    def _get_actividad_notas_map(self, docente_asignacion_id):
        qs = ActividadNotas.objects.filter(
            actividad__docente_asignacion_id=docente_asignacion_id
        ).select_related('actividad', 'estudiante')
        result = {}
        for an in qs:
            act_key = str(an.actividad_id)
            est_key = str(an.estudiante_id)
            result.setdefault(act_key, {})[est_key] = float(an.valor) if an.valor is not None else None
        return result

    def _get_notas_dimension(self, docente_asignacion_id, periodo_id=None):
        if not periodo_id:
            return []
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT estudiante_id, dimension_id, nota_dimension, promedio_porcentual
                   FROM v_notas_por_dimension
                   WHERE docente_asignacion_id = %s AND periodo_id = %s""",
                [docente_asignacion_id, periodo_id],
            )
            rows = cursor.fetchall()
        result = {}
        for estudiante_id, dim_id, nota, promedio in rows:
            result.setdefault(str(estudiante_id), {})[str(dim_id)] = float(nota)
        return result

    def get_notas_totales(self, usuario, docente_asignacion_id, periodo_id):
        if not self.ac.puede_editar_notas(usuario, docente_asignacion_id) and not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver estas notas')

        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT estudiante_id, periodo_id, nota_total, dimensiones_evaluadas
                   FROM v_notas_totales
                   WHERE docente_asignacion_id = %s AND periodo_id = %s""",
                [docente_asignacion_id, periodo_id],
            )
            rows = cursor.fetchall()
        return [
            {
                'estudiante_id': r[0],
                'periodo_id': r[1],
                'nota_total': float(r[2]) if r[2] else 0,
                'dimensiones_evaluadas': r[3],
            }
            for r in rows
        ]

    def get_notas_por_dimension(self, usuario, docente_asignacion_id, periodo_id):
        if not self.ac.puede_editar_notas(usuario, docente_asignacion_id) and not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver estas notas')

        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT v.estudiante_id, v.dimension_id, v.nota_dimension, v.promedio_porcentual,
                          v.puntaje_dimension, d.nombre AS dimension_nombre
                   FROM v_notas_por_dimension v
                   JOIN dimensiones_evaluacion d ON d.id = v.dimension_id
                   WHERE v.docente_asignacion_id = %s AND v.periodo_id = %s
                   ORDER BY v.estudiante_id, d.orden""",
                [docente_asignacion_id, periodo_id],
            )
            rows = cursor.fetchall()
        return [
            {
                'estudiante_id': r[0],
                'dimension_id': r[1],
                'nota': float(r[2]) if r[2] else 0,
                'promedio': float(r[3]) if r[3] else 0,
                'puntaje_maximo': float(r[4]) if r[4] else 0,
                'dimension_nombre': r[5],
            }
            for r in rows
        ]
