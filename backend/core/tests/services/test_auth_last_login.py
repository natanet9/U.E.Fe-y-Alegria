from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from core.services.auth_service import AuthService


class TestAuthLastLogin:

    def test_login_records_last_login(self):
        service = AuthService()
        mock_usuario = MagicMock()
        mock_usuario.id = 1
        mock_usuario.activo = True
        mock_usuario.email = "admin@test.com"
        mock_usuario.nombre_completo = "Admin"
        mock_usuario.last_login = None
        mock_usuario.rol = SimpleNamespace(id=1, nombre="secretaria")

        with patch('core.services.auth_service.Usuarios.objects.select_related') as mock_qs:
            mock_qs.return_value.get.return_value = mock_usuario
            with patch('core.services.auth_service.check_password', return_value=True):
                with patch('core.services.auth_service.build_token', return_value='token123'):
                    response, error = service.login("admin@test.com", "pass123")
                    assert error is None
                    assert mock_usuario.last_login is not None
                    mock_usuario.save.assert_called_once_with(update_fields=['last_login'])
