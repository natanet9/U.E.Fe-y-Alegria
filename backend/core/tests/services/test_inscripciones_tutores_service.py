import pytest

from core.services.inscripciones_service import InscripcionesService
from core.services.tutores_service import TutoresService
from core.models import (
    Roles,
    Usuarios,
    Niveles,
    Grados,
    Paralelos,
    Cursos,
    Estudiantes,
    Inscripciones,
    Tutores,
)


@pytest.mark.django_db
def test_inscripciones_list_obtener_y_actualizar_estado():
    rol_dir = Roles.objects.create(nombre='director')
    rol_sec = Roles.objects.create(nombre='secretaria')
    diru = Usuarios.objects.create(nombre='D', email='d@x.com', password_hash='x', rol=rol_dir)
    sec = Usuarios.objects.create(nombre='S', email='s@x.com', password_hash='x', rol=rol_sec)

    nivel = Niveles.objects.create(nombre='Primaria')
    grado = Grados.objects.create(nivel=nivel, nombre='3ro', numero=3)
    paralelo = Paralelos.objects.create(nombre='B')
    curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)

    est = Estudiantes.objects.create(rude='r1', ci='111', primer_apellido='A', nombres='Est')
    ins = Inscripciones.objects.create(estudiante=est, curso=curso, gestion=2026)

    svc = InscripcionesService()
    lst = svc.listar(diru)
    assert any(i['id'] == ins.id for i in lst)

    data = svc.obtener(diru, ins.id)
    assert data['estudiante_id'] == est.id

    # actualizar estado con permiso
    out = svc.actualizar_estado(sec, ins.id, 'retirado')
    assert out['estado'] == 'retirado'

    # invalid state
    with pytest.raises(ValueError):
        svc.actualizar_estado(sec, ins.id, 'noexiste')

    # no permission
    rol_doc = Roles.objects.create(nombre='docente')
    docu = Usuarios.objects.create(nombre='Doc', email='doc@x.com', password_hash='x', rol=rol_doc)
    with pytest.raises(PermissionError):
        svc.actualizar_estado(docu, ins.id, 'activo')


@pytest.mark.django_db
def test_tutores_crud_and_list():
    rol_sec = Roles.objects.create(nombre='secretaria')
    rol_dir = Roles.objects.create(nombre='director')
    sec = Usuarios.objects.create(nombre='S', email='s5@example.com', password_hash='x', rol=rol_sec)
    diru = Usuarios.objects.create(nombre='D5', email='d5@example.com', password_hash='x', rol=rol_dir)

    svc = TutoresService()
    out = svc.crear(sec, {'ci': '9999', 'nombres': 'Juan', 'primer_apellido': 'Perez'})
    tid = out['id']
    assert out['mensaje']

    t = svc.obtener(diru, tid)
    assert t['ci'] == '9999'

    # actualizar
    up = svc.actualizar(sec, tid, {'celular': '7777'})
    assert up['id'] == tid

    # eliminar
    msg = svc.eliminar(sec, tid)
    assert 'elimin' in msg['mensaje']

    # listar
    lst = svc.listar(diru)
    assert any(x['id'] == tid for x in lst)
