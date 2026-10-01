from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import DocenteAsignacion
from core.views import courses_view, course_delete_view


class TestCourseViews:

    def test_list_courses_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/")
        response = courses_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_courses_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="director"),
        )
        with patch("core.views.CourseService.listar_cursos", return_value={"data": [], "total": 0}):
            response = courses_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_update_assignment(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/1/", {"gestion": 2027}, format="json")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="director"),
        )
        with patch("core.views.CourseService.actualizar_asignacion", return_value={"id": 1, "gestion": 2027}):
            response = course_delete_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

    def test_update_assignment_error_paths(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/1/", {"gestion": 2027}, format="json")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="director"),
        )
        with patch("core.views.CourseService.actualizar_asignacion", side_effect=PermissionError("Sin permiso")):
            response = course_delete_view(request, 1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        request = factory.put("/api/courses/1/", {"gestion": 2027}, format="json")
        request.usuario = SimpleNamespace(
            id=1, activo=True, nombre_completo="Admin",
            email="admin@test.com",
            rol=SimpleNamespace(nombre="director"),
        )
        with patch("core.views.CourseService.actualizar_asignacion", side_effect=DocenteAsignacion.DoesNotExist):
            response = course_delete_view(request, 1)
        assert response.status_code == status.HTTP_404_NOT_FOUND
