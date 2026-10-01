from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import grades_view


class TestGradeViews:

    def test_list_grades_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/grades/")
        response = grades_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_grades_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/grades/?docente_asignacion_id=1&periodo_id=1")
        request.usuario = SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com")
        tot = {1: 10.0}
        dim = {1: {'SER': 5.0}}
        with patch("core.views.GradesService.get_notas_totales", return_value=tot), \
             patch("core.views.GradesService.get_notas_por_dimension", return_value=dim):
            response = grades_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"totales": tot, "por_dimension": dim}
