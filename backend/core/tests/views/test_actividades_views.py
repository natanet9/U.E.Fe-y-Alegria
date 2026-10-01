from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import Actividades
from core.views import (
    actividades_view,
    actividad_delete_view,
    actividad_detail_view,
    actividades_notas_view,
    actividades_notas_estudiante_view,
)


def _make_usuario():
    return SimpleNamespace(
        id=1,
        activo=True,
        nombre_completo="Docente",
        email="doc@test.com",
        rol=SimpleNamespace(nombre="docente"),
    )


class TestActividadesViews:

    # ── actividades_view ────────────────────────────────────────────────────────

    def test_actividades_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/")
        response = actividades_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_actividades_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/?docente_asignacion_id=1")
        request.usuario = _make_usuario()
        actividades = [{"id": 1, "nombre": "Examen"}]
        with patch("core.views.ac.puede_editar_notas", return_value=True), \
             patch("core.views.ActivityService._list_actividades", return_value=actividades):
            response = actividades_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"actividades": actividades}

    def test_actividades_create_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/", {"nombre": "Examen"}, format="json")
        request.usuario = _make_usuario()
        actividad = {"id": 1, "nombre": "Examen"}
        with patch("core.views.ActivityService.crear_actividad", return_value=actividad):
            response = actividades_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {"mensaje": "Actividad creada", "actividad": actividad}

    def test_actividades_create_validation(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/", {}, format="json")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.crear_actividad", side_effect=ValueError("Error de validación")):
            response = actividades_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Error de validación"}

    def test_actividades_create_permision(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/", {}, format="json")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.crear_actividad", side_effect=PermissionError("Sin permiso")):
            response = actividades_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"error": "Sin permiso"}

    # ── actividad_delete_view ────────────────────────────────────────────────────

    def test_actividad_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_actividad_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.eliminar_actividad"):
            response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"mensaje": "Actividad eliminada"}

    def test_actividad_delete_permision(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.eliminar_actividad", side_effect=PermissionError("Sin permiso")):
            response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"error": "Sin permiso"}

    def test_actividad_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.eliminar_actividad", side_effect=Actividades.DoesNotExist):
            response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"error": "Actividad no encontrada"}

    def test_actividad_detail_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/1/detail/")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.obtener_actividad", return_value={"id": 1, "nombre": "Examen"}):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_actividad_detail_update(self):
        factory = APIRequestFactory()
        request = factory.put("/api/actividades/1/detail/", {"nombre": "Examen 2"}, format="json")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.actualizar_actividad", return_value={"id": 1, "nombre": "Examen 2"}):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_actividad_detail_error_paths(self):
        factory = APIRequestFactory()

        request = factory.get("/api/actividades/1/detail/")
        response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.obtener_actividad", side_effect=Actividades.DoesNotExist):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        request = factory.put("/api/actividades/1/detail/", {"nombre": "Examen 2"}, format="json")
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.actualizar_actividad", side_effect=PermissionError("Sin permiso")):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── actividades_notas_view ───────────────────────────────────────────────────

    def test_notas_guardar_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/notas/")
        response = actividades_notas_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_notas_guardar_success(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/actividades/notas/",
            {"actividad_id": 1, "notas": [{"estudiante_id": 1, "nota": 10.0}]},
            format="json",
        )
        request.usuario = _make_usuario()
        updated = [{"estudiante_id": 1, "nota": 10.0}]
        with patch("core.views.ActivityService.guardar_notas_actividad", return_value=updated):
            response = actividades_notas_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"mensaje": "Notas actualizadas", "updated_count": 1}

    def test_notas_guardar_permision(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/actividades/notas/",
            {"actividad_id": 1, "notas": []},
            format="json",
        )
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.guardar_notas_actividad", side_effect=PermissionError("Sin permiso")):
            response = actividades_notas_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"error": "Sin permiso"}

    # ── actividades_notas_estudiante_view ────────────────────────────────────────

    def test_notas_estudiante_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/notas/estudiante/")
        response = actividades_notas_estudiante_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_notas_estudiante_success(self):
        factory = APIRequestFactory()
        request = factory.get(
            "/api/actividades/notas/estudiante/?docente_asignacion_id=1&estudiante_id=1"
        )
        request.usuario = _make_usuario()
        notas = {"materia": "Matematicas", "calificaciones": []}
        with patch("core.views.ActivityService.get_notas_estudiante", return_value=notas):
            response = actividades_notas_estudiante_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"notas": notas}

    def test_notas_estudiante_permision(self):
        factory = APIRequestFactory()
        request = factory.get(
            "/api/actividades/notas/estudiante/?docente_asignacion_id=1&estudiante_id=1"
        )
        request.usuario = _make_usuario()
        with patch("core.views.ActivityService.get_notas_estudiante", side_effect=PermissionError("Sin permiso")):
            response = actividades_notas_estudiante_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"error": "Sin permiso"}
