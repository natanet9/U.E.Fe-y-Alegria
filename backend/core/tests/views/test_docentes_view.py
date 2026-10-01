from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import docentes_view


class TestDocentesView:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/docentes/")
        response = docentes_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_returns_users_list(self):
        factory = APIRequestFactory()
        request = factory.get("/api/docentes/")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="secretaria"),
        )
        with patch("core.views.UserService.listar", return_value=[]):
            response = docentes_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_post_creates_user(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/", {"nombre": "Test"}, format="json")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="secretaria"),
        )
        with patch("core.views.UserService.crear", return_value={"id": 1}):
            response = docentes_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_validation_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/", {"nombre": ""}, format="json")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="secretaria"),
        )
        with patch("core.views.UserService.crear", side_effect=ValueError("Datos inválidos")):
            response = docentes_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/", {"nombre": "Test"}, format="json")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="secretaria"),
        )
        with patch("core.views.UserService.crear", side_effect=PermissionError("Sin permisos")):
            response = docentes_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
