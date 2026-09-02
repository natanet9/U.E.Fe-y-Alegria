from django.db.models import Avg, Count, Q, Value, TextField
from django.db.models.functions import Concat, Coalesce, Trim

from ..models import (
    ActividadNotas, Areas, Asistencias, Cursos, DocenteAsignacion,
    Docentes, Grados, Inscripciones, Niveles, Paralelos, Usuarios,
)
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_gestion, ValidationError


@trace_service_class
class CourseService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar_cursos(self, usuario, query=None, page=1, page_size=8):
        if not (self.ac.puede_ver_todo(usuario) or self.ac.es_docente(usuario)):
            return {'cursos': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

        qs = Cursos.objects.filter(activo=True).select_related('grado__nivel', 'paralelo').order_by('grado__nivel__nombre', 'grado__numero', 'paralelo__nombre')

        if query:
            qs = qs.filter(
                Q(grado__nombre__icontains=query)
                | Q(paralelo__nombre__icontains=query)
                | Q(grado__nivel__nombre__icontains=query)
                | Q(docenteasignacion__docente__usuario__nombre_completo__icontains=query)
                | Q(docenteasignacion__area__nombre__icontains=query)
            ).distinct()

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        cursos_page = qs[offset:offset + page_size]

        # Batch-fetch related data for the page to avoid N+1 queries
        result = []
        curso_ids = [c.id for c in cursos_page]

        asignaciones_qs = list(DocenteAsignacion.objects.filter(curso_id__in=curso_ids, activo=True).select_related('docente__usuario', 'area'))
        asignaciones_by_curso = {}
        for a in asignaciones_qs:
            asignaciones_by_curso.setdefault(a.curso_id, []).append(a)

        # Count estudiantes per curso in one query (across gestiones) to keep page fast.
        estudiantes_counts = {
            row['curso']: row['c'] for row in (
                Inscripciones.objects.filter(curso_id__in=curso_ids, estado='activo')
                .values('curso')
                .annotate(c=Count('id'))
            )
        }

        for curso in cursos_page:
            asignaciones = asignaciones_by_curso.get(curso.id, [])

            docentes = sorted(set(a.docente.usuario.nombre_completo for a in asignaciones if a.docente and a.docente.usuario))
            areas = [a.area.nombre for a in asignaciones if a.area]
            gestiones = sorted(set(a.gestion for a in asignaciones))

            estudiantes = estudiantes_counts.get(curso.id, 0)

            # Defer expensive aggregates (notas/asistencia) to the course detail endpoint
            rendimiento = None
            asistencia = None

            result.append({
                'id': curso.id,
                'grado': curso.grado.nombre if curso.grado else None,
                'nivel': curso.grado.nivel.nombre if curso.grado and curso.grado.nivel else None,
                'paralelo': curso.paralelo.nombre if curso.paralelo else None,
                'docentes': docentes,
                'areas': areas,
                'gestiones': gestiones,
                'asignacion_ids': [a.id for a in asignaciones],
                'asignaciones': [
                    {
                        'id': a.id,
                        'area': a.area.nombre if a.area else None,
                        'area_id': a.area_id,
                        'docente': a.docente.usuario.nombre_completo if a.docente and a.docente.usuario else None,
                        'gestion': a.gestion,
                    }
                    for a in asignaciones
                ],
                'total_estudiantes': estudiantes,
                'rendimiento': rendimiento,
                'asistencia': asistencia,
            })

        catalogos = {
            'cursos': list(Cursos.objects.filter(activo=True).values('id', 'grado__nombre', 'paralelo__nombre').order_by('grado__nombre', 'paralelo__nombre')),
            'areas': list(Areas.objects.filter(activo=True).values('id', 'nombre').order_by('nombre')),
            'docentes': list(Usuarios.objects.filter(rol__nombre='docente', activo=True).annotate(
                nombre_completo=Trim(Concat(
                    Coalesce('nombre', Value('', output_field=TextField())),
                    Value(' ', output_field=TextField()),
                    Coalesce('primer_apellido', Value('', output_field=TextField())),
                    Value(' ', output_field=TextField()),
                    Coalesce('segundo_apellido', Value('', output_field=TextField())),
                    output_field=TextField(),
                ))
            ).values('id', 'nombre_completo').order_by('nombre', 'primer_apellido', 'segundo_apellido')),
        }

        return {
            'cursos': result,
            'catalogos': catalogos,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def listar_asignaciones(self, usuario, query=None, page=1, page_size=8):
        # Return a simple list of active docente asignacion records for tests and consumers
        if not (self.ac.puede_ver_todo(usuario) or self.ac.es_docente(usuario)):
            return []

        qs = DocenteAsignacion.objects.filter(activo=True).select_related('docente__usuario', 'curso', 'area')
        if self.ac.es_docente(usuario):
            qs = qs.filter(docente__usuario=usuario)

        if query:
            qs = qs.filter(
                Q(curso__grado__nombre__icontains=query)
                | Q(curso__paralelo__nombre__icontains=query)
                | Q(area__nombre__icontains=query)
                | Q(docente__usuario__nombre__icontains=query)
                | Q(docente__usuario__primer_apellido__icontains=query)
            )

        result = []
        for da in qs.order_by('curso__grado__nivel__nombre', 'curso__grado__numero', 'curso__paralelo__nombre'):
            result.append({
                'id': da.id,
                'docente': da.docente.usuario.nombre_completo if da.docente and da.docente.usuario else None,
                'curso': str(da.curso),
                'area': da.area.nombre if da.area else None,
                'gestion': da.gestion,
            })
        return result

    def crear_asignacion(self, usuario, data):
        if not self.ac.puede_editar_notas(usuario):
            raise PermissionError('No tienes permisos para crear asignaciones')

        validar_required(data, ['usuario_id', 'curso_id', 'area_id', 'gestion'])
        validar_gestion(data.get('gestion'))

        usuario_obj = Usuarios.objects.get(id=data['usuario_id'])
        curso_obj = Cursos.objects.get(id=data['curso_id'])
        area_obj = Areas.objects.get(id=data['area_id'])
        gestion = data['gestion']

        docente_obj, _ = Docentes.objects.get_or_create(usuario=usuario_obj)

        existing = DocenteAsignacion.objects.filter(
            curso=curso_obj, area=area_obj, gestion=gestion, activo=True
        ).exclude(docente=docente_obj).first()
        if existing:
            raise ValueError(
                f'El curso {curso_obj} ya tiene asignado {existing.docente.usuario.nombre_completo} '
                f'para el área {area_obj.nombre} en la gestión {gestion}'
            )

        da = DocenteAsignacion.objects.create(
            docente=docente_obj, curso=curso_obj, area=area_obj, gestion=gestion,
        )
        return {
            'id': da.id,
            'usuario': usuario_obj.nombre_completo,
            'usuario_id': usuario_obj.id,
            'curso_id': curso_obj.id,
            'area': area_obj.nombre,
            'area_id': area_obj.id,
            'gestion': gestion,
        }

    def actualizar_asignacion(self, usuario, asignacion_id, data):
        if not self.ac.puede_editar_notas(usuario):
            raise PermissionError('No tienes permisos para actualizar asignaciones')

        da = DocenteAsignacion.objects.get(id=asignacion_id)

        if 'usuario_id' in data or 'docente_id' in data:
            usuario_id = data.get('usuario_id', data.get('docente_id'))
            usuario_obj = Usuarios.objects.get(id=usuario_id)
            docente_obj, _ = Docentes.objects.get_or_create(usuario=usuario_obj)
            da.docente = docente_obj
        if 'curso_id' in data:
            da.curso = Cursos.objects.get(id=data['curso_id'])
        if 'area_id' in data:
            da.area = Areas.objects.get(id=data['area_id'])
        if 'gestion' in data:
            validar_gestion(data['gestion'])
            da.gestion = data['gestion']
        if 'activo' in data:
            da.activo = data['activo']

        da.save()
        self.audit.record(usuario, accion='UPDATE', tabla='docente_asignacion', registro_id=asignacion_id, datos_nuevo={k: data[k] for k in data if k in data})
        area_nombre = None
        usuario_nombre = None
        try:
            if da.area_id:
                area_nombre = Areas.objects.get(id=da.area_id).nombre
        except Exception:
            area_nombre = None
        try:
            if da.docente_id and da.docente and da.docente.usuario:
                usuario_nombre = da.docente.usuario.nombre_completo
        except Exception:
            usuario_nombre = None

        return {
            'id': da.id,
            'docente_id': da.docente_id,
            'usuario': usuario_nombre,
            'curso_id': da.curso_id,
            'area': area_nombre,
            'area_id': da.area_id,
            'gestion': da.gestion,
            'activo': da.activo,
        }

    def eliminar_asignacion(self, usuario, asignacion_id):
        if not self.ac.puede_editar_notas(usuario):
            raise PermissionError('No tienes permisos para eliminar asignaciones')

        da = DocenteAsignacion.objects.get(id=asignacion_id)
        da.activo = False
        da.save(update_fields=['activo'])
        self.audit.record(usuario, accion='DELETE', tabla='docente_asignacion',
                          registro_id=asignacion_id, datos_nuevo={'activo': False})

    def eliminar(self, usuario, asignacion_id):
        return self.eliminar_asignacion(usuario, asignacion_id)

    def restaurar_asignacion(self, usuario, asignacion_id):
        if not self.ac.puede_editar_notas(usuario):
            raise PermissionError('No tienes permisos para restaurar asignaciones')

        da = DocenteAsignacion.objects.get(id=asignacion_id)
        da.activo = True
        da.save(update_fields=['activo'])
        self.audit.record(usuario, accion='RESTORE', tabla='docente_asignacion',
                          registro_id=asignacion_id, datos_nuevo={'activo': True})
        usuario_nombre = None
        area_nombre = None
        try:
            usuario_nombre = da.docente.usuario.nombre_completo if da.docente and da.docente.usuario else None
        except Exception:
            usuario_nombre = None
        try:
            area_nombre = da.area.nombre if da.area else None
        except Exception:
            area_nombre = None
        return {
            'id': da.id,
            'usuario': usuario_nombre,
            'usuario_id': da.docente.usuario.id if da.docente and da.docente.usuario else None,
            'area': area_nombre,
            'area_id': da.area_id,
            'gestion': da.gestion,
            'activo': da.activo,
        }

    def restaurar(self, usuario, asignacion_id):
        return self.restaurar_asignacion(usuario, asignacion_id)

    def get_catalogos(self):
        return {
            'areas': list(Areas.objects.filter(activo=True).values('id', 'nombre').order_by('nombre')),
            'grados': list(
                Grados.objects.filter(activo=True)
                .select_related('nivel')
                .values('id', 'nombre', 'nivel__nombre', 'numero')
                .order_by('nivel__nombre', 'numero')
            ),
            'paralelos': list(Paralelos.objects.filter(activo=True).values('id', 'nombre').order_by('nombre')),
            'niveles': list(Niveles.objects.filter(activo=True).values('id', 'nombre').order_by('nombre')),
            'cursos': list(
                Cursos.objects.filter(activo=True)
                .select_related('grado__nivel', 'paralelo')
                .values('id', 'grado__nombre', 'grado__nivel__nombre', 'paralelo__nombre')
                .order_by('grado__nivel__nombre', 'grado__numero', 'paralelo__nombre')
            ),
            'docentes': list(
                Usuarios.objects.filter(rol__nombre='docente', activo=True)
                .annotate(
                    nombre_completo=Trim(Concat(
                        Coalesce('nombre', Value('', output_field=TextField())),
                        Value(' ', output_field=TextField()),
                        Coalesce('primer_apellido', Value('', output_field=TextField())),
                        Value(' ', output_field=TextField()),
                        Coalesce('segundo_apellido', Value('', output_field=TextField())),
                        output_field=TextField(),
                    ))
                )
                .values('id', 'nombre_completo')
                .order_by('nombre', 'primer_apellido', 'segundo_apellido')
            ),
        }

    def detalles_asignaciones(self, asignacion_ids):
        """
        Devuelve detalles ligeros para varias asignaciones:
        rendimiento (avg notas), asistencia (%), total_estudiantes, curso_id, gestion
        """
        asignaciones = list(DocenteAsignacion.objects.filter(id__in=asignacion_ids).select_related('curso'))
        if not asignaciones:
            return []

        # Map asignacion_id -> curso_id, gestion
        mapa = {a.id: {'curso_id': a.curso_id, 'gestion': a.gestion} for a in asignaciones}
        curso_ids = list({v['curso_id'] for v in mapa.values()})
        gestiones = list({v['gestion'] for v in mapa.values()})

        # Estudiantes por (curso, gestion)
        ins_qs = Inscripciones.objects.filter(curso_id__in=curso_ids, gestion__in=gestiones, estado='activo')
        counts = {}
        for row in ins_qs.values('curso', 'gestion').annotate(c=Count('id')):
            counts[(row['curso'], row['gestion'])] = row['c']

        # Rendimiento promedio por asignacion (actividad -> docente_asignacion)
        notas_rows = ActividadNotas.objects.filter(actividad__docente_asignacion_id__in=asignacion_ids).values('actividad__docente_asignacion_id').annotate(promedio=Avg('valor'))
        rendimiento_map = {r['actividad__docente_asignacion_id']: float(r['promedio']) if r['promedio'] is not None else None for r in notas_rows}

        # Asistencia: total + presentes por asignacion
        asist_rows = Asistencias.objects.filter(docente_asignacion_id__in=asignacion_ids).values('docente_asignacion_id').annotate(total=Count('id'), presentes=Count('id', filter=Q(estado='presente')))
        asist_map = {r['docente_asignacion_id']: (r['total'], r['presentes']) for r in asist_rows}

        result = []
        for aid in asignacion_ids:
            meta = mapa.get(aid)
            if not meta:
                continue
            total_est = counts.get((meta['curso_id'], meta['gestion']), 0)
            rend = rendimiento_map.get(aid)
            total, presentes = asist_map.get(aid, (0, 0))
            asistencia = round(presentes / total * 100, 1) if total > 0 else None
            result.append({
                'docente_asignacion_id': aid,
                'curso_id': meta['curso_id'],
                'gestion': meta['gestion'],
                'total_estudiantes': total_est,
                'rendimiento': round(rend, 1) if rend is not None else None,
                'asistencia': asistencia,
            })
        return result
