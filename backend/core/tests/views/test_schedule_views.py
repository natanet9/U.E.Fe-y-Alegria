from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import schedules_view


class TestScheduleViews:

    def test_list_schedules_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/schedules/")
        response = schedules_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_schedules_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/schedules/")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        payload = []
        with patch("core.views.ScheduleService.listar_horarios", return_value=payload):
            response = schedules_view(request)
        assert response.status_code == status.HTTP_200_OK
