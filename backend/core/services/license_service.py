from django.utils import timezone

from ..models import Licencias, Inscripciones, DocenteAsignacion, Docentes
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .notification_service import NotificationService
from .validation import validar_required, validar_fecha, validar_rango_fechas, ValidationError
from .pagination import paginar_desde_queryset


@trace_service_class
class LicenseService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()
        self.notif = NotificationService()

    def listar(self, usuario, estado=None, page=1, page_size=20):
        qs = Licencias.objects.select_related(
            'estudiante', 'tutor_solicitante', 'regente', 'aprobado_por'
        ).filter(activo=True).order_by('-created_at')

        if not self.ac.puede_ver_todo(usuario):
            if self.ac.es_regente(usuario):
                qs = qs.filter(regente=usuario)
            elif self.ac.es_docente(usuario):
                docente = Docentes.objects.filter(usuario=usuario).first()
                if not docente:
                    return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
                cursos_qs = DocenteAsignacion.objects.filter(
                    docente=docente, activo=True
                ).values('curso_id', 'gestion').distinct()
                estudiante_ids = Inscripciones.objects.filter(
                    estado='activo'
                ).filter(
                    curso_id__in=cursos_qs.values('curso_id'),
                    gestion__in=cursos_qs.values('gestion'),
                ).values_list('estudiante_id', flat=True).distinct()
                qs = qs.filter(estudiante_id__in=estudiante_ids)
            else:
                raise PermissionError('No tienes permisos para ver licencias')

        if estado:
            qs = qs.filter(estado=estado)

        result = paginar_desde_queryset(qs, page=page, page_size=page_size)
        result['items'] = [
            {
                'id': l.id,
                'estudiante_id': l.estudiante_id,
                'estudiante': f'{l.estudiante.nombres} {l.estudiante.primer_apellido}',
                'tutor': l.tutor_solicitante.nombres + ' ' + l.tutor_solicitante.primer_apellido if l.tutor_solicitante else None,
                'motivo': l.motivo,
                'fecha_inicio': str(l.fecha_inicio),
                'fecha_fin': str(l.fecha_fin),
                'dias': (l.fecha_fin - l.fecha_inicio).days + 1,
                'requiere_respaldo': l.requiere_respaldo,
                'respaldo_presentado': l.respaldo_presentado,
                'estado': l.estado,
                'regente': l.regente.nombre_completo if l.regente else None,
                'aprobado_por': l.aprobado_por.nombre_completo if l.aprobado_por else None,
                'aprobado_en': str(l.aprobado_en) if l.aprobado_en else None,
                'observaciones': l.observaciones or '',
            }
            for l in result['items']
        ]
        return result

    def crear(self, usuario, data):
        if not self.ac.puede_gestionar_licencias(usuario):
            raise PermissionError('No tienes permisos para gestionar licencias')

        validar_required(data, ['estudiante_id', 'motivo', 'fecha_inicio', 'fecha_fin'])
        validar_fecha(data.get('fecha_inicio'), 'fecha_inicio')
        validar_fecha(data.get('fecha_fin'), 'fecha_fin')
        validar_rango_fechas(
            validar_fecha(data.get('fecha_inicio')),
            validar_fecha(data.get('fecha_fin')),
            'Licencia',
        )

        estudiante_id = data.get('estudiante_id')
        motivo = data.get('motivo')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        licencia = Licencias.objects.create(
            estudiante_id=estudiante_id,
            tutor_solicitante_id=data.get('tutor_id'),
            regente=usuario if self.ac.es_regente(usuario) else None,
            motivo=motivo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            requiere_respaldo=data.get('requiere_respaldo', False),
        )
        self.audit.record_licencia_change(usuario, 'CREATE', licencia.id, {'estudiante_id': estudiante_id, 'motivo': motivo})
        self.notif.notificar_directores(
            f'Nueva licencia pendiente: {motivo[:60]}{"..." if len(motivo) > 60 else ""}',
            tipo='warning',
            link='/licencias',
        )
        return {'id': licencia.id, 'mensaje': 'Licencia creada exitosamente'}

    def obtener(self, usuario, licencia_id):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver licencias')

        licencia = Licencias.objects.select_related('estudiante', 'tutor_solicitante', 'regente', 'aprobado_por').get(id=licencia_id, activo=True)
        return {
            'id': licencia.id,
            'estudiante_id': licencia.estudiante_id,
            'estudiante': f'{licencia.estudiante.nombres} {licencia.estudiante.primer_apellido}',
            'tutor_id': licencia.tutor_solicitante_id,
            'motivo': licencia.motivo,
            'fecha_inicio': str(licencia.fecha_inicio),
            'fecha_fin': str(licencia.fecha_fin),
            'requiere_respaldo': licencia.requiere_respaldo,
            'respaldo_presentado': licencia.respaldo_presentado,
            'estado': licencia.estado,
            'observaciones': licencia.observaciones or '',
        }

    def actualizar(self, usuario, licencia_id, data):
        if not self.ac.puede_gestionar_licencias(usuario):
            raise PermissionError('No tienes permisos para gestionar licencias')

        licencia = Licencias.objects.get(id=licencia_id, activo=True)
        for campo in ('motivo', 'fecha_inicio', 'fecha_fin', 'requiere_respaldo', 'respaldo_presentado', 'observaciones'):
            if campo in data:
                setattr(licencia, campo, data[campo])
        licencia.save()
        self.audit.record_licencia_change(usuario, 'UPDATE', licencia_id, {k: data[k] for k in data if k in data})
        return {'id': licencia.id, 'mensaje': 'Licencia actualizada exitosamente'}

    def eliminar(self, usuario, licencia_id):
        if not self.ac.puede_gestionar_licencias(usuario):
            raise PermissionError('No tienes permisos para gestionar licencias')

        licencia = Licencias.objects.get(id=licencia_id)
        licencia.activo = False
        licencia.save(update_fields=['activo'])
        self.audit.record_licencia_change(usuario, 'DELETE', licencia_id, {})
        return {'mensaje': 'Licencia eliminada'}

    def marcar_respaldo(self, usuario, licencia_id):
        if not self.ac.puede_gestionar_licencias(usuario):
            raise PermissionError('No tienes permisos para gestionar licencias')

        licencia = Licencias.objects.get(id=licencia_id, activo=True)
        if not licencia.requiere_respaldo:
            raise ValueError('Esta licencia no requiere respaldo')

        licencia.respaldo_presentado = True
        licencia.save(update_fields=['respaldo_presentado'])
        self.audit.record(usuario, accion='UPDATE', tabla='licencias',
                          registro_id=licencia_id, datos_nuevo={'respaldo_presentado': True})
        return {'mensaje': 'Respaldo marcado como presentado', 'licencia_id': licencia_id}

    def aprobar(self, usuario, licencia_id, aceptar=True, observaciones=''):
        licencia = Licencias.objects.get(id=licencia_id, activo=True)
        dias = (licencia.fecha_fin - licencia.fecha_inicio).days + 1

        if not self.ac.puede_aprobar_licencia_directa(usuario, dias):
            if self.ac.es_regente(usuario):
                raise PermissionError('Las licencias de mas de 3 dias requieren aprobacion de secretaria')
            raise PermissionError('No tienes permisos para aprobar licencias')

        licencia.estado = 'aprobada' if aceptar else 'rechazada'
        licencia.aprobado_por = usuario
        licencia.aprobado_en = timezone.now()
        licencia.observaciones = observaciones
        licencia.save(update_fields=['estado', 'aprobado_por', 'aprobado_en', 'observaciones'])
        self.audit.record_licencia_change(usuario, 'APPROVE' if aceptar else 'REJECT', licencia_id, {'estado': licencia.estado})

        return {
            'id': licencia.id,
            'estado': licencia.estado,
            'mensaje': f'Licencia {"aprobada" if aceptar else "rechazada"} exitosamente',
        }
