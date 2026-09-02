from django.db import connection
from ..models import Estudiantes, Inscripciones, NotaObservaciones, Asistencias, Periodos, DocenteAsignacion
from ..tracing import trace_service_class
from .access_service import AccessControlService
from collections import OrderedDict


@trace_service_class
class ReportCardService:

    def __init__(self):
        self.ac = AccessControlService()

    def _batch_notas_totales(self, estudiante_id, da_ids, periodo_ids):
        """Batch query v_notas_totales for all (estudiante, DA, periodo) combinations at once."""
        if not da_ids or not periodo_ids:
            return {}
        placeholders_da = ','.join(['%s'] * len(da_ids))
        placeholders_per = ','.join(['%s'] * len(periodo_ids))
        sql = f"""SELECT docente_asignacion_id, periodo_id, nota_total
                   FROM v_notas_totales
                  WHERE estudiante_id = %s
                    AND docente_asignacion_id IN ({placeholders_da})
                    AND periodo_id IN ({placeholders_per})"""
        params = [estudiante_id] + list(da_ids) + list(periodo_ids)
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        result = {}
        for da_id, per_id, nota in rows:
            result[(da_id, per_id)] = float(nota) if nota is not None else None
        return result

    def _batch_attendance(self, estudiante_id, da_ids, periodos):
        """Batch query attendance for all periods at once."""
        if not da_ids or not periodos:
            return {}
        placeholders_da = ','.join(['%s'] * len(da_ids))
        from django.db.models import Count, Q
        qs = Asistencias.objects.filter(
            estudiante_id=estudiante_id,
            docente_asignacion_id__in=da_ids,
        ).values('docente_asignacion_id', 'fecha', 'estado')
        all_asist = list(qs)
        result = {}
        for p in periodos:
            p_total = 0
            p_presentes = 0
            for a in all_asist:
                if p.fecha_inicio <= a['fecha'] <= p.fecha_fin:
                    p_total += 1
                    if a['estado'] == 'presente':
                        p_presentes += 1
            result[p.id] = {
                'total': p_total,
                'presentes': p_presentes,
                'porcentaje': round((p_presentes / p_total) * 100, 1) if p_total > 0 else 0,
            }
        return result

    def generar_boletin(self, usuario, estudiante_id, gestion=None):
        estudiante_id = int(estudiante_id)
        estudiantes_autorizados = self.ac.get_estudiantes_autorizados(usuario)
        if estudiantes_autorizados is not None and estudiante_id not in estudiantes_autorizados:
            raise PermissionError('No autorizado')

        estudiante = Estudiantes.objects.get(id=estudiante_id)

        if not gestion:
            ins_actual = Inscripciones.objects.filter(estudiante_id=estudiante_id).order_by('-gestion').first()
            if not ins_actual:
                raise ValueError('sin inscripciones')
            gestion = ins_actual.gestion

        inscripciones = list(Inscripciones.objects.filter(
            estudiante_id=estudiante_id, gestion=gestion
        ).select_related('curso__grado', 'curso__paralelo'))

        if not inscripciones:
            raise ValueError(f'No hay inscripciones para la gestion {gestion}')

        periodos = list(Periodos.objects.filter(gestion=gestion).order_by('fecha_inicio'))
        curso = inscripciones[0].curso

        asignaciones = list(DocenteAsignacion.objects.filter(
            curso=curso, gestion=gestion, activo=True
        ).select_related('area'))

        da_ids = [da.id for da in asignaciones]
        periodo_ids = [p.id for p in periodos]

        # Bulk fetch all notas
        notas_map = self._batch_notas_totales(estudiante_id, da_ids, periodo_ids)

        # Build materias_map preserving area order
        materias_map = OrderedDict()
        for da in asignaciones:
            area_id = da.area_id
            if area_id not in materias_map:
                materias_map[area_id] = {
                    'docente_asignacion_id': da.id,
                    'area_id': area_id,
                    'area': da.area.nombre,
                    'docente': da.usuario.nombre_completo,
                    'notas_por_periodo': {},
                }
            entry = materias_map[area_id]
            for p in periodos:
                pid_str = str(p.id)
                if pid_str in entry['notas_por_periodo']:
                    continue
                key = (da.id, p.id)
                nota = notas_map.get(key)
                if nota is not None:
                    entry['notas_por_periodo'][pid_str] = nota

        materias = []
        for entry in materias_map.values():
            notas_por_periodo = {}
            for p in periodos:
                pid_str = str(p.id)
                notas_por_periodo[pid_str] = entry['notas_por_periodo'].get(pid_str)
            notas_con_cero = [v if v is not None else 0 for v in notas_por_periodo.values()]
            materias.append({
                'docente_asignacion_id': entry['docente_asignacion_id'],
                'area_id': entry['area_id'],
                'area': entry['area'],
                'docente': entry['docente'],
                'notas_por_periodo': notas_por_periodo,
                'promedio_final': round(sum(notas_con_cero) / len(notas_con_cero), 2) if periodos else None,
            })

        # Batch observaciones
        observaciones = []
        obs_qs = NotaObservaciones.objects.filter(
            estudiante_id=estudiante_id,
            docente_asignacion_id__in=da_ids,
            periodo_id__in=periodo_ids,
        ).select_related('periodo')
        area_map = {da.id: da.area.nombre for da in asignaciones}
        for o in obs_qs:
            observaciones.append({
                'periodo_id': o.periodo_id,
                'periodo': o.periodo.nombre,
                'area': area_map.get(o.docente_asignacion_id, ''),
                'indicador': o.indicador,
                'observacion': o.observacion or '',
            })

        # Batch attendance
        asist_map = self._batch_attendance(estudiante_id, da_ids, periodos)
        asistencias = []
        for p in periodos:
            a = asist_map.get(p.id, {'total': 0, 'presentes': 0, 'porcentaje': 0})
            asistencias.append({
                'periodo_id': p.id,
                'periodo': p.nombre,
                'total': a['total'],
                'presentes': a['presentes'],
                'porcentaje': a['porcentaje'],
            })

        return {
            'estudiante': {
                'id': estudiante.id,
                'rude': estudiante.rude,
                'ci': estudiante.ci,
                'nombres': estudiante.nombres,
                'primer_apellido': estudiante.primer_apellido,
                'segundo_apellido': estudiante.segundo_apellido or '',
            },
            'curso': {
                'id': curso.id,
                'nombre': str(curso),
                'grado': curso.grado.nombre,
                'paralelo': curso.paralelo.nombre,
            },
            'gestion': gestion,
            'periodos': [{'id': p.id, 'nombre': p.nombre} for p in periodos],
            'materias': materias,
            'observaciones': observaciones,
            'asistencias': asistencias,
        }

    def boletin_consolidado_gestion(self, usuario, gestion=None):
        if not self.ac.puede_ver_todo(usuario) and not self.ac.es_director(usuario) and not self.ac.es_secretaria(usuario):
            raise PermissionError('No autorizado')

        if not gestion:
            ultimo_periodo = Periodos.objects.filter(estado='activo').order_by('-gestion').first()
            if not ultimo_periodo:
                raise ValueError('No hay periodos activos')
            gestion = ultimo_periodo.gestion

        from ..models import Cursos
        cursos = Cursos.objects.filter(gestion=gestion, activo=True).select_related('grado', 'paralelo').order_by('grado__numero', 'paralelo__nombre')
        periodos = list(Periodos.objects.filter(gestion=gestion).order_by('fecha_inicio'))
        periodo_ids = [p.id for p in periodos]

        resultado = []
        for curso in cursos:
            inscripciones = Inscripciones.objects.filter(
                curso=curso, gestion=gestion, estado='activo'
            ).select_related('estudiante')

            estudiante_ids = [ins.estudiante_id for ins in inscripciones]
            if not estudiante_ids:
                continue

            # Get all DA ids for this course
            da_ids = list(DocenteAsignacion.objects.filter(
                curso=curso, gestion=gestion, activo=True
            ).values_list('id', flat=True))

            if not da_ids:
                continue

            # Bulk fetch all notas for all students in this course in one query
            placeholders_da = ','.join(['%s'] * len(da_ids))
            placeholders_per = ','.join(['%s'] * len(periodo_ids))
            placeholders_est = ','.join(['%s'] * len(estudiante_ids))
            sql = f"""SELECT estudiante_id, docente_asignacion_id, periodo_id, nota_total
                       FROM v_notas_totales
                      WHERE estudiante_id IN ({placeholders_est})
                        AND docente_asignacion_id IN ({placeholders_da})
                        AND periodo_id IN ({placeholders_per})"""
            params = list(estudiante_ids) + list(da_ids) + list(periodo_ids)
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            # Index: (estudiante_id, da_id, periodo_id) -> nota_total
            notas_index = {}
            for est_id, da_pk, per_id, nota in rows:
                key = (est_id, da_pk, per_id)
                notas_index[key] = float(nota) if nota is not None else None

            estudiantes_data = []
            for ins in inscripciones:
                eid = ins.estudiante_id
                promedios_por_periodo = {}
                for p in periodos:
                    notas_periodo = []
                    for da_pk in da_ids:
                        nota = notas_index.get((eid, da_pk, p.id))
                        if nota is not None:
                            notas_periodo.append(nota)
                    promedios_por_periodo[str(p.id)] = round(sum(notas_periodo) / len(notas_periodo), 2) if notas_periodo else None

                valores = [v for v in promedios_por_periodo.values() if v is not None]
                promedio_general = round(sum(valores) / len(valores), 2) if valores else None

                estudiantes_data.append({
                    'estudiante_id': eid,
                    'rude': ins.estudiante.rude,
                    'nombres': ins.estudiante.nombres,
                    'primer_apellido': ins.estudiante.primer_apellido,
                    'segundo_apellido': ins.estudiante.segundo_apellido or '',
                    'promedios_por_periodo': promedios_por_periodo,
                    'promedio_general': promedio_general,
                })

            if estudiantes_data:
                resultado.append({
                    'curso_id': curso.id,
                    'curso': str(curso),
                    'grado': curso.grado.nombre,
                    'paralelo': curso.paralelo.nombre,
                    'estudiantes': estudiantes_data,
                })

        return {
            'gestion': gestion,
            'periodos': [{'id': p.id, 'nombre': p.nombre} for p in periodos],
            'cursos': resultado,
        }
