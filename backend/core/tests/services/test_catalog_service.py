import pytest

from core.services.catalog_service import CatalogService
from core.models import (
    Roles,
    Usuarios,
    Niveles,
    Grados,
    Paralelos,
    Cursos,
    DimensionesEvaluacion,
    Areas,
)


@pytest.mark.django_db
def test_listar_niveles_permitido():
    rol = Roles.objects.create(nombre='director')
    user = Usuarios.objects.create(nombre='D', email='d@example.com', password_hash='x', rol=rol)
    Niveles.objects.create(nombre='Inicial')
    Niveles.objects.create(nombre='Primaria')

    svc = CatalogService()
    res = svc.listar_niveles(user)
    assert isinstance(res, list)
    assert any(r['nombre'] == 'Inicial' for r in res)


@pytest.mark.django_db
def test_listar_niveles_no_permitido():
    rol = Roles.objects.create(nombre='docente')
    user = Usuarios.objects.create(nombre='Doc', email='doc@example.com', password_hash='x', rol=rol)
    svc = CatalogService()
    with pytest.raises(PermissionError):
        svc.listar_niveles(user)


@pytest.mark.django_db
def test_crear_y_eliminar_nivel_por_secretaria():
    rol = Roles.objects.create(nombre='secretaria')
    user = Usuarios.objects.create(nombre='S', email='s@example.com', password_hash='x', rol=rol)
    svc = CatalogService()

    out = svc.crear_nivel(user, {'nombre': 'Secundaria'})
    assert out['nombre'] == 'Secundaria'
    nid = out['id']

    # eliminar
    msg = svc.eliminar_nivel(user, nid)
    assert 'elimin' in msg['mensaje']


@pytest.mark.django_db
def test_grado_crud_and_list_by_nivel():
    rol_sec = Roles.objects.create(nombre='secretaria')
    rol_dir = Roles.objects.create(nombre='director')
    sec = Usuarios.objects.create(nombre='S', email='s2@example.com', password_hash='x', rol=rol_sec)
    diru = Usuarios.objects.create(nombre='D2', email='d2@example.com', password_hash='x', rol=rol_dir)

    nivel = Niveles.objects.create(nombre='Primaria')
    svc = CatalogService()

    # crear grado
    out = svc.crear_grado(sec, {'nombre': '1ro', 'numero': 1, 'nivel_id': nivel.id})
    assert out['nombre'] == '1ro'
    gid = out['id']

    # listar por nivel
    lst = svc.listar_grados(diru, nivel_id=nivel.id)
    assert any(g['id'] == gid for g in lst)

    # eliminar
    msg = svc.eliminar_grado(sec, gid)
    assert 'Grado' in msg['mensaje'] or 'elimin' in msg['mensaje']


@pytest.mark.django_db
def test_curso_crud_and_list():
    rol_sec = Roles.objects.create(nombre='secretaria')
    rol_dir = Roles.objects.create(nombre='director')
    sec = Usuarios.objects.create(nombre='S3', email='s3@example.com', password_hash='x', rol=rol_sec)
    diru = Usuarios.objects.create(nombre='D3', email='d3@example.com', password_hash='x', rol=rol_dir)

    nivel = Niveles.objects.create(nombre='Basica')
    grado = Grados.objects.create(nivel=nivel, nombre='2do', numero=2)
    paralelo = Paralelos.objects.create(nombre='A')

    svc = CatalogService()
    out = svc.crear_curso(sec, {'grado_id': grado.id, 'paralelo_id': paralelo.id, 'gestion': 2026})
    assert 'id' in out
    cid = out['id']

    lst = svc.listar_cursos(diru, grado_id=grado.id)
    assert any(c['id'] == cid for c in lst)

    msg = svc.eliminar_curso(sec, cid)
    assert 'Curso' in msg['mensaje'] or 'elimin' in msg['mensaje']


@pytest.mark.django_db
def test_areas_y_dimensiones_crud():
    rol_sec = Roles.objects.create(nombre='secretaria')
    rol_dir = Roles.objects.create(nombre='director')
    sec = Usuarios.objects.create(nombre='S4', email='s4@example.com', password_hash='x', rol=rol_sec)
    diru = Usuarios.objects.create(nombre='D4', email='d4@example.com', password_hash='x', rol=rol_dir)

    svc = CatalogService()
    a = svc.crear_area(sec, {'nombre': 'Matematica'})
    assert a['nombre'] == 'Matematica'
    d = svc.crear_dimension(diru, {'nombre': 'Comprension', 'orden': 1, 'gestion': 2026})
    assert d['orden'] == 1

    las = svc.listar_areas(diru)
    assert any(x['nombre'] == 'Matematica' for x in las)
    ldim = svc.listar_dimensiones(diru)
    assert any(x['nombre'] == 'Comprension' for x in ldim)
