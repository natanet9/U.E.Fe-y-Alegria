import pytest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from core.services.notification_service import NotificationService


@pytest.fixture
def service():
    return NotificationService()


class TestNotificationService:

    def test_notificar_directores_creates_notifications(self, service):
        directores = [
            SimpleNamespace(id=1, nombre_completo="Dir A"),
            SimpleNamespace(id=2, nombre_completo="Dir B"),
        ]
        with patch('core.models.Usuarios.objects.filter') as mock_filter:
            mock_filter.return_value = directores
            with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
                service.notificar_directores("Test message", tipo="warning", link="/test")
                assert mock_create.call_count == 2
                mock_create.assert_any_call(
                    usuario=directores[0], mensaje="Test message", tipo="warning", link="/test"
                )
                mock_create.assert_any_call(
                    usuario=directores[1], mensaje="Test message", tipo="warning", link="/test"
                )

    def test_notificar_directores_default_params(self, service):
        directores = [SimpleNamespace(id=1, nombre_completo="Dir A")]
        with patch('core.models.Usuarios.objects.filter') as mock_filter:
            mock_filter.return_value = directores
            with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
                service.notificar_directores("Alert")
                mock_create.assert_called_once_with(
                    usuario=directores[0], mensaje="Alert", tipo="info", link=None
                )

    def test_notificar_directores_empty(self, service):
        with patch('core.models.Usuarios.objects.filter') as mock_filter:
            mock_filter.return_value = []
            with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
                service.notificar_directores("Test")
                mock_create.assert_not_called()

    def test_notificar_directores_filters_only_active(self, service):
        with patch('core.models.Usuarios.objects.filter') as mock_filter:
            mock_filter.return_value = []
            service.notificar_directores("Test")
            mock_filter.assert_called_once_with(rol__nombre='director', activo=True)

    def test_notificar_cierre_proximo_skip_when_not_active(self, service):
        periodo = MagicMock(estado='cerrado')
        result = service.notificar_cierre_proximo(periodo)
        assert result is None

    def test_notificar_cierre_proximo_skip_when_far(self, service):
        from datetime import date
        periodo = MagicMock(estado='activo', fecha_fin=date.today() + timedelta(days=10))
        result = service.notificar_cierre_proximo(periodo)
        assert result is None

    def test_notificar_cierre_proximo_creates_notifications(self, service):
        from datetime import date
        periodo = MagicMock(
            estado='activo',
            nombre='Bim1',
            gestion=2026,
            fecha_fin=date.today() + timedelta(days=3),
        )
        docentes = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        with patch('core.models.Usuarios.objects.filter') as mock_u:
            mock_u.return_value.distinct.return_value = docentes
            with patch('core.services.notification_service.Notificacion.objects.filter') as mock_n:
                mock_n.return_value.exists.return_value = False
                with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
                    result = service.notificar_cierre_proximo(periodo)
                    assert result == 2
                    assert mock_create.call_count == 2

    def test_notificar_periodo_cerrado(self, service):
        from datetime import date
        periodo = MagicMock(estado='cerrado', nombre='Bim1', gestion=2026)
        cerrado_por = MagicMock(nombre_completo="Director")
        docentes = [SimpleNamespace(id=1)]
        with patch('core.models.Usuarios.objects.filter') as mock_u:
            mock_u.return_value.distinct.return_value = docentes
            with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
                service.notificar_periodo_cerrado(periodo, cerrado_por)
                mock_create.assert_called_once()
                args = mock_create.call_args[1]
                assert 'cerrado por Director' in args['mensaje']
                assert args['tipo'] == 'alert'

    def test_notificar_periodo_cerrado_skip_when_not_closed(self, service):
        periodo = MagicMock(estado='activo')
        with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
            service.notificar_periodo_cerrado(periodo, MagicMock())
            mock_create.assert_not_called()

    def test_crear_notification(self, service):
        usuario = MagicMock(id=1)
        with patch('core.services.notification_service.Notificacion.objects.create') as mock_create:
            mock_notif = MagicMock(id=10, mensaje="Test", tipo="info", link="/test",
                                   leida=False, created_at=MagicMock(isoformat=lambda: "2026-01-01"))
            mock_create.return_value = mock_notif
            result = service.crear(usuario, "Test", tipo="info", link="/test")
            assert result['id'] == 10
            assert result['mensaje'] == "Test"
            mock_create.assert_called_once_with(
                usuario=usuario, mensaje="Test", tipo="info", link="/test"
            )

    def test_listar_notifications(self, service):
        usuario = MagicMock(id=1)
        mock_qs = MagicMock()
        mock_qs.count.return_value = 1
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__.return_value = [
            MagicMock(id=1, mensaje="A", tipo="info", link="/a", leida=False,
                      created_at=MagicMock(isoformat=lambda: "2026-01-01"))
        ]
        with patch('core.services.notification_service.Notificacion.objects.filter') as mock_filter:
            mock_filter.return_value = mock_qs
            with patch.object(service, 'contar_no_leidas', return_value=0):
                result = service.listar(usuario)
                assert result['total'] == 1
                assert result['data'][0]['mensaje'] == "A"

    def test_marcar_leida(self, service):
        usuario = MagicMock(id=1)
        notif = MagicMock(id=5, leida=False, mensaje="X", tipo="info", link=None,
                          created_at=MagicMock(isoformat=lambda: "2026-01-01"))
        with patch('core.services.notification_service.Notificacion.objects.get') as mock_get:
            mock_get.return_value = notif
            result = service.marcar_leida(usuario, 5)
            assert result['id'] == 5
            assert notif.leida is True
            notif.save.assert_called_once_with(update_fields=['leida'])

    def test_contar_no_leidas(self, service):
        usuario = MagicMock(id=1)
        with patch('core.services.notification_service.Notificacion.objects.filter') as mock_filter:
            mock_filter.return_value.count.return_value = 3
            result = service.contar_no_leidas(usuario)
            assert result == 3
