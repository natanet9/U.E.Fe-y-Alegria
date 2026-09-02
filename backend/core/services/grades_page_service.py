from django.db import connection
from django.db.models import Count

from ..models import (
    Areas, Cursos, DocenteAsignacion,
    Estudiantes, Grados, Inscripciones, Periodos,
)
from .access_service import AccessControlService
from ..tracing import trace_service_class


NORMALIZACION_MATERIAS = {
    "Artes Plasticas": "Artes Plásticas",
    "Educacion Fisica": "Educación Física",
    "Lenguaje y Comunicacion": "Lenguaje y Comunicación",
    "Matematicas": "Matemáticas",
    "Tecnica Tecnologica": "Técnica Tecnológica",
}


@trace_service_class
class GradesPageService:

    def __init__(self):
        self.ac = AccessControlService()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _resolve_periodos(self, periodo_id):
        """Return a list of all period ids for the gestion of the given
        period (or latest active period). When *periodo_id* is given, only
        that period is returned, so downstream code can always divide by
        the total count to treat missing periods as zero."""
        if periodo_id:
            p = Periodos.objects.get(id=periodo_id)
            return [p.id]
        ultimo = Periodos.objects.filter(activo=True).order_by('-gestion', '-numero').first()
        if not ultimo:
            return []
        return list(
            Periodos.objects.filter(gestion=ultimo.gestion)
            .order_by('fecha_inicio')
            .values_list('id', flat=True)
        )

    def get_docente_status(self, usuario, periodo_id=None):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver esta informacion')

        pid_list = self._resolve_periodos(periodo_id)
        if not pid_list:
            return {'periodo': None, 'docentes': [], 'resumen': []}
        pid = pid_list[0]  # only one period matters for docente status

        try:
            p = Periodos.objects.get(id=pid)
        except Periodos.DoesNotExist:
            return {'periodo': None, 'docentes': [], 'resumen': []}
        periodo_nombre = f'{p.nombre} {p.gestion}'

        asignaciones = DocenteAsignacion.objects.filter(activo=True, gestion=p.gestion).select_related(
            'docente__usuario', 'curso__grado', 'curso__paralelo', 'area'
        ).order_by('curso__grado__numero', 'curso__grado__nombre', 'curso__paralelo__nombre', 'area__nombre')

        ids = [da.id for da in asignaciones]

        total_estudiantes = {}
        if ids:
            from django.db.models import Count
            qs = Inscripciones.objects.filter(
                curso_id__in=set(da.curso_id for da in asignaciones),
                estado='activo',
            ).values('curso_id').annotate(total=Count('id'))
            for row in qs:
                total_estudiantes[row['curso_id']] = row['total']

        con_notas = {}
        if ids:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT v.docente_asignacion_id, COUNT(DISTINCT v.estudiante_id)
                           FROM v_notas_totales v
                           WHERE v.docente_asignacion_id = ANY(%s) AND v.periodo_id = %s
                           GROUP BY v.docente_asignacion_id""",
                        [ids, pid],
                    )
                    for row in cursor.fetchall():
                        con_notas[row[0]] = row[1]
            except Exception:
                pass

        cerrados = set()
        if ids:
            from ..models import PeriodoCierreDocente
            cerrados = set(
                PeriodoCierreDocente.objects.filter(
                    docente_asignacion_id__in=ids, periodo_id=pid
                ).values_list('docente_asignacion_id', flat=True)
            )

        docentes = []
        for da in asignaciones:
            total = total_estudiantes.get(da.curso_id, 0)
            con = con_notas.get(da.id, 0)
            pct = round((con / total * 100), 1) if total > 0 else 0
            docentes.append({
                'asignacion_id': da.id,
                'docente': da.docente.usuario.nombre_completo if da.docente and da.docente.usuario else '—',
                'email': da.docente.usuario.email if da.docente and da.docente.usuario else '',
                'grado': da.curso.grado.nombre if da.curso and da.curso.grado else '—',
                'area': da.area.nombre if da.area else '—',
                'curso_id': da.curso_id,
                'curso': str(da.curso),
                'total_estudiantes': total,
                'con_notas': con,
                'sin_notas': total - con,
                'porcentaje': pct,
                'cerrado': da.id in cerrados,
            })

        grados = {}
        for d in docentes:
            g = d['grado']
            if g not in grados:
                grados[g] = {'grado': g, 'total_asignaciones': 0, 'completadas': 0, 'docentes': []}
            grados[g]['total_asignaciones'] += 1
            if d['porcentaje'] == 100:
                grados[g]['completadas'] += 1
            grados[g]['docentes'].append(d)

        resumen = [
            {'titulo': 'Docentes', 'valor': len(set(d['docente'] for d in docentes))},
            {'titulo': 'Asignaciones', 'valor': len(docentes)},
            {'titulo': 'Completadas', 'valor': sum(1 for d in docentes if d['porcentaje'] == 100)},
            {'titulo': 'Pendientes', 'valor': sum(1 for d in docentes if d['porcentaje'] < 100)},
        ]

        return {
            'periodo': periodo_nombre,
            'periodo_id': pid,
            'grados': list(grados.values()),
            'docentes': docentes,
            'resumen': resumen,
        }

    def get_overview(self, usuario, query='', periodo_id=None, page=1, page_size=10):
        rol = self.ac.get_role_name(usuario)
        puede_ver_todo = self.ac.puede_ver_todo(usuario)
        estudiantes_autorizados = self.ac.get_estudiantes_autorizados(usuario)

        filtros = self._build_filtros(periodo_id)
        resumen = self._build_resumen(periodo_id)
        promedio_por_asignatura = self._promedio_por_asignatura(periodo_id, estudiantes_autorizados)
        mejores_estudiantes = self._mejores_estudiantes(periodo_id, limit=10, estudiantes_autorizados=estudiantes_autorizados)
        por_curso = self._por_curso(periodo_id, estudiantes_autorizados)
        por_estudiante, calificaciones, paginacion = self._por_estudiante(
            periodo_id, query, page, page_size, estudiantes_autorizados
        )

        return {
            'resumen': resumen,
            'calificaciones': calificaciones,
            'filtros': filtros,
            'promedio_por_asignatura': promedio_por_asignatura,
            'mejores_estudiantes': mejores_estudiantes,
            'por_estudiante': por_estudiante,
            'por_curso': por_curso,
            'permisos': {
                'puede_crear': puede_ver_todo,
                'puede_ver_todo': puede_ver_todo,
            },
            'paginacion': paginacion,
        }

    def get_by_course(self, usuario):
        grados_data = []
        try:
            grados_qs = Grados.objects.filter(activo=True).order_by('numero')
            for g in grados_qs:
                insc = Inscripciones.objects.filter(
                    curso__grado=g, estado='activo'
                ).count()
                grados_data.append({
                    'id': g.id,
                    'nombre': g.nombre,
                    'total_estudiantes': insc,
                    'promedio_general': None,
                })
        except Exception:
            grados_data = []

        resumen = [
            {'titulo': 'Total Cursos', 'valor': Cursos.objects.filter(activo=True).count()},
            {'titulo': 'Total Grados', 'valor': Grados.objects.filter(activo=True).count()},
            {'titulo': 'Docentes Asignados', 'valor': DocenteAsignacion.objects.filter(activo=True).count()},
            {'titulo': 'Estudiantes Inscritos', 'valor': Inscripciones.objects.filter(estado='activo').count()},
        ]

        return {'grados': grados_data, 'resumen': resumen}

    def _build_filtros(self, periodo_id):
        periodos = Periodos.objects.filter(activo=True).order_by('-gestion', 'numero')
        materias_set = set()
        materias = []
        for a in Areas.objects.filter(activo=True).order_by('nombre'):
            nombre_normalizado = NORMALIZACION_MATERIAS.get(a.nombre, a.nombre)
            if nombre_normalizado not in materias_set:
                materias_set.add(nombre_normalizado)
                materias.append(nombre_normalizado)
        return {
            'periodos': [{'id': p.id, 'nombre': f'{p.nombre} {p.gestion}'} for p in periodos],
            'materias': materias,
        }

    def _build_resumen(self, periodo_id):
        total_est = Inscripciones.objects.filter(estado='activo').count()
        total_doc = DocenteAsignacion.objects.filter(activo=True).values('docente').distinct().count()
        total_curso = Cursos.objects.filter(activo=True).count()
        total_asig = DocenteAsignacion.objects.filter(activo=True).count()

        return [
            {'titulo': 'Estudiantes', 'valor': total_est, 'detalle': 'Inscritos activos', 'acento': 'blue'},
            {'titulo': 'Docentes', 'valor': total_doc, 'detalle': 'Con asignaciones', 'acento': 'violet'},
            {'titulo': 'Cursos', 'valor': total_curso, 'detalle': 'Activos', 'acento': 'green'},
            {'titulo': 'Asignaciones', 'valor': total_asig, 'detalle': 'Docente-Área-Curso', 'acento': 'orange'},
        ]

    def _promedio_por_asignatura(self, periodo_id, estudiantes_autorizados=None):
        pid_list = self._resolve_periodos(periodo_id)
        if not pid_list:
            return {'labels': [], 'data': []}
        total_periodos = len(pid_list)

        try:
            with connection.cursor() as cursor:
                sql = """SELECT a.id, COALESCE(a.nombre, 'Sin area'),
                                SUM(v.nota_total) / %s AS subject_avg
                         FROM v_notas_totales v
                         JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                         LEFT JOIN areas a ON a.id = da.area_id
                         WHERE v.periodo_id = ANY(%s)"""
                params = [total_periodos, pid_list]

                if estudiantes_autorizados is not None:
                    sql += " AND v.estudiante_id = ANY(%s)"
                    params.append(estudiantes_autorizados)

                sql += """ GROUP BY a.id, a.nombre, v.estudiante_id"""

                cursor.execute(sql, params)
                rows = cursor.fetchall()
        except Exception:
            rows = []

        # group by area and average student-level subject averages
        from collections import defaultdict
        area_vals = defaultdict(list)
        for area_id, area_nombre, subject_avg in rows:
            if subject_avg is None:
                continue
            norm = NORMALIZACION_MATERIAS.get(area_nombre, area_nombre)
            area_vals[norm].append(float(subject_avg))

        labels = []
        data = []
        for area, valores in sorted(area_vals.items()):
            labels.append(area)
            data.append(round(sum(valores) / len(valores), 2))

        return {'labels': labels, 'data': data}

    def _mejores_estudiantes(self, periodo_id, limit=10, estudiantes_autorizados=None):
        pid_list = self._resolve_periodos(periodo_id)
        if not pid_list:
            return []
        total_periodos = len(pid_list)

        try:
            with connection.cursor() as cursor:
                sql = """SELECT sub.estudiante_id,
                                ROUND(AVG(sub.subject_avg), 2) AS promedio
                         FROM (
                             SELECT v.estudiante_id, da.area_id,
                                    SUM(v.nota_total) / %s AS subject_avg
                             FROM v_notas_totales v
                             JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                             WHERE v.periodo_id = ANY(%s)"""
                params = [total_periodos, pid_list]

                if estudiantes_autorizados is not None:
                    sql += " AND v.estudiante_id = ANY(%s)"
                    params.append(estudiantes_autorizados)

                sql += """ GROUP BY v.estudiante_id, da.area_id
                         ) sub
                         GROUP BY sub.estudiante_id
                         ORDER BY promedio DESC, sub.estudiante_id ASC
                         LIMIT %s"""

                cursor.execute(sql, params + [limit])
                rows = cursor.fetchall()
        except Exception:
            rows = []

        if not rows:
            return []

        ids = [r[0] for r in rows]
        estudiantes = Estudiantes.objects.filter(id__in=ids)
        nombre_map = {e.id: e for e in estudiantes}

        return [
            {
                'id': est_id,
                'posicion': i + 1,
                'nombre': f'{nombre_map[est_id].nombres} {nombre_map[est_id].primer_apellido}' if est_id in nombre_map else f'Estudiante #{est_id}',
                'documento': nombre_map[est_id].ci if est_id in nombre_map else '-',
                'promedio': float(prom),
                'detalle': 'Excelente rendimiento',
            }
            for i, (est_id, prom) in enumerate(rows)
            if est_id in nombre_map
        ]

    def _por_curso(self, periodo_id, estudiantes_autorizados=None):
        pid_list = self._resolve_periodos(periodo_id)
        if not pid_list:
            return []
        total_periodos = len(pid_list)

        try:
            with connection.cursor() as cursor:
                sql = """SELECT c.id, CONCAT(g.nombre, ' ', p.nombre) AS curso_nombre,
                                ROUND(AVG(sub.subject_avg), 2) AS promedio,
                                COUNT(DISTINCT sub.estudiante_id) AS total_est
                         FROM (
                             SELECT v.estudiante_id, da.curso_id, da.area_id,
                                    SUM(v.nota_total) / %s AS subject_avg
                             FROM v_notas_totales v
                             JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                             WHERE v.periodo_id = ANY(%s)"""
                params = [total_periodos, pid_list]

                if estudiantes_autorizados is not None:
                    sql += " AND v.estudiante_id = ANY(%s)"
                    params.append(estudiantes_autorizados)

                sql += """ GROUP BY v.estudiante_id, da.curso_id, da.area_id
                         ) sub
                         JOIN cursos c ON c.id = sub.curso_id
                         JOIN grados g ON g.id = c.grado_id
                         JOIN paralelos p ON p.id = c.paralelo_id
                         GROUP BY c.id, g.nombre, p.nombre
                         ORDER BY promedio DESC"""

                cursor.execute(sql, params)
                rows = cursor.fetchall()
        except Exception:
            rows = []

        result = []
        for r in rows:
            curso_id = r[0]
            # Obtener la distribución y el mejor estudiante para cada curso
            distribucion = [
                {'label': '90+', 'value': 0, 'color': '#d1fae5'},
                {'label': '80-89', 'value': 0, 'color': '#dbeafe'},
                {'label': '70-79', 'value': 0, 'color': '#fef3c7'},
                {'label': '<70', 'value': 0, 'color': '#fee2e2'},
            ]

            try:
                with connection.cursor() as cursor:
                    sql = """SELECT ROUND(AVG(sub.subject_avg), 2)
                             FROM (
                                 SELECT v.estudiante_id, da.area_id,
                                        SUM(v.nota_total) / %s AS subject_avg
                                 FROM v_notas_totales v
                                 JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                                 WHERE da.curso_id = %s AND v.periodo_id = ANY(%s)"""
                    params = [total_periodos, curso_id, pid_list]

                    if estudiantes_autorizados is not None:
                        sql += " AND v.estudiante_id = ANY(%s)"
                        params.append(estudiantes_autorizados)

                    sql += """ GROUP BY v.estudiante_id, da.area_id
                             ) sub
                             GROUP BY sub.estudiante_id"""

                    cursor.execute(sql, params)
                    notas_curso = [row[0] for row in cursor.fetchall() if row[0] is not None]

                    for nota in notas_curso:
                        if nota >= 90:
                            distribucion[0]['value'] += 1
                        elif nota >= 80:
                            distribucion[1]['value'] += 1
                        elif nota >= 70:
                            distribucion[2]['value'] += 1
                        else:
                            distribucion[3]['value'] += 1

                    # Convertir a porcentajes
                    total_notas = len(notas_curso) if notas_curso else 1
                    for d in distribucion:
                        d['value'] = round((d['value'] / total_notas) * 100, 1)
            except Exception:
                pass

            mejor_estudiante = '-'
            try:
                with connection.cursor() as cursor:
                    sql = """SELECT sub.estudiante_id,
                                    ROUND(AVG(sub.subject_avg), 2) as prom
                             FROM (
                                 SELECT v.estudiante_id, da.area_id,
                                        SUM(v.nota_total) / %s AS subject_avg
                                 FROM v_notas_totales v
                                 JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                                 WHERE da.curso_id = %s AND v.periodo_id = ANY(%s)"""
                    params = [total_periodos, curso_id, pid_list]

                    if estudiantes_autorizados is not None:
                        sql += " AND v.estudiante_id = ANY(%s)"
                        params.append(estudiantes_autorizados)

                    sql += """ GROUP BY v.estudiante_id, da.area_id
                             ) sub
                             GROUP BY sub.estudiante_id
                             ORDER BY prom DESC LIMIT 1"""
                    cursor.execute(sql, params)
                    row = cursor.fetchone()
                    if row:
                        est_id = row[0]
                        try:
                            est = Estudiantes.objects.get(id=est_id)
                            mejor_estudiante = f'{est.nombres} {est.primer_apellido}'
                        except Estudiantes.DoesNotExist:
                            pass
            except Exception:
                pass

            result.append({
                'id': r[0],
                'curso': r[1],
                'promedio': float(r[2]) if r[2] else 0,
                'distribucion': distribucion,
                'estudiantes': int(r[3]),
                'mejor_estudiante': mejor_estudiante,
            })
        
        return result

    def _por_estudiante(self, periodo_id, query, page, page_size, estudiantes_autorizados=None):
        pid_list = self._resolve_periodos(periodo_id)
        if not pid_list:
            return ([], [], {'pagina': 1, 'paginas': 1, 'anterior': False, 'siguiente': False, 'total': 0})
        total_periodos = len(pid_list)
        offset = (page - 1) * page_size

        # Build WHERE conditions
        where_clauses = ["v.periodo_id = ANY(%s)"]
        params = [pid_list]

        if estudiantes_autorizados is not None:
            where_clauses.append("v.estudiante_id = ANY(%s)")
            params.append(estudiantes_autorizados)

        if query:
            where_clauses.append("""(e.nombres ILIKE %s OR e.primer_apellido ILIKE %s OR e.ci ILIKE %s)""")
            q = f'%{query}%'
            params.extend([q, q, q])

        where_sql = " AND ".join(where_clauses)

        # Main query: per-student average = avg of subject-level averages
        # (each subject avg = sum(notas) / total_periodos, missing = 0)
        try:
            with connection.cursor() as cursor:
                sql = f"""SELECT subq.estudiante_id, e.nombres, e.primer_apellido, e.ci,
                                  ROUND(AVG(subq.subject_avg), 2) AS promedio
                          FROM (
                              SELECT v.estudiante_id, da.area_id,
                                     SUM(v.nota_total) / %s AS subject_avg
                              FROM v_notas_totales v
                              JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                              JOIN estudiantes e ON e.id = v.estudiante_id
                              WHERE {where_sql}
                              GROUP BY v.estudiante_id, da.area_id
                          ) subq
                          JOIN estudiantes e ON e.id = subq.estudiante_id
                          GROUP BY subq.estudiante_id, e.nombres, e.primer_apellido, e.ci
                          ORDER BY promedio DESC
                          LIMIT %s OFFSET %s"""
                cursor.execute(sql, params + [total_periodos, page_size, offset])
                rows = cursor.fetchall()
        except Exception:
            rows = []

        try:
            with connection.cursor() as cursor:
                sql = f"""SELECT COUNT(DISTINCT subq.estudiante_id)
                          FROM (
                              SELECT v.estudiante_id
                              FROM v_notas_totales v
                              JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                              JOIN estudiantes e ON e.id = v.estudiante_id
                              WHERE {where_sql}
                              GROUP BY v.estudiante_id, da.area_id
                          ) subq"""
                cursor.execute(sql, params)
                total = int(cursor.fetchone()[0] or 0)
        except Exception:
            total = 0

        total_pages = max(1, (total + page_size - 1) // page_size) if total else 1

        estudiante_ids = [r[0] for r in rows] if rows else []

        materias_por_estudiante = {}
        attendance_map = {}
        if estudiante_ids:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT a.estudiante_id,
                                  COUNT(*) AS total,
                                  COUNT(*) FILTER (WHERE a.estado = 'presente') AS presentes
                           FROM asistencias a
                           WHERE a.estudiante_id = ANY(%s)
                           GROUP BY a.estudiante_id""",
                        [estudiante_ids],
                    )
                    for row in cursor.fetchall():
                        est_id = row[0]
                        total = row[1]
                        presentes = row[2]
                        attendance_map[est_id] = round(presentes / total * 100, 1) if total > 0 else 0
            except Exception:
                pass
            try:
                with connection.cursor() as cursor:
                    sql = """SELECT v.estudiante_id, a.nombre,
                                    ROUND(SUM(v.nota_total) / %s, 2) as nota
                             FROM v_notas_totales v
                             JOIN docente_asignacion da ON da.id = v.docente_asignacion_id
                             JOIN areas a ON a.id = da.area_id
                             WHERE v.estudiante_id = ANY(%s) AND v.periodo_id = ANY(%s)
                             GROUP BY v.estudiante_id, a.nombre"""
                    cursor.execute(sql, [total_periodos, estudiante_ids, pid_list])
                    for row in cursor.fetchall():
                        est_id = row[0]
                        materia_nombre = row[1]
                        nota = row[2]
                        materia_normalizada = NORMALIZACION_MATERIAS.get(materia_nombre, materia_nombre)
                        if est_id not in materias_por_estudiante:
                            materias_por_estudiante[est_id] = {}
                        materias_por_estudiante[est_id][materia_normalizada] = float(nota) if nota else '-'
            except Exception:
                pass

        por_estudiante = []
        for r in rows:
            est_id = r[0]
            por_estudiante.append({
                'id': est_id,
                'estudiante': f'{r[1]} {r[2]}'.strip(),
                'documento': r[3] or '-',
                'materias': materias_por_estudiante.get(est_id, {}),
                'promedio': float(r[4]) if r[4] else 0,
                'tendencia': 'stable',
                'asistencia': attendance_map.get(est_id, 0),
            })

        return (
            por_estudiante,
            por_estudiante,
            {
                'pagina': page,
                'paginas': total_pages,
                'anterior': page > 1,
                'siguiente': page < total_pages,
                'total': total,
            },
        )
