from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import students_view


class TestStudentViews:

    def test_list_students_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/")
        response = students_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_students_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        payload = {"total": 0, "estudiantes": []}
        with patch("core.views.StudentsService.listar", return_value=payload):
            response = students_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload

    def test_create_student_authenticated(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/", {"nombres": "Nuevo", "primer_apellido": "Test", "rude": "R001", "ci": "123"}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        created = {"id": 1, "nombres": "Nuevo", "primer_apellido": "Test"}
        with patch("core.views.StudentsService.crear", return_value=created):
            response = students_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["estudiante"]["id"] == 1

    def test_create_student_permision_denied(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/", {}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.StudentsService.crear", side_effect=PermissionError("sin permisos")):
            response = students_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_student_invalid(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/", {}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.StudentsService.crear", side_effect=ValueError("datos invalidos")):
            response = students_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
