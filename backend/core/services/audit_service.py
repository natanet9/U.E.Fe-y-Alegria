from uuid import uuid4

from django.utils import timezone

from ..models import AuditLog
from ..tracing import trace_service_class
from .access_service import AccessControlService


@trace_service_class
class AuditService:

    def __init__(self):
        self.ac = AccessControlService()

    def record(self, usuario, *, accion, tabla, registro_id=None, datos_anterior=None, datos_nuevo=None):
        if not usuario:
            return
        AuditLog.objects.create(
            tabla=tabla,
            registro_id=registro_id,
            accion=accion,
            datos_anterior=datos_anterior,
            datos_nuevo=datos_nuevo,
            usuario=usuario,
            fecha_cambio=timezone.now(),
        )

    def record_nota_change(self, usuario, actividad_nota_id, valor_anterior, valor_nuevo, estudiante_id):
        self.record(
            usuario, accion='UPDATE', tabla='actividad_notas',
            registro_id=actividad_nota_id,
            datos_anterior={'valor': float(valor_anterior) if valor_anterior else None},
            datos_nuevo={'valor': float(valor_nuevo) if valor_nuevo else None, 'estudiante_id': estudiante_id},
        )

    def record_actividad_change(self, usuario, accion, actividad_id, data=None):
        self.record(
            usuario, accion=accion, tabla='actividades',
            registro_id=actividad_id, datos_nuevo=data,
        )

    def record_estudiante_change(self, usuario, accion, estudiante_id, data=None):
        self.record(
            usuario, accion=accion, tabla='estudiantes',
            registro_id=estudiante_id, datos_nuevo=data,
        )

    def record_inscripcion_change(self, usuario, accion, inscripcion_id, data=None):
        self.record(
            usuario, accion=accion, tabla='inscripciones',
            registro_id=inscripcion_id, datos_nuevo=data,
        )

    def record_licencia_change(self, usuario, accion, licencia_id, data=None):
        self.record(
            usuario, accion=accion, tabla='licencias',
            registro_id=licencia_id, datos_nuevo=data,
        )

    def record_usuario_change(self, usuario, accion, usuario_id, data=None):
        self.record(
            usuario, accion=accion, tabla='usuarios',
            registro_id=usuario_id, datos_nuevo=data,
        )

    def historial_nota(self, usuario, nota_id):
        if not self.ac.puede_ver_auditoria(usuario):
            raise PermissionError('No autorizado')

        from ..models import AuditLog
        qs = AuditLog.objects.filter(
            tabla='actividad_notas',
            registro_id=nota_id,
        ).select_related('usuario').order_by('-fecha_cambio')

        return [
            {
                'id': entry.id,
                'accion': entry.accion,
                'valor_anterior': entry.datos_anterior,
                'valor_nuevo': entry.datos_nuevo,
                'usuario': entry.usuario.nombre_completo if entry.usuario else None,
                'fecha': entry.fecha_cambio.isoformat(),
            }
            for entry in qs
        ]

    def listar(self, usuario, tabla=None, registro_id=None, accion=None, page=1, page_size=20):
        if not usuario:
            raise PermissionError('No autorizado')

        ac = AccessControlService()
        if not ac.puede_ver_auditoria(usuario):
            raise PermissionError('Solo administradores pueden ver auditoria')

        qs = AuditLog.objects.select_related('usuario').all().order_by('-fecha_cambio')
        if tabla:
            qs = qs.filter(tabla=tabla)
        if registro_id:
            qs = qs.filter(registro_id=registro_id)
        if accion:
            qs = qs.filter(accion=accion)

        if page is None:
            return [
                {
                    'id': entry.id,
                    'tabla': entry.tabla,
                    'registro_id': entry.registro_id,
                    'accion': entry.accion,
                    'datos_anterior': entry.datos_anterior,
                    'datos_nuevo': entry.datos_nuevo,
                    'usuario': entry.usuario.nombre_completo if entry.usuario else None,
                    'fecha': entry.fecha_cambio.isoformat(),
                }
                for entry in qs
            ]

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]

        return {
            'data': [
                {
                    'id': entry.id,
                    'tabla': entry.tabla,
                    'registro_id': entry.registro_id,
                    'accion': entry.accion,
                    'datos_anterior': entry.datos_anterior,
                    'datos_nuevo': entry.datos_nuevo,
                    'usuario': entry.usuario.nombre_completo if entry.usuario else None,
                    'fecha': entry.fecha_cambio.isoformat(),
                }
                for entry in items
            ],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }
