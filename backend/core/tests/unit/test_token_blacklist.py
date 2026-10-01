from types import SimpleNamespace
from unittest.mock import patch

from core.views import logout_view


class TestTokenBlacklist:

    def test_logout_blacklists_token(self):
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.post("/api/auth/logout/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer test_token_123"
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.TokenBlacklist.objects.create") as mock_create:
            response = logout_view(request)
            assert response.status_code == 200
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert kwargs['token'] == 'test_token_123'
            assert kwargs['usuario'].id == 1
