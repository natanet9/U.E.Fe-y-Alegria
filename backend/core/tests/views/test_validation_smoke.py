from unittest.mock import patch
from rest_framework.test import APIRequestFactory

from core.views import (
    students_view,
    docentes_view,
    actividades_view,
    actividades_notas_view,
    schedules_view,
    reports_download_view,
)


factory = APIRequestFactory()


def fake_usuario():
    class U:
        id = 1
        nombre_completo = 'Test'

    u = U()
    class R:
        nombre = 'secretaria'

    u.rol = R()
    return u


def test_students_post_missing_fields_returns_400():
    req = factory.post('/api/students/', {}, format='json')
    req.usuario = fake_usuario()
    resp = students_view(req)
    assert resp.status_code == 400


def test_docentes_post_missing_fields_returns_400():
    req = factory.post('/api/docentes/', {}, format='json')
    req.usuario = fake_usuario()
    resp = docentes_view(req)
    assert resp.status_code == 400


def test_actividades_post_missing_fields_returns_400():
    req = factory.post('/api/actividades/', {}, format='json')
    req.usuario = fake_usuario()
    with patch('core.views.AccessControlService.puede_editar_notas_libremente', return_value=True):
        resp = actividades_view(req)
    assert resp.status_code == 400


def test_actividades_notas_missing_fields_returns_400():
    req = factory.post('/api/actividades/notas/', {}, format='json')
    req.usuario = fake_usuario()
    resp = actividades_notas_view(req)
    assert resp.status_code == 400


def test_schedules_post_missing_fields_returns_400():
    req = factory.post('/api/schedules/', {}, format='json')
    req.usuario = fake_usuario()
    resp = schedules_view(req)
    assert resp.status_code == 400 or resp.status_code == 403


def test_reports_download_missing_params_returns_400():
    req = factory.get('/api/reports/download', {}, format='json')
    req.usuario = fake_usuario()
    resp = reports_download_view(req)
    assert resp.status_code == 400
