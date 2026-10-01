from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import (
    ActividadNotas, DimensionConfigPeriodo, EstudianteTutor,
    Inscripciones, Periodos, Tutores,
)
from core.views import (
    schedule_delete_view,
    periodos_view, periodo_detail_view,
    dimension_config_view, dimension_config_detail_view,
    catalog_view, catalog_delete_view,
    tutores_view, tutor_detail_view,
    inscripciones_view, inscripcion_detail_view,
    mark_periodo_enviado_view,
    estudiante_tutor_view, estudiante_tutor_delete_view,
    actividad_nota_detail_view,
    attendance_admin_view,
)

USUARIO = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
USUARIO_SEC = SimpleNamespace(
    id=1, activo=True, nombre_completo="Secretaria", email="sec@test.com",
    rol=SimpleNamespace(nombre="secretaria"),
)


# ── schedule_delete_view ────────────────────────────────────────────────────────


class TestScheduleDeleteViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/schedules/1/")
        response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/schedules/1/")
        request.usuario = USUARIO
        with patch("core.views.ScheduleService.eliminar_horario", return_value=None):
            response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/schedules/1/")
        request.usuario = USUARIO
        with patch("core.views.ScheduleService.eliminar_horario", side_effect=PermissionError("no")):
            response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_exception(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/schedules/1/")
        request.usuario = USUARIO
        with patch("core.views.ScheduleService.eliminar_horario", side_effect=ValueError("mal")):
            response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── periodos_view ───────────────────────────────────────────────────────────────


class TestPeriodosNewViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/")
        response = periodos_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/?gestion=2026")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.listar", return_value={"results": [], "total": 0}):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_post_crear_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", return_value={"id": 1}):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_habilitar_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "habilitar", "periodo_id": 1}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.habilitar", return_value={"id": 1, "habilitado": True}):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_post_cerrar_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "cerrar", "periodo_id": 1}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.cerrar", return_value={"id": 1, "cerrado": True}):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_post_accion_desconocida(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "unknown"}, format="json")
        request.usuario = USUARIO
        response = periodos_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", side_effect=PermissionError("no")):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_value_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", side_effect=ValueError("mal")):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/", {"accion": "crear"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.crear", side_effect=Periodos.DoesNotExist):
            response = periodos_view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── periodo_detail_view ─────────────────────────────────────────────────────────


class TestPeriodoDetailNewViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/1/")
        response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/1/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.obtener", return_value={"id": 1, "nombre": "P1"}):
            response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/1/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.obtener", side_effect=PermissionError("no")):
            response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/periodos/999/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.obtener", side_effect=Periodos.DoesNotExist):
            response = periodo_detail_view(request, periodo_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/periodos/1/", {"nombre": "P2"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.actualizar", return_value={"id": 1, "nombre": "P2"}):
            response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/periodos/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.actualizar", side_effect=PermissionError("no")):
            response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/periodos/999/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.actualizar", side_effect=Periodos.DoesNotExist):
            response = periodo_detail_view(request, periodo_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/periodos/1/")
        response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/periodos/1/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.eliminar", return_value={"mensaje": "Periodo eliminado"}):
            response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/periodos/1/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.eliminar", side_effect=PermissionError("no")):
            response = periodo_detail_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/periodos/999/")
        request.usuario = USUARIO
        with patch("core.views.PeriodoService.eliminar", side_effect=Periodos.DoesNotExist):
            response = periodo_detail_view(request, periodo_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── dimension_config_view ───────────────────────────────────────────────────────


class TestDimensionConfigViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dimension-config/")
        response = dimension_config_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dimension-config/?periodo_id=1")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.listar", return_value=[]):
            response = dimension_config_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dimension-config/")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.listar", side_effect=PermissionError("no")):
            response = dimension_config_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/dimension-config/", {}, format="json")
        response = dimension_config_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/dimension-config/", {"nombre": "Dim1"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.crear", return_value={"id": 1, "nombre": "Dim1"}):
            response = dimension_config_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/dimension-config/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.crear", side_effect=PermissionError("no")):
            response = dimension_config_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_value_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/dimension-config/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.crear", side_effect=ValueError("mal")):
            response = dimension_config_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── dimension_config_detail_view ────────────────────────────────────────────────


class TestDimensionConfigDetailViews:

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/dimension-config/1/", {}, format="json")
        response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/dimension-config/1/", {"nombre": "Actualizado"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.actualizar", return_value={"id": 1, "nombre": "Actualizado"}):
            response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/dimension-config/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.actualizar", side_effect=PermissionError("no")):
            response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/dimension-config/999/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.actualizar", side_effect=DimensionConfigPeriodo.DoesNotExist):
            response = dimension_config_detail_view(request, config_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_value_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/dimension-config/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.actualizar", side_effect=ValueError("mal")):
            response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/dimension-config/1/")
        response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/dimension-config/1/")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.eliminar", return_value=None):
            response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/dimension-config/1/")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.eliminar", side_effect=PermissionError("no")):
            response = dimension_config_detail_view(request, config_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/dimension-config/999/")
        request.usuario = USUARIO
        with patch("core.views.DimensionConfigService.eliminar", side_effect=DimensionConfigPeriodo.DoesNotExist):
            response = dimension_config_detail_view(request, config_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── catalog_view ────────────────────────────────────────────────────────────────


class TestCatalogViews:

    def test_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/catalogos/niveles/")
        response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/catalogos/niveles/")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.listar_niveles", return_value={"results": [], "total": 0}):
            response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_200_OK

    def test_list_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/catalogos/niveles/")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.listar_niveles", side_effect=PermissionError("no")):
            response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_modelo_desconocido(self):
        factory = APIRequestFactory()
        request = factory.get("/api/catalogos/unknown/")
        request.usuario = USUARIO
        response = catalog_view(request, modelo="unknown")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/catalogos/niveles/", {"nombre": "Nuevo"}, format="json")
        response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/catalogos/niveles/", {"nombre": "Nuevo"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.crear_niveles", return_value={"id": 1, "nombre": "Nuevo"}):
            response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/catalogos/niveles/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.crear_niveles", side_effect=PermissionError("no")):
            response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_value_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/catalogos/niveles/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.crear_niveles", side_effect=ValueError("mal")):
            response = catalog_view(request, modelo="niveles")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_grados_with_nivel_id(self):
        factory = APIRequestFactory()
        request = factory.get("/api/catalogos/grados/?nivel_id=1")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.listar_grados", return_value={"results": [], "total": 0}):
            response = catalog_view(request, modelo="grados")
        assert response.status_code == status.HTTP_200_OK

    def test_list_cursos_with_grado_id(self):
        factory = APIRequestFactory()
        request = factory.get("/api/catalogos/cursos/?grado_id=1")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.listar_cursos", return_value={"results": [], "total": 0}):
            response = catalog_view(request, modelo="cursos")
        assert response.status_code == status.HTTP_200_OK


# ── catalog_delete_view ─────────────────────────────────────────────────────────


class TestCatalogDeleteViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/catalogos/niveles/1/")
        response = catalog_delete_view(request, modelo="niveles", item_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/catalogos/niveles/1/")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.eliminar_niveles", return_value={"mensaje": "eliminado"}):
            response = catalog_delete_view(request, modelo="niveles", item_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/catalogos/niveles/1/")
        request.usuario = USUARIO
        with patch("core.views.CatalogService.eliminar_niveles", side_effect=PermissionError("no")):
            response = catalog_delete_view(request, modelo="niveles", item_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_modelo_no_eliminable(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/catalogos/unknown/1/")
        request.usuario = USUARIO
        response = catalog_delete_view(request, modelo="unknown", item_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── tutores_view ────────────────────────────────────────────────────────────────


class TestTutoresViews:

    def test_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/")
        response = tutores_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.listar", return_value={"results": [], "total": 0}):
            response = tutores_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_list_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.listar", side_effect=PermissionError("no")):
            response = tutores_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/tutores/", {}, format="json")
        response = tutores_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/tutores/", {"nombre": "Tutor1"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.crear", return_value={"id": 1, "nombre": "Tutor1"}):
            response = tutores_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/tutores/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.crear", side_effect=PermissionError("no")):
            response = tutores_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_value_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/tutores/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.crear", side_effect=ValueError("mal")):
            response = tutores_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── tutor_detail_view ───────────────────────────────────────────────────────────


class TestTutorDetailViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/1/")
        response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/1/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.obtener", return_value={"id": 1, "nombre": "Tutor1"}):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/1/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.obtener", side_effect=PermissionError("no")):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/tutores/999/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.obtener", side_effect=Tutores.DoesNotExist):
            response = tutor_detail_view(request, tutor_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/tutores/1/", {}, format="json")
        response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/tutores/1/", {"nombre": "Actualizado"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.actualizar", return_value={"id": 1, "nombre": "Actualizado"}):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/tutores/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.actualizar", side_effect=PermissionError("no")):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/tutores/999/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.actualizar", side_effect=Tutores.DoesNotExist):
            response = tutor_detail_view(request, tutor_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_value_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/tutores/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.actualizar", side_effect=ValueError("mal")):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/tutores/1/")
        response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/tutores/1/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.eliminar", return_value={"mensaje": "eliminado"}):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/tutores/1/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.eliminar", side_effect=PermissionError("no")):
            response = tutor_detail_view(request, tutor_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/tutores/999/")
        request.usuario = USUARIO
        with patch("core.views.TutoresService.eliminar", side_effect=Tutores.DoesNotExist):
            response = tutor_detail_view(request, tutor_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── inscripciones_view ──────────────────────────────────────────────────────────


class TestInscripcionesViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/")
        response = inscripciones_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/?curso_id=1&gestion=2026")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.listar", return_value={"results": [], "total": 0}):
            response = inscripciones_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.listar", side_effect=PermissionError("no")):
            response = inscripciones_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── inscripcion_detail_view ─────────────────────────────────────────────────────


class TestInscripcionDetailViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/1/")
        response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/1/")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.obtener", return_value={"id": 1, "estudiante": {"id": 1}}):
            response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/1/")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.obtener", side_effect=PermissionError("no")):
            response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/inscripciones/999/")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.obtener", side_effect=Inscripciones.DoesNotExist):
            response = inscripcion_detail_view(request, inscripcion_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/inscripciones/1/", {}, format="json")
        response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_success(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/inscripciones/1/", {"estado": "ACTIVO"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.actualizar_estado", return_value={"id": 1, "estado": "ACTIVO"}):
            response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_patch_sin_estado(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/inscripciones/1/", {}, format="json")
        request.usuario = USUARIO
        response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_permission_error(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/inscripciones/1/", {"estado": "ACTIVO"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.actualizar_estado", side_effect=PermissionError("no")):
            response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_not_found(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/inscripciones/999/", {"estado": "ACTIVO"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.actualizar_estado", side_effect=Inscripciones.DoesNotExist):
            response = inscripcion_detail_view(request, inscripcion_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_value_error(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/inscripciones/1/", {"estado": "INVALIDO"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.InscripcionesService.actualizar_estado", side_effect=ValueError("mal")):
            response = inscripcion_detail_view(request, inscripcion_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── mark_periodo_enviado_view ───────────────────────────────────────────────────


class TestMarkPeriodoEnviadoViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/1/marcar-enviado/")
        response = mark_periodo_enviado_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_permiso(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/1/marcar-enviado/")
        request.usuario = USUARIO
        with patch("core.views.AccessControlService.es_secretaria", return_value=False), \
             patch("core.views.AccessControlService.es_director", return_value=False):
            response = mark_periodo_enviado_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/1/marcar-enviado/")
        request.usuario = USUARIO_SEC
        mock_periodo = MagicMock()
        mock_periodo.id = 1
        with patch("core.views.AccessControlService.es_secretaria", return_value=True), \
             patch("core.views.Periodos.objects.get", return_value=mock_periodo), \
             patch("core.views.AuditService.record"):
            response = mark_periodo_enviado_view(request, periodo_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/periodos/999/marcar-enviado/")
        request.usuario = USUARIO_SEC
        with patch("core.views.AccessControlService.es_secretaria", return_value=True), \
             patch("core.views.Periodos.objects.get", side_effect=Periodos.DoesNotExist):
            response = mark_periodo_enviado_view(request, periodo_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── estudiante_tutor_view ───────────────────────────────────────────────────────


class TestEstudianteTutorViews:

    def test_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/estudiante-tutor/")
        response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/estudiante-tutor/?estudiante_id=1")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.listar", return_value=[]):
            response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_list_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/estudiante-tutor/")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.listar", side_effect=PermissionError("no")):
            response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/estudiante-tutor/", {}, format="json")
        response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/estudiante-tutor/", {"estudiante_id": 1, "tutor_id": 1}, format="json")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.crear", return_value={"id": 1, "estudiante_id": 1, "tutor_id": 1}):
            response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/estudiante-tutor/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.crear", side_effect=PermissionError("no")):
            response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_value_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/estudiante-tutor/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.crear", side_effect=ValueError("mal")):
            response = estudiante_tutor_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── estudiante_tutor_delete_view ────────────────────────────────────────────────


class TestEstudianteTutorDeleteViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/estudiante-tutor/1/")
        response = estudiante_tutor_delete_view(request, relacion_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/estudiante-tutor/1/")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.eliminar", return_value={"mensaje": "eliminado"}):
            response = estudiante_tutor_delete_view(request, relacion_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/estudiante-tutor/1/")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.eliminar", side_effect=PermissionError("no")):
            response = estudiante_tutor_delete_view(request, relacion_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/estudiante-tutor/999/")
        request.usuario = USUARIO
        with patch("core.views.EstudianteTutorService.eliminar", side_effect=EstudianteTutor.DoesNotExist):
            response = estudiante_tutor_delete_view(request, relacion_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── actividad_nota_detail_view ──────────────────────────────────────────────────


class TestActividadNotaDetailViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/notas/1/")
        response = actividad_nota_detail_view(request, nota_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/notas/1/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.obtener_nota", return_value={"id": 1, "nota": 10.0}):
            response = actividad_nota_detail_view(request, nota_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/notas/1/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.obtener_nota", side_effect=PermissionError("no")):
            response = actividad_nota_detail_view(request, nota_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/notas/999/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.obtener_nota", side_effect=ActividadNotas.DoesNotExist):
            response = actividad_nota_detail_view(request, nota_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/notas/1/")
        response = actividad_nota_detail_view(request, nota_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/notas/1/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.eliminar_nota", return_value={"mensaje": "eliminado"}):
            response = actividad_nota_detail_view(request, nota_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/notas/1/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.eliminar_nota", side_effect=PermissionError("no")):
            response = actividad_nota_detail_view(request, nota_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/notas/999/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.eliminar_nota", side_effect=ActividadNotas.DoesNotExist):
            response = actividad_nota_detail_view(request, nota_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── attendance_admin_view ───────────────────────────────────────────────────────


class TestAttendanceAdminViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/attendance/admin/")
        response = attendance_admin_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/attendance/admin/?fecha=2026-05-01")
        request.usuario = USUARIO
        with patch("core.views.AttendanceService.listar_asistencias_admin", return_value=[{"id": 1}]):
            response = attendance_admin_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/attendance/admin/")
        request.usuario = USUARIO
        with patch("core.views.AttendanceService.listar_asistencias_admin", side_effect=PermissionError("no")):
            response = attendance_admin_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
