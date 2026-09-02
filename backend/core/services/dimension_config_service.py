from ..models import DimensionConfigPeriodo, DimensionesEvaluacion, Periodos
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_puntaje_maximo, ValidationError


@trace_service_class
class DimensionConfigService:
    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar(self, usuario, periodo_id=None):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver configuraciones')

        qs = DimensionConfigPeriodo.objects.select_related('periodo', 'dimension').all()
        if periodo_id:
            qs = qs.filter(periodo_id=periodo_id)

        return [
            {
                'id': c.id,
                'periodo_id': c.periodo_id,
                'periodo_nombre': str(c.periodo),
                'dimension_id': c.dimension_id,
                'dimension_nombre': c.dimension.nombre,
                'puntaje_maximo': float(c.puntaje_maximo),
            }
            for c in qs.order_by('periodo__gestion', 'periodo__nombre', 'dimension__orden')
        ]

    def crear(self, usuario, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede configurar dimensiones')

        validar_required(data, ['periodo_id', 'dimension_id', 'puntaje_maximo'])
        validar_puntaje_maximo(data.get('puntaje_maximo'))

        config = DimensionConfigPeriodo.objects.create(
            periodo_id=data['periodo_id'],
            dimension_id=data['dimension_id'],
            puntaje_maximo=data['puntaje_maximo'],
        )
        self.audit.record(usuario, accion='CREATE', tabla='dimension_config_periodo', registro_id=config.id, datos_nuevo={'periodo_id': data['periodo_id'], 'dimension_id': data['dimension_id'], 'puntaje_maximo': data['puntaje_maximo']})
        return {
            'id': config.id,
            'periodo_id': config.periodo_id,
            'dimension_id': config.dimension_id,
            'puntaje_maximo': float(config.puntaje_maximo),
        }

    def actualizar(self, usuario, config_id, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede modificar configuraciones')

        config = DimensionConfigPeriodo.objects.get(id=config_id)
        if 'puntaje_maximo' in data:
            validar_puntaje_maximo(data['puntaje_maximo'])
            config.puntaje_maximo = data['puntaje_maximo']
        if 'dimension_id' in data:
            config.dimension_id = data['dimension_id']
        config.save()
        self.audit.record(usuario, accion='UPDATE', tabla='dimension_config_periodo', registro_id=config.id, datos_nuevo={k: data[k] for k in data if k in data})
        return {
            'id': config.id,
            'periodo_id': config.periodo_id,
            'dimension_id': config.dimension_id,
            'puntaje_maximo': float(config.puntaje_maximo),
        }

    def eliminar(self, usuario, config_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar configuraciones')

        DimensionConfigPeriodo.objects.filter(id=config_id).delete()
        self.audit.record(usuario, accion='DELETE', tabla='dimension_config_periodo', registro_id=config_id)
        return {'mensaje': 'Configuracion eliminada'}
