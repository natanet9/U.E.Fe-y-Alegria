from django.utils import timezone

from ..models import Notificacion
from ..tracing import trace_service_class
from .access_service import AccessControlService


@trace_service_class
class NotificationService:

    def __init__(self):
        self.ac = AccessControlService()

    def crear(self, usuario, mensaje, tipo='info', link=None):
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            mensaje=mensaje,
            tipo=tipo,
            link=link,
        )
        return self._to_dict(notificacion)

    def listar(self, usuario, solo_no_leidas=False, page=1, page_size=20):
        qs = Notificacion.objects.filter(usuario=usuario)
        if solo_no_leidas:
            qs = qs.filter(leida=False)
        qs = qs.order_by('-created_at')

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]
        return {
            'data': [self._to_dict(n) for n in items],
            'total': total,
            'no_leidas': Notificacion.objects.filter(usuario=usuario, leida=False).count(),
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def marcar_leida(self, usuario, notificacion_id):
        notif = Notificacion.objects.get(id=notificacion_id, usuario=usuario)
        notif.leida = True
        notif.save(update_fields=['leida'])
        return self._to_dict(notif)

    def marcar_todas_leidas(self, usuario):
        Notificacion.objects.filter(usuario=usuario, leida=False).update(leida=True)
        return {'mensaje': 'Notificaciones marcadas como leidas'}

    def contar_no_leidas(self, usuario):
        return Notificacion.objects.filter(usuario=usuario, leida=False).count()

    def notificar_cierre_proximo(self, periodo):
        """Crea notificaciones para todos los docentes del periodo activo
        cuando se acerca la fecha de cierre."""
        from ..models import DocenteAsignacion, Usuarios
        from datetime import date, timedelta

        if periodo.estado != 'activo':
            return

        dias_restantes = (periodo.fecha_fin - date.today()).days
        if dias_restantes > 7 or dias_restantes < 0:
            return

        mensaje = (
            f"El {periodo.nombre} {periodo.gestion} cierra el {periodo.fecha_fin}. "
            f"Quedan {dias_restantes} dia{'s' if dias_restantes != 1 else ''}. "
            "Registra todas tus notas antes del cierre."
        )
        tipo = 'warning' if dias_restantes <= 3 else 'info'

        docentes = Usuarios.objects.filter(
            rol__nombre='docente',
            activo=True,
            docenteasignacion__gestion=periodo.gestion,
            docenteasignacion__activo=True,
        ).distinct()

        creadas = 0
        for docente in docentes:
            # Evitar duplicados: no crear si ya hay una notificacion similar en las ultimas 24h
            ya_notificado = Notificacion.objects.filter(
                usuario=docente,
                mensaje=mensaje,
                created_at__gte=timezone.now() - timedelta(hours=24),
            ).exists()
            if not ya_notificado:
                Notificacion.objects.create(
                    usuario=docente,
                    mensaje=mensaje,
                    tipo=tipo,
                    link=f"/cursos",
                )
                creadas += 1
        return creadas

    def notificar_periodo_cerrado(self, periodo, cerrado_por):
        """Notifica a todos los docentes que el periodo fue cerrado."""
        from ..models import Usuarios

        if periodo.estado != 'cerrado':
            return

        mensaje = f"El {periodo.nombre} {periodo.gestion} ha sido cerrado por {cerrado_por.nombre_completo}. Las notas son definitivas."

        docentes = Usuarios.objects.filter(
            rol__nombre='docente',
            activo=True,
            docenteasignacion__gestion=periodo.gestion,
            docenteasignacion__activo=True,
        ).distinct()

        for docente in docentes:
            Notificacion.objects.create(
                usuario=docente,
                mensaje=mensaje,
                tipo='alert',
                link="/cursos",
            )

    def notificar_directores(self, mensaje, tipo='info', link=None):
        """Crea una notificacion para todos los usuarios con rol director."""
        from ..models import Usuarios
        directores = Usuarios.objects.filter(rol__nombre='director', activo=True)
        for director in directores:
            Notificacion.objects.create(
                usuario=director,
                mensaje=mensaje,
                tipo=tipo,
                link=link,
            )

    def _to_dict(self, notificacion):
        return {
            'id': notificacion.id,
            'mensaje': notificacion.mensaje,
            'tipo': notificacion.tipo,
            'leida': notificacion.leida,
            'link': notificacion.link,
            'created_at': notificacion.created_at.isoformat(),
        }
