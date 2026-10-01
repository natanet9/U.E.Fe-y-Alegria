from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import attendance_detail_view
from core.models import Asistencias


class TestAttendanceDetailView:

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/attendance/1/", {}, format="json")
        response = attendance_detail_view(request, asistencia_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/attendance/1/", {"estado": "ausente"}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.AttendanceService.actualizar_asistencia", return_value={"id": 1, "estado": "ausente"}):
            response = attendance_detail_view(request, asistencia_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/attendance/1/", {}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.AttendanceService.actualizar_asistencia", side_effect=PermissionError("no")):
            response = attendance_detail_view(request, asistencia_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_success(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/attendance/1/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.AttendanceService.eliminar_asistencia", return_value={"mensaje": "Asistencia eliminada"}):
            response = attendance_detail_view(request, asistencia_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_not_found(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/attendance/999/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.AttendanceService.eliminar_asistencia", side_effect=Asistencias.DoesNotExist):
            response = attendance_detail_view(request, asistencia_id=999)
        assert response.status_code == status.HTTP_404_NOT_FOUND
