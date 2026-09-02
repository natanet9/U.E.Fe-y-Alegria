from ..models import ConfiguracionEscuela
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, ValidationError


@trace_service_class
class ConfigService:
    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def obtener(self, usuario):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')
        config, _ = ConfiguracionEscuela.objects.get_or_create(id=1)
        return {
            'id': config.id,
            'nombre': config.nombre,
            'direccion': config.direccion,
            'telefono': config.telefono,
            'email': config.email,
            'ciudad': config.ciudad,
            'gestion_actual': config.gestion_actual,
            'escala_aprobacion': float(config.escala_aprobacion),
        }

    def actualizar(self, usuario, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede modificar la configuracion')

        config, _ = ConfiguracionEscuela.objects.get_or_create(id=1)
        for campo in ('nombre', 'direccion', 'telefono', 'email', 'ciudad', 'gestion_actual', 'escala_aprobacion'):
            if campo in data:
                setattr(config, campo, data[campo])
        config.save()
        self.audit.record(usuario, accion='UPDATE', tabla='configuracion_escuela', registro_id=config.id, datos_nuevo={k: data[k] for k in data if k in data})
        return self.obtener(usuario)
