from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import Periodos
from core.views import periodos_view, periodo_detail_view


USUARIO = SimpleNamespace(
    id=1, activo=True, nombre_completo="Sec",
    email="sec@test.com",
    rol=SimpleNamespace(nombre="secretaria"),
)


class TestPeriodosView:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/")
        response = periodos_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_lists_periodos(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.listar", return_value=[]):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_post_creates_periodo(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", return_value={"id": 1}):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_validation_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", side_effect=ValueError("Datos inválidos")):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", side_effect=PermissionError("Sin permisos")):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_periodo_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", side_effect=Periodos.DoesNotExist):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_get_put_delete(self):
        factory = APIRequestFactory()

        request = factory.get("/api/periodos/1/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.obtener", return_value={"id": 1, "nombre": "P1"}):
            response = periodo_detail_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

        request = factory.put("/api/periodos/1/", {"nombre": "P2"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.actualizar", return_value={"id": 1, "nombre": "P2"}):
            response = periodo_detail_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

        request = factory.delete("/api/periodos/1/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.eliminar", return_value={"mensaje": "Periodo eliminado"}):
            response = periodo_detail_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

    def test_detail_error_paths(self):
        factory = APIRequestFactory()

        request = factory.get("/api/periodos/1/")
        with patch("core.views.PeriodoService.obtener", side_effect=Periodos.DoesNotExist):
            response = periodo_detail_view(request, 1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        request.usuario = USUARIO
        with patch("core.views.PeriodoService.obtener", side_effect=Periodos.DoesNotExist):
            response = periodo_detail_view(request, 1)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        with patch("core.views.PeriodoService.actualizar", side_effect=PermissionError("Sin permiso")):
            request = factory.put("/api/periodos/1/", {"nombre": "X"}, format="json")
            request.usuario = USUARIO
            response = periodo_detail_view(request, 1)
        assert response.status_code == status.HTTP_403_FORBIDDEN
