from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import health_view, login_view, logout_view, me_view


class TestAuthViews:

    def test_health_view(self):
        factory = APIRequestFactory()
        request = factory.get("/api/health/")
        response = health_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    def test_login_missing_fields(self):
        factory = APIRequestFactory()
        request = factory.post("/api/login/", {"email": ""}, format="json")
        response = login_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/login/", {"email": "a@b.com", "password": "p"}, format="json")
        with patch("core.views.AuthService.login", return_value=({"token": "x", "usuario": {"email": "a@b.com"}}, None)):
            response = login_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["token"] == "x"

    def test_login_failure(self):
        factory = APIRequestFactory()
        request = factory.post("/api/login/", {"email": "a@b.com", "password": "wrong"}, format="json")
        with patch("core.views.AuthService.login", return_value=(None, "Credenciales invalidas")):
            response = login_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        response = me_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_user(self):
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        request.usuario = SimpleNamespace(id=1, nombre_completo="Ana", email="test@test.com", activo=True)
        with patch("core.views.AuthService.get_me", return_value={"email": "test@test.com", "nombre_completo": "Ana"}):
            response = me_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["usuario"]["email"] == "test@test.com"

    def test_logout(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/logout/")
        response = logout_view(request)
        assert response.status_code == status.HTTP_200_OK
