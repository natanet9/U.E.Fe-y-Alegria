from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.services.auth_service import AuthService


class TestTokenRefresh:

    def test_refresh_success(self):
        service = AuthService()
        usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                                  last_login=None, rol=SimpleNamespace(id=1, nombre="secretaria"))
        with patch('core.services.auth_service.refresh_token', return_value='new_token_123'):
            with patch.object(service, 'get_me', return_value={"id": 1, "nombre": "Admin"}):
                result = service.refresh(usuario)
                assert result['token'] == 'new_token_123'
                assert 'usuario' in result
