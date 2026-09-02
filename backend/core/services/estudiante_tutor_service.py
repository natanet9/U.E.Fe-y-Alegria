from ..models import EstudianteTutor, Estudiantes, Tutores
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, ValidationError


@trace_service_class
class EstudianteTutorService:
    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar(self, usuario, estudiante_id=None, tutor_id=None):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        qs = EstudianteTutor.objects.select_related('estudiante', 'tutor').filter(activo=True)
        if estudiante_id:
            qs = qs.filter(estudiante_id=estudiante_id)
        if tutor_id:
            qs = qs.filter(tutor_id=tutor_id)

        return [
            {
                'id': et.id,
                'estudiante_id': et.estudiante_id,
                'estudiante_nombre': str(et.estudiante),
                'tutor_id': et.tutor_id,
                'tutor_nombre': str(et.tutor),
                'es_principal': et.es_principal,
            }
            for et in qs.order_by('estudiante__primer_apellido')
        ]

    def crear(self, usuario, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede gestionar tutores de estudiantes')

        validar_required(data, ['estudiante_id', 'tutor_id'])

        et, created = EstudianteTutor.objects.get_or_create(
            estudiante_id=data['estudiante_id'],
            tutor_id=data['tutor_id'],
            defaults={'es_principal': data.get('es_principal', False)},
        )
        if not created:
            if 'es_principal' in data:
                et.es_principal = data['es_principal']
                et.save(update_fields=['es_principal'])
            return {'id': et.id, 'mensaje': 'Relacion actualizada'}

        self.audit.record(usuario, accion='CREATE', tabla='estudiante_tutor',
                          registro_id=et.id, datos_nuevo={'estudiante_id': data['estudiante_id'], 'tutor_id': data['tutor_id']})
        return {'id': et.id, 'mensaje': 'Tutor asociado al estudiante'}

    def eliminar(self, usuario, relacion_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar relaciones')

        et = EstudianteTutor.objects.get(id=relacion_id)
        et.activo = False
        et.save(update_fields=['activo'])
        self.audit.record(usuario, accion='DELETE', tabla='estudiante_tutor',
                          registro_id=relacion_id)
        return {'mensaje': 'Relacion eliminada'}
