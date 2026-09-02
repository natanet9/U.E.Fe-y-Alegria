from django.db.models import Q

from ..models import Cursos, Estudiantes, Inscripciones
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_gestion, ValidationError


@trace_service_class
class InscripcionesService:
    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar(self, usuario, curso_id=None, gestion=None, estado=None, estudiante_id=None, page=None, page_size=None):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        qs = Inscripciones.objects.select_related(
            'estudiante', 'curso__grado', 'curso__paralelo'
        ).filter(activo=True).order_by('estudiante__primer_apellido', 'estudiante__nombres')

        if curso_id:
            qs = qs.filter(curso_id=curso_id)
        if gestion:
            qs = qs.filter(gestion=gestion)
        if estado:
            qs = qs.filter(estado=estado)
        if estudiante_id:
            qs = qs.filter(estudiante_id=estudiante_id)

        if page is None or page_size is None:
            return [
                {
                    'id': i.id,
                    'estudiante_id': i.estudiante_id,
                    'estudiante_nombre': f'{i.estudiante.nombres} {i.estudiante.primer_apellido}',
                    'curso_id': i.curso_id,
                    'curso_nombre': str(i.curso),
                    'gestion': i.gestion,
                    'fecha_inscripcion': str(i.fecha_inscripcion),
                    'estado': i.estado,
                }
                for i in qs
            ]

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]
        return {
            'data': [
                {
                    'id': i.id,
                    'estudiante_id': i.estudiante_id,
                    'estudiante_nombre': f'{i.estudiante.nombres} {i.estudiante.primer_apellido}',
                    'curso_id': i.curso_id,
                    'curso_nombre': str(i.curso),
                    'gestion': i.gestion,
                    'fecha_inscripcion': str(i.fecha_inscripcion),
                    'estado': i.estado,
                }
                for i in items
            ],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def obtener(self, usuario, inscripcion_id):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        i = Inscripciones.objects.select_related(
            'estudiante', 'curso__grado', 'curso__paralelo'
        ).get(id=inscripcion_id, activo=True)
        return {
            'id': i.id,
            'estudiante_id': i.estudiante_id,
            'estudiante_nombre': f'{i.estudiante.nombres} {i.estudiante.primer_apellido}',
            'curso_id': i.curso_id,
            'curso_nombre': str(i.curso),
            'gestion': i.gestion,
            'fecha_inscripcion': str(i.fecha_inscripcion),
            'estado': i.estado,
        }

    def actualizar_estado(self, usuario, inscripcion_id, nuevo_estado):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede modificar inscripciones')

        validos = ['activo', 'retirado', 'transferido']
        if nuevo_estado not in validos:
            raise ValueError(f'Estado invalido. Valores permitidos: {", ".join(validos)}')

        inscripcion = Inscripciones.objects.get(id=inscripcion_id, activo=True)
        old_estado = inscripcion.estado
        inscripcion.estado = nuevo_estado
        inscripcion.save(update_fields=['estado'])
        self.audit.record_inscripcion_change(
            usuario, 'UPDATE', inscripcion_id,
            {'estado': nuevo_estado, 'estado_anterior': old_estado},
        )
        return {'mensaje': 'Estado de inscripcion actualizado', 'estado': nuevo_estado}

    def eliminar(self, usuario, inscripcion_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar inscripciones')

        inscripcion = Inscripciones.objects.get(id=inscripcion_id)
        old_data = {'estudiante_id': inscripcion.estudiante_id, 'curso_id': inscripcion.curso_id, 'gestion': inscripcion.gestion, 'estado': inscripcion.estado}
        inscripcion.activo = False
        inscripcion.save(update_fields=['activo'])
        self.audit.record_inscripcion_change(usuario, 'DELETE', inscripcion_id, old_data)
        return {'mensaje': 'Inscripcion eliminada'}
