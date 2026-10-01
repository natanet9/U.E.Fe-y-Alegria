from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import dashboard_view


class TestDashboardViews:

    def test_dashboard_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/")
        response = dashboard_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_returns_payload(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/")
        request.usuario = SimpleNamespace(id=1, nombre_completo="Admin", email="admin@test.com", activo=True)
        payload = {"stats": {}, "periodo_activo": None}
        with patch("core.views.DashboardService.build_dashboard", return_value=payload):
            response = dashboard_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload

    def test_dashboard_force_refresh_flag(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/?force=1")
        request.usuario = SimpleNamespace(id=1, nombre_completo="Admin", email="admin@test.com", activo=True)
        payload = {"stats": {}, "periodo_activo": None}
        with patch("core.views.DashboardService.build_dashboard", return_value=payload) as mock_build:
            response = dashboard_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload
        mock_build.assert_called_once()
        assert mock_build.call_args.kwargs.get("force_refresh") is True
