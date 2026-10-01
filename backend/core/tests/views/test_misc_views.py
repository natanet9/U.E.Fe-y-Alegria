from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import DocenteAsignacion, Licencias
from core.views import (
    health_view, course_detail_view, recompute_actividades_view,
    attendance_view, attendance_admin_view, licencias_view, licencia_detail_view, cierre_view,
    reports_download_view, grades_update_view,
)

usuario_mock = SimpleNamespace(
    id=1, activo=True, nombre_completo="Admin",
    email="admin@test.com",
    rol=SimpleNamespace(nombre="secretaria"),
)


class TestMiscViews:

    # ── Health ────────────────────────────────────────────────────────────────

    def test_health(self):
        factory = APIRequestFactory()
        request = factory.get("/api/health/")
        response = health_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    # ── Course detail ─────────────────────────────────────────────────────────

    def test_course_detail_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/detail/")
        response = course_detail_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_course_detail_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/detail/?docente_asignacion_id=1&periodo_id=1")
        request.usuario = usuario_mock
        with patch("core.views.GradesService.get_course_detail", return_value={"nombre": "Matematicas"}):
            response = course_detail_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"nombre": "Matematicas"}

    def test_course_detail_permision(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/detail/?docente_asignacion_id=1")
        request.usuario = usuario_mock
        with patch("core.views.GradesService.get_course_detail", side_effect=PermissionError("Sin permiso")):
            response = course_detail_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_course_detail_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/detail/?docente_asignacion_id=999")
        request.usuario = usuario_mock
        with patch("core.views.GradesService.get_course_detail", side_effect=DocenteAsignacion.DoesNotExist):
            response = course_detail_view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ── Recompute ─────────────────────────────────────────────────────────────

    def test_recompute_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/grades/recompute/")
        response = recompute_actividades_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_recompute_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/grades/recompute/")
        request.usuario = usuario_mock
        response = recompute_actividades_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "mensaje" in response.data

    # ── Grades update ─────────────────────────────────────────────────────────

    def test_grades_update_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/grades/update/")
        response = grades_update_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_grades_update_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/grades/update/", {"nota": 10}, format="json")
        request.usuario = usuario_mock
        with patch("core.views.ActivityService.update_notas_directo", return_value={"actualizado": True}):
            response = grades_update_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"actualizado": True}

    def test_grades_update_validation(self):
        factory = APIRequestFactory()
        request = factory.post("/api/grades/update/", {"nota": 999}, format="json")
        request.usuario = usuario_mock
        with patch("core.views.ActivityService.update_notas_directo", side_effect=ValueError("Nota invalida")):
            response = grades_update_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ── Attendance ────────────────────────────────────────────────────────────

    def test_attendance_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/attendance/")
        response = attendance_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_attendance_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/attendance/?docente_asignacion_id=1")
        request.usuario = usuario_mock
        with patch("core.views.AttendanceService.listar_asistencias", return_value=[{"fecha": "2025-01-01"}]):
            response = attendance_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"asistencias": [{"fecha": "2025-01-01"}]}

    def test_attendance_create_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/attendance/", {
            "docente_asignacion_id": 1, "fecha": "2025-01-01", "estados": {"1": "A"},
        }, format="json")
        request.usuario = usuario_mock
        with patch("core.views.AttendanceService.marcar_asistencias", return_value=None):
            response = attendance_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_permision(self):
        factory = APIRequestFactory()
        request = factory.post("/api/attendance/", {
            "docente_asignacion_id": 1, "fecha": "2025-01-01", "estados": {"1": "A"},
        }, format="json")
        request.usuario = usuario_mock
        with patch("core.views.AttendanceService.marcar_asistencias", side_effect=PermissionError("Sin permiso")):
            response = attendance_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_attendance_admin_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/attendance/admin/")
        request.usuario = usuario_mock
        with patch("core.views.AttendanceService.listar_asistencias_admin", return_value=[{"docente_asignacion_id": 1}]):
            response = attendance_admin_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"asistencias": [{"docente_asignacion_id": 1}]}

    # ── Licencias ─────────────────────────────────────────────────────────────

    def test_licencias_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/licencias/")
        response = licencias_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_licencias_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/licencias/")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.listar", return_value=[{"id": 1}]):
            response = licencias_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"licencias": [{"id": 1}]}

    def test_licencias_create_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/licencias/", {"motivo": "Enfermedad"}, format="json")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.crear", return_value={"id": 1, "motivo": "Enfermedad"}):
            response = licencias_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == 1

    def test_licencias_create_permision(self):
        factory = APIRequestFactory()
        request = factory.post("/api/licencias/", {"motivo": "Enfermedad"}, format="json")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.crear", side_effect=PermissionError("Sin permiso")):
            response = licencias_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_licencias_approve_success(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/licencias/", {"licencia_id": 1, "aceptar": True}, format="json")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.aprobar", return_value={"id": 1, "estado": "aprobada"}):
            response = licencias_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_licencias_approve_no_id(self):
        factory = APIRequestFactory()
        request = factory.patch("/api/licencias/", {"aceptar": True}, format="json")
        request.usuario = usuario_mock
        response = licencias_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_licencia_detail_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/licencias/1/")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.obtener", return_value={"id": 1, "estado": "pendiente"}):
            response = licencia_detail_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

    def test_licencia_detail_error_paths(self):
        factory = APIRequestFactory()

        request = factory.get("/api/licencias/1/")
        response = licencia_detail_view(request, 1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        request.usuario = usuario_mock
        with patch("core.views.LicenseService.obtener", side_effect=Licencias.DoesNotExist):
            response = licencia_detail_view(request, 1)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_licencia_detail_update_and_delete(self):
        factory = APIRequestFactory()

        request = factory.put("/api/licencias/1/", {"motivo": "Cambio"}, format="json")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.actualizar", return_value={"id": 1, "mensaje": "Licencia actualizada exitosamente"}):
            response = licencia_detail_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

        request = factory.delete("/api/licencias/1/")
        request.usuario = usuario_mock
        with patch("core.views.LicenseService.eliminar", return_value={"mensaje": "Licencia eliminada"}):
            response = licencia_detail_view(request, 1)
        assert response.status_code == status.HTTP_200_OK

    # ── Cierre ────────────────────────────────────────────────────────────────

    def test_cierre_list_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/cierre/")
        response = cierre_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cierre_list_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/cierre/")
        request.usuario = usuario_mock
        with patch("core.views.CierreService.listar_cierres", return_value=[{"id": 1}]):
            response = cierre_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"cierres": [{"id": 1}]}

    def test_cierre_create_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/cierre/", {
            "accion": "cerrar", "docente_asignacion_id": 1, "periodo_id": 1,
        }, format="json")
        request.usuario = usuario_mock
        with patch("core.views.CierreService.cerrar_docente", return_value={"mensaje": "Cerrado"}):
            response = cierre_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"mensaje": "Cerrado"}

    # ── Reports download ──────────────────────────────────────────────────────

    def test_reports_download_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/reports/download/")
        response = reports_download_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reports_download_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/reports/download/?docente_asignacion_id=1&periodo_id=1")
        request.usuario = usuario_mock
        buf = BytesIO(b"fake excel content")
        with patch("core.views.ReportsService.export_notas_excel", return_value=buf):
            response = reports_download_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
