from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import schedule_delete_view
from core.models import Horarios


class TestScheduleUpdateView:

    def test_put_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.put("/api/schedules/1/", {}, format="json")
        response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_put_success(self):
        factory = APIRequestFactory()
        request = factory.put("/api/schedules/1/", {"aula": "B2"}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ScheduleService.actualizar_horario", return_value={"id": 1, "mensaje": "Horario actualizado"}):
            response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_200_OK

    def test_put_permission_error(self):
        factory = APIRequestFactory()
        request = factory.put("/api/schedules/1/", {}, format="json")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        with patch("core.views.ScheduleService.actualizar_horario", side_effect=PermissionError("no")):
            response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.delete("/api/schedules/1/")
        response = schedule_delete_view(request, horario_id=1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
