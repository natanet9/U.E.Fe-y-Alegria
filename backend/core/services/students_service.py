from django.db import connection
from django.db.models import Q

from ..models import Estudiantes, Inscripciones, ActividadNotas, Actividades, Asistencias, NotaObservaciones, Periodos
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_ci, validar_fecha, validar_nombre, validar_rude, ValidationError


@trace_service_class
class StudentsService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar(self, usuario, query=None, grado_id=None, page=1, page_size=8, incluir_inactivos=False):
        if incluir_inactivos:
            qs = Estudiantes.objects.all().order_by('primer_apellido', 'nombres')
        else:
            qs = Estudiantes.objects.filter(estado='activo').order_by('primer_apellido', 'nombres')
        
        # Aplicar filtro por scope
        estudiantes_ids = self.ac.get_estudiantes_autorizados(usuario)
        if estudiantes_ids is not None:
            if not estudiantes_ids:
                return {
                    'estudiantes': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0,
                }
            qs = qs.filter(id__in=estudiantes_ids)

        if query:
            qs = qs.filter(
                Q(nombres__icontains=query)
                | Q(primer_apellido__icontains=query)
                | Q(ci__icontains=query)
                | Q(rude__icontains=query)
            )

        if grado_id:
            qs = qs.filter(
                inscripciones__curso__grado_id=grado_id,
                inscripciones__estado='activo',
            )

        # If page is None, return full list
        if page is None:
            estudiantes = qs
            result = [self._to_dict(e) for e in estudiantes]
            self._enrich_from_db(result)
            return result

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        estudiantes = qs[offset:offset + page_size]

        result = [self._to_dict(e) for e in estudiantes]
        self._enrich_from_db(result)

        return {
            'estudiantes': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def obtener(self, usuario, estudiante_id):
        # Verificar si el usuario está autorizado a ver este estudiante
        estudiantes_ids = self.ac.get_estudiantes_autorizados(usuario)
        if estudiantes_ids is not None and estudiante_id not in estudiantes_ids:
            raise PermissionError('No tienes permisos para ver este estudiante')

        e = Estudiantes.objects.get(id=estudiante_id)
        return self._to_dict(e)

    def crear(self, usuario, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede crear estudiantes')

        validar_required(data, ['rude', 'ci', 'nombres', 'primer_apellido'])
        validar_rude(data.get('rude'))
        validar_ci(data.get('ci'))
        validar_fecha(data.get('fecha_nacimiento'), 'fecha_nacimiento')
        validar_nombre(data.get('nombres'), 'Nombres')
        validar_nombre(data.get('primer_apellido'), 'Primer apellido')

        estudiante = Estudiantes.objects.create(
            rude=data['rude'],
            ci=data['ci'],
            nombres=data['nombres'],
            primer_apellido=data['primer_apellido'],
            segundo_apellido=data.get('segundo_apellido', ''),
            fecha_nacimiento=data.get('fecha_nacimiento'),
            genero=data.get('genero'),
            pais_nacimiento=data.get('pais_nacimiento', 'Bolivia'),
            tiene_discapacidad=data.get('tiene_discapacidad', False),
            tipo_discapacidad=data.get('tipo_discapacidad', ''),
            tiene_tea=data.get('tiene_tea', False),
            dificultad_aprendizaje=data.get('dificultad_aprendizaje', ''),
        )
        self.audit.record_estudiante_change(usuario, 'CREATE', estudiante.id, {'rude': data['rude'], 'nombres': data['nombres']})
        return self._to_dict(estudiante)

    def actualizar(self, usuario, estudiante_id, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede modificar estudiantes')

        estudiante = Estudiantes.objects.get(id=estudiante_id)

        if data.get('ci'):
            validar_ci(data.get('ci'))
        if data.get('rude'):
            validar_rude(data.get('rude'))

        for campo in ('rude', 'ci', 'nombres', 'primer_apellido', 'segundo_apellido',
                       'fecha_nacimiento', 'genero', 'pais_nacimiento',
                       'tiene_discapacidad', 'tipo_discapacidad',
                       'tiene_tea', 'dificultad_aprendizaje'):
            if campo in data:
                setattr(estudiante, campo, data[campo])
        estudiante.save()
        self.audit.record_estudiante_change(usuario, 'UPDATE', estudiante_id, {k: data[k] for k in data if k in data})
        return self._to_dict(estudiante)

    def eliminar(self, usuario, estudiante_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar estudiantes')

        estudiante = Estudiantes.objects.get(id=estudiante_id)
        estudiante.estado = 'inactivo'
        estudiante.save(update_fields=['estado'])
        self.audit.record_estudiante_change(usuario, 'DELETE', estudiante_id, {'estado': 'inactivo'})

    def restaurar(self, usuario, estudiante_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede restaurar estudiantes')

        estudiante = Estudiantes.objects.get(id=estudiante_id)
        estudiante.estado = 'activo'
        estudiante.save(update_fields=['estado'])
        self.audit.record_estudiante_change(usuario, 'RESTORE', estudiante_id, {'estado': 'activo'})
        return self._to_dict(estudiante)

    def historial_academico(self, usuario, estudiante_id):
        estudiantes_ids = self.ac.get_estudiantes_autorizados(usuario)
        if estudiantes_ids is not None and estudiante_id not in estudiantes_ids:
            raise PermissionError('No autorizado para ver el historial de este estudiante')

        estudiante = Estudiantes.objects.get(id=estudiante_id)
        resultado = self._to_dict(estudiante)

        inscripciones_qs = list(Inscripciones.objects.filter(
            estudiante_id=estudiante_id
        ).select_related('curso__grado', 'curso__paralelo').order_by('-gestion'))

        resultado['inscripciones'] = [
            {
                'id': i.id,
                'curso': str(i.curso),
                'grado': i.curso.grado.nombre,
                'paralelo': i.curso.paralelo.nombre,
                'gestion': i.gestion,
                'estado': i.estado,
                'fecha_inscripcion': str(i.fecha_inscripcion),
            }
            for i in inscripciones_qs
        ]

        notas_qs = ActividadNotas.objects.filter(
            estudiante_id=estudiante_id
        ).select_related(
            'actividad__periodo',
            'actividad__dimension',
            'actividad__docente_asignacion__curso__grado',
            'actividad__docente_asignacion__curso__paralelo',
            'actividad__docente_asignacion__area',
        ).order_by('-actividad__periodo__gestion', 'actividad__periodo__nombre', 'actividad__fecha_actividad')[:500]

        actividades = []
        for an in notas_qs:
            da = an.actividad.docente_asignacion
            actividades.append({
                'actividad_id': an.actividad_id,
                'actividad_nombre': an.actividad.nombre,
                'dimension': an.actividad.dimension.nombre,
                'puntaje_maximo': float(an.actividad.puntaje_maximo),
                'valor': float(an.valor) if an.valor is not None else None,
                'fecha': str(an.actividad.fecha_actividad),
                'periodo': an.actividad.periodo.nombre,
                'gestion': an.actividad.periodo.gestion,
                'docente_asignacion_id': da.id if da else None,
                'curso': str(da.curso) if da else None,
                'area': da.area.nombre if da and da.area_id else None,
            })
        resultado['actividades'] = actividades

        obs_qs = list(NotaObservaciones.objects.filter(
            estudiante_id=estudiante_id
        )        .select_related('periodo', 'docente_asignacion__curso__grado', 'docente_asignacion__curso__paralelo', 'docente_asignacion__area').order_by('-periodo__gestion', 'periodo__nombre')[:200])
        resultado['observaciones'] = [
            {
                'id': o.id,
                'periodo': o.periodo.nombre,
                'gestion': o.periodo.gestion,
                'curso': str(o.docente_asignacion.curso),
                'area': o.docente_asignacion.area.nombre,
                'indicador': o.indicador,
                'observacion': o.observacion,
            }
            for o in obs_qs
        ]

        asistencias_qs = list(Asistencias.objects.filter(
            estudiante_id=estudiante_id
        ).select_related('docente_asignacion__curso__grado', 'docente_asignacion__curso__paralelo').order_by('-fecha')[:1000])

        resultado['asistencias'] = [
            {
                'id': a.id,
                'fecha': str(a.fecha),
                'estado': a.estado,
                'tipo': a.tipo,
                'curso': str(a.docente_asignacion.curso) if a.docente_asignacion else None,
            }
            for a in asistencias_qs
        ]

        from collections import Counter
        resumen_gestion = {}
        for a in asistencias_qs:
            gestion = a.fecha.year
            if gestion not in resumen_gestion:
                resumen_gestion[gestion] = Counter()
            resumen_gestion[gestion][a.estado] += 1

        resultado['resumen_asistencias'] = {
            str(g): dict(counts) for g, counts in resumen_gestion.items()
        }

        return resultado

    def _validar_data(self, data):
        required = ('rude', 'ci', 'nombres', 'primer_apellido')
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise ValueError(f'Campos requeridos faltantes: {", ".join(missing)}')

    def _enrich_from_db(self, estudiantes):
        """Batch-enrich student dicts with grado, promedio, asistencia."""
        ids = [e['id'] for e in estudiantes]
        if not ids:
            return

        id_list = ','.join(['%s'] * len(ids))

        # current active period
        periodo = Periodos.objects.filter(estado='activo').order_by('-gestion', 'fecha_inicio').first()
        periodo_id = periodo.id if periodo else None

        # grado: latest inscripcion
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"""SELECT DISTINCT ON (i.estudiante_id) i.estudiante_id,
                           g.nombre AS grado_nombre
                    FROM inscripciones i
                    JOIN cursos c ON c.id = i.curso_id
                    JOIN grados g ON g.id = c.grado_id
                    WHERE i.estudiante_id IN ({id_list}) AND i.estado = 'activo'
                    ORDER BY i.estudiante_id, i.gestion DESC""",
                ids,
            )
            grado_map = {row[0]: row[1] for row in cursor.fetchall()}
            cursor.close()
        except Exception:
            grado_map = {}

        # promedio from v_notas_totales
        if periodo_id:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    f"""SELECT estudiante_id, ROUND(AVG(nota_total), 2)
                        FROM v_notas_totales
                        WHERE estudiante_id IN ({id_list})
                          AND periodo_id = %s
                          AND nota_total IS NOT NULL
                        GROUP BY estudiante_id""",
                    ids + [periodo_id],
                )
                promedio_map = {row[0]: float(row[1]) for row in cursor.fetchall()}
                cursor.close()
            except Exception:
                promedio_map = {}
        else:
            promedio_map = {}

        # asistencia from asistencias
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"""SELECT estudiante_id,
                           COUNT(*) FILTER (WHERE estado = 'presente') * 100.0 / NULLIF(COUNT(*), 0)
                    FROM asistencias
                    WHERE estudiante_id IN ({id_list})
                    GROUP BY estudiante_id""",
                ids,
            )
            asistencia_map = {row[0]: round(float(row[1]), 1) for row in cursor.fetchall()}
            cursor.close()
        except Exception:
            asistencia_map = {}

        for e in estudiantes:
            eid = e['id']
            if eid in grado_map:
                e['grado'] = grado_map[eid]
            if eid in promedio_map:
                e['promedio'] = promedio_map[eid]
            if eid in asistencia_map:
                e['asistencia'] = asistencia_map[eid]

    def _to_dict(self, e):
        return {
            'id': e.id,
            'rude': e.rude,
            'ci': e.ci,
            'nombres': e.nombres,
            'primer_apellido': e.primer_apellido,
            'segundo_apellido': e.segundo_apellido or '',
            'fecha_nacimiento': str(e.fecha_nacimiento) if e.fecha_nacimiento else None,
            'genero': e.genero,
            'pais_nacimiento': e.pais_nacimiento,
            'tiene_discapacidad': e.tiene_discapacidad,
            'tipo_discapacidad': e.tipo_discapacidad or '',
            'tiene_tea': e.tiene_tea,
            'dificultad_aprendizaje': e.dificultad_aprendizaje or '',
            'estado': e.estado,
        }
