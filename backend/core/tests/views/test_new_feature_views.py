from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import student_history_view, enrollment_promote_view, config_view
from core.models import Estudiantes


class TestStudentHistoryView:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/1/history/")
        response = student_history_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/1/history/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.StudentsService.historial_academico", return_value={"id": 1, "inscripciones": [], "actividades": [], "observaciones": [], "asistencias": [], "resumen_asistencias": {}}):
            response = student_history_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/1/history/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.StudentsService.historial_academico", side_effect=PermissionError("no")):
            response = student_history_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/999/history/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.StudentsService.historial_academico", side_effect=Estudiantes.DoesNotExist):
            response = student_history_view(request, estudiante_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEnrollmentPromoteView:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/promote/", {}, format="json")
        response = enrollment_promote_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/promote/", {"origen_curso_id": 1, "destino_curso_id": 2, "origen_gestion": 2025, "destino_gestion": 2026}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.EnrollmentService.promocionar_estudiantes", return_value={"mensaje": "5 estudiantes promocionados", "promocionados": 5, "ya_inscritos": 0}):
            response = enrollment_promote_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/promote/", {"origen_curso_id": 1, "destino_curso_id": 2, "origen_gestion": 2025, "destino_gestion": 2026}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.EnrollmentService.promocionar_estudiantes", side_effect=PermissionError("no")):
            response = enrollment_promote_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_value_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/promote/", {}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.EnrollmentService.promocionar_estudiantes", side_effect=ValueError("no hay estudiantes")):
            response = enrollment_promote_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestConfigView:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/config/")
        response = config_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/config/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ConfigService.obtener", return_value={"nombre": "U.E. Test", "gestion_actual": 2026}):
            response = config_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/config/", {"nombre": "Nuevo nombre"}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ConfigService.actualizar", return_value={"nombre": "Nuevo nombre"}):
            response = config_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/config/", {}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ConfigService.actualizar", side_effect=PermissionError("no")):
            response = config_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/config/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ConfigService.obtener", side_effect=PermissionError("no")):
            response = config_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
