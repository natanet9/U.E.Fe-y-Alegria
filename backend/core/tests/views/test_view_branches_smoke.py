import pytest
from unittest.mock import patch

from rest_framework.test import APIRequestFactory

from core.views import (
    health_view,
    login_view,
    me_view,
    catalog_view,
    students_view,
)
from core.models import Usuarios, Roles


factory = APIRequestFactory()


def test_health_view():
    req = factory.get('/health')
    resp = health_view(req)
    assert resp.status_code == 200


def test_login_view_missing_data():
    req = factory.post('/login', {})
    resp = login_view(req)
    assert resp.status_code == 400


def test_me_view_unauthorized():
    req = factory.get('/me')
    resp = me_view(req)
    assert resp.status_code == 401


def test_catalog_view_unknown_model():
    # unauthenticated
    req = factory.get('/catalog/unknown')
    resp = catalog_view(req, 'unknown')
    assert resp.status_code == 401


@pytest.mark.django_db
def test_catalog_list_niveles_calls_service():
    r = Roles.objects.create(nombre='director')
    u = Usuarios.objects.create(nombre='D', email='d@x.com', password_hash='x', rol=r)
    req = factory.get('/catalog/niveles')
    req.usuario = u
    with patch('core.views.CatalogService') as MockCatalog:
        instance = MockCatalog.return_value
        instance.listar_niveles.return_value = [{'id': 1, 'nombre': 'Inicial'}]
        resp = catalog_view(req, 'niveles')
        assert resp.status_code == 200
        assert resp.data['data'][0]['nombre'] == 'Inicial'


@pytest.mark.django_db
def test_students_create_permission_denied():
    r = Roles.objects.create(nombre='docente')
    u = Usuarios.objects.create(nombre='Doc', email='doc@x.com', password_hash='x', rol=r)
    req = factory.post('/students', {'nombre': 'X'})
    req.usuario = u
    with patch('core.views.StudentsService') as MockSvc:
        MockSvc.return_value.crear.side_effect = PermissionError('No autorizado')
        resp = students_view(req)
        assert resp.status_code == 403
