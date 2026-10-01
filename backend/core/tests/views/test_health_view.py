from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import health_view


class TestHealthView:

    def test_health_returns_ok(self):
        factory = APIRequestFactory()
        request = factory.get("/api/health/")
        mock_cursor = __import__('unittest').mock.MagicMock()
        with patch('core.views.connection.cursor') as mock_conn:
            mock_conn.return_value.__enter__.return_value = mock_cursor
            with patch('core.views.MigrationExecutor') as mock_exec:
                mock_exec.return_value.migration_plan.return_value = []
                response = health_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'
        assert 'database' in response.data
        assert 'duration_ms' in response.data

    def test_health_db_down(self):
        factory = APIRequestFactory()
        request = factory.get("/api/health/")
        from django.db.utils import OperationalError
        with patch('core.views.connection.cursor', side_effect=OperationalError("no db")):
            response = health_view(request)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['status'] == 'degraded'
