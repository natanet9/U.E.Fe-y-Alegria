from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import report_card_view
from core.models import Estudiantes


class TestReportCardView:

    def test_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/report-card/?estudiante_id=1")
        response = report_card_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/report-card/?estudiante_id=1&gestion=2026")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ReportCardService.generar_boletin", return_value={"estudiante": {"id": 1}, "materias": []}):
            response = report_card_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_missing_estudiante_id(self):
        factory = APIRequestFactory()
        request = factory.get("/api/report-card/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        response = report_card_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_permission_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/report-card/?estudiante_id=1")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ReportCardService.generar_boletin", side_effect=PermissionError("no")):
            response = report_card_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/report-card/?estudiante_id=999")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ReportCardService.generar_boletin", side_effect=Estudiantes.DoesNotExist):
            response = report_card_view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_value_error(self):
        factory = APIRequestFactory()
        request = factory.get("/api/report-card/?estudiante_id=1")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ReportCardService.generar_boletin", side_effect=ValueError("sin inscripciones")):
            response = report_card_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
