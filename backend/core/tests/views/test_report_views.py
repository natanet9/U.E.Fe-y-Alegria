from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import reports_view, reports_download_view


class TestReportViews:

    def test_reports_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/reports/")
        response = reports_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_download_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/reports/download/")
        response = reports_download_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
