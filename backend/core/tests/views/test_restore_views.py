from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import Actividades, DocenteAsignacion, Estudiantes, Usuarios
from core.views import (
    student_restore_view, student_delete_view, student_detail_view,
    docente_restore_view, docente_delete_view, docente_detail_view,
    course_restore_view, course_delete_view,
    actividad_restore_view, actividad_delete_view, actividad_detail_view,
)

USUARIO = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")


# ── Student restore, delete, detail ──────────────────────────────────────────────


class TestStudentRestoreViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/1/restore/")
        response = student_restore_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.restaurar", return_value={"mensaje": "restaurado"}):
            response = student_restore_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.restaurar", side_effect=PermissionError("no")):
            response = student_restore_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/999/restore/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.restaurar", side_effect=Estudiantes.DoesNotExist):
            response = student_restore_view(request, estudiante_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStudentDeleteViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/students/1/")
        response = student_delete_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/students/1/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.eliminar", return_value=None):
            response = student_delete_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/students/1/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.eliminar", side_effect=PermissionError("no")):
            response = student_delete_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/students/999/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.eliminar", side_effect=Estudiantes.DoesNotExist):
            response = student_delete_view(request, estudiante_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStudentDetailViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/1/detail/")
        response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/1/detail/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.obtener", return_value={"id": 1, "nombres": "Test"}):
            response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/1/detail/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.obtener", side_effect=PermissionError("no")):
            response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/999/detail/")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.obtener", side_effect=Estudiantes.DoesNotExist):
            response = student_detail_view(request, estudiante_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/students/1/detail/", {"nombres": "Updated"}, format="json")
        response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/students/1/detail/", {"nombres": "Updated"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.actualizar", return_value={"id": 1, "nombres": "Updated"}):
            response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/students/1/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.actualizar", side_effect=PermissionError("no")):
            response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/students/999/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.actualizar", side_effect=Estudiantes.DoesNotExist):
            response = student_detail_view(request, estudiante_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_value_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/students/1/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.StudentsService.actualizar", side_effect=ValueError("mal")):
            response = student_detail_view(request, estudiante_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Docente restore, delete, detail ─────────────────────────────────────────────


class TestDocenteRestoreViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/1/restore/")
        response = docente_restore_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.UserService.restaurar", return_value={"mensaje": "restaurado"}):
            response = docente_restore_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.UserService.restaurar", side_effect=PermissionError("no")):
            response = docente_restore_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/docentes/999/restore/")
        request.usuario = USUARIO
        with patch("core.views.UserService.restaurar", side_effect=Usuarios.DoesNotExist):
            response = docente_restore_view(request, usuario_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDocenteDeleteViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/docentes/1/")
        response = docente_delete_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/docentes/1/")
        request.usuario = USUARIO
        with patch("core.views.UserService.eliminar", return_value=None):
            response = docente_delete_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/docentes/1/")
        request.usuario = USUARIO
        with patch("core.views.UserService.eliminar", side_effect=PermissionError("no")):
            response = docente_delete_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/docentes/999/")
        request.usuario = USUARIO
        with patch("core.views.UserService.eliminar", side_effect=Usuarios.DoesNotExist):
            response = docente_delete_view(request, usuario_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDocenteDetailViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/docentes/1/detail/")
        response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/docentes/1/detail/")
        request.usuario = USUARIO
        with patch("core.views.UserService.obtener", return_value={"id": 1, "nombre_completo": "Docente"}):
            response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/docentes/1/detail/")
        request.usuario = USUARIO
        with patch("core.views.UserService.obtener", side_effect=PermissionError("no")):
            response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/docentes/999/detail/")
        request.usuario = USUARIO
        with patch("core.views.UserService.obtener", side_effect=Usuarios.DoesNotExist):
            response = docente_detail_view(request, usuario_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/docentes/1/detail/", {"nombre_completo": "Updated"}, format="json")
        response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/docentes/1/detail/", {"nombre_completo": "Updated"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.UserService.actualizar", return_value={"id": 1, "nombre_completo": "Updated"}):
            response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/docentes/1/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.UserService.actualizar", side_effect=PermissionError("no")):
            response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/docentes/999/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.UserService.actualizar", side_effect=Usuarios.DoesNotExist):
            response = docente_detail_view(request, usuario_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_value_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/docentes/1/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.UserService.actualizar", side_effect=ValueError("mal")):
            response = docente_detail_view(request, usuario_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Course restore, delete ──────────────────────────────────────────────────────


class TestCourseRestoreViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/courses/1/restore/")
        response = course_restore_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/courses/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.CourseService.restaurar", return_value={"mensaje": "restaurado"}):
            response = course_restore_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/courses/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.CourseService.restaurar", side_effect=PermissionError("no")):
            response = course_restore_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/courses/999/restore/")
        request.usuario = USUARIO
        with patch("core.views.CourseService.restaurar", side_effect=DocenteAsignacion.DoesNotExist):
            response = course_restore_view(request, asignacion_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCourseDeleteViews:

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/1/", {"gestion": 2027}, format="json")
        response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/1/", {"gestion": 2027}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CourseService.actualizar_asignacion", return_value={"id": 1, "gestion": 2027}):
            response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CourseService.actualizar_asignacion", side_effect=PermissionError("no")):
            response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/999/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CourseService.actualizar_asignacion", side_effect=DocenteAsignacion.DoesNotExist):
            response = course_delete_view(request, asignacion_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_value_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/courses/1/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.CourseService.actualizar_asignacion", side_effect=ValueError("mal")):
            response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/courses/1/")
        response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/courses/1/")
        request.usuario = USUARIO
        with patch("core.views.CourseService.eliminar", return_value=None):
            response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/courses/1/")
        request.usuario = USUARIO
        with patch("core.views.CourseService.eliminar", side_effect=PermissionError("no")):
            response = course_delete_view(request, asignacion_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/courses/999/")
        request.usuario = USUARIO
        with patch("core.views.CourseService.eliminar", side_effect=DocenteAsignacion.DoesNotExist):
            response = course_delete_view(request, asignacion_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── Actividad restore, delete, detail ───────────────────────────────────────────


class TestActividadRestoreViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/1/restore/")
        response = actividad_restore_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.restaurar_actividad", return_value={"mensaje": "restaurado"}):
            response = actividad_restore_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/1/restore/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.restaurar_actividad", side_effect=PermissionError("no")):
            response = actividad_restore_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/actividades/999/restore/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.restaurar_actividad", side_effect=Actividades.DoesNotExist):
            response = actividad_restore_view(request, actividad_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestActividadDeleteViews:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.eliminar_actividad", return_value=None):
            response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/1/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.eliminar_actividad", side_effect=PermissionError("no")):
            response = actividad_delete_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/actividades/999/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.eliminar_actividad", side_effect=Actividades.DoesNotExist):
            response = actividad_delete_view(request, actividad_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestActividadDetailViews:

    def test_get_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/1/detail/")
        response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/1/detail/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.obtener_actividad", return_value={"id": 1, "nombre": "Examen"}):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_get_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/1/detail/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.obtener_actividad", side_effect=PermissionError("no")):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/actividades/999/detail/")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.obtener_actividad", side_effect=Actividades.DoesNotExist):
            response = actividad_detail_view(request, actividad_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/actividades/1/detail/", {"nombre": "Examen 2"}, format="json")
        response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/actividades/1/detail/", {"nombre": "Examen 2"}, format="json")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.actualizar_actividad", return_value={"id": 1, "nombre": "Examen 2"}):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/actividades/1/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.actualizar_actividad", side_effect=PermissionError("no")):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_not_found(self):
        factory = APIRequestFactory()
        request = factory.put("/api/actividades/999/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.actualizar_actividad", side_effect=Actividades.DoesNotExist):
            response = actividad_detail_view(request, actividad_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_value_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/actividades/1/detail/", {}, format="json")
        request.usuario = USUARIO
        with patch("core.views.ActivityService.actualizar_actividad", side_effect=ValueError("mal")):
            response = actividad_detail_view(request, actividad_id=1)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
