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

        estudiante_id = data['estudiante_id']

        # El primer tutor asignado al estudiante queda como principal
        es_principal = data.get('es_principal')
        if es_principal is None:
            es_principal = not EstudianteTutor.objects.filter(
                estudiante_id=estudiante_id, activo=True,
            ).exists()
        es_principal = self._as_bool(es_principal)

        et, created = EstudianteTutor.objects.get_or_create(
            estudiante_id=estudiante_id,
            tutor_id=data['tutor_id'],
            defaults={'es_principal': es_principal},
        )
        if not created:
            campos = []
            if 'es_principal' in data:
                et.es_principal = es_principal
                campos.append('es_principal')
            if getattr(et, 'activo', True) is False:
                et.activo = True
                campos.append('activo')
            if campos:
                et.save(update_fields=campos)
            if es_principal:
                self._marcar_principal(estudiante_id, et.id)
            return {'id': et.id, 'mensaje': 'Relacion actualizada'}

        if es_principal:
            self._marcar_principal(estudiante_id, et.id)

        self.audit.record(usuario, accion='CREATE', tabla='estudiante_tutor',
                          registro_id=et.id, datos_nuevo={
                              'estudiante_id': estudiante_id,
                              'tutor_id': data['tutor_id'],
                              'es_principal': es_principal,
                          })
        return {'id': et.id, 'mensaje': 'Tutor asociado al estudiante'}

    @staticmethod
    def _as_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ('1', 'true', 'yes', 'si')

    def _marcar_principal(self, estudiante_id, relacion_id):
        """Deja un unico tutor principal por estudiante."""
        EstudianteTutor.objects.filter(
            estudiante_id=estudiante_id, activo=True, es_principal=True,
        ).exclude(id=relacion_id).update(es_principal=False)

    def _promover_principal(self, estudiante_id):
        """Promueve otro tutor activo cuando el principal fue removido."""
        if not estudiante_id:
            return
        try:
            candidato = EstudianteTutor.objects.filter(
                estudiante_id=estudiante_id, activo=True,
            ).order_by('id').first()
        except Exception:
            return
        if candidato is None:
            return
        candidato.es_principal = True
        candidato.save(update_fields=['es_principal'])

    def eliminar(self, usuario, relacion_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar relaciones')

        et = EstudianteTutor.objects.get(id=relacion_id)
        et.activo = False
        et.save(update_fields=['activo'])
        # El estudiante no debe quedarse sin tutor principal
        if getattr(et, 'es_principal', False):
            self._promover_principal(getattr(et, 'estudiante_id', None))

        self.audit.record(usuario, accion='DELETE', tabla='estudiante_tutor',
                          registro_id=relacion_id)
        return {'mensaje': 'Relacion eliminada'}
