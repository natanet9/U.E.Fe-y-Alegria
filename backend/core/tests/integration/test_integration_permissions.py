from datetime import date
import pytest
from rest_framework.test import APIRequestFactory

from core.models import (
    Roles, Usuarios, Niveles, Grados, Paralelos, Cursos,
    Areas, Periodos, DimensionesEvaluacion, DocenteAsignacion, Docentes,
    Estudiantes, Inscripciones,
)

from core.views import students_view, actividades_view, actividades_notas_view


@pytest.mark.django_db
def test_secretaria_can_create_student_and_docente_cannot():
    # Setup roles and users
    Roles.objects.bulk_create([Roles(nombre='secretaria'), Roles(nombre='docente')])
    secretaria_role = Roles.objects.get(nombre='secretaria')
    docente_role = Roles.objects.get(nombre='docente')

    secretaria = Usuarios.objects.create(nombre='Sec', email='sec@test.com', rol=secretaria_role, activo=True)
    docente = Usuarios.objects.create(nombre='Doc', email='doc@test.com', rol=docente_role, activo=True)

    factory = APIRequestFactory()

    # Secretaria creates student (valid data)
    req = factory.post('/api/students/', {
        'rude': 'RUD100', 'ci': '55555555', 'nombres': 'Pedro', 'primer_apellido': 'Gomez'
    }, format='json')
    req.usuario = secretaria
    resp = students_view(req)
    assert resp.status_code == 201

    # Docente attempts to create student -> forbidden
    req2 = factory.post('/api/students/', {
        'rude': 'RUD101', 'ci': '66666666', 'nombres': 'Luis', 'primer_apellido': 'Perez'
    }, format='json')
    req2.usuario = docente
    resp2 = students_view(req2)
    assert resp2.status_code == 403


@pytest.mark.django_db
def test_docente_can_create_activity_and_only_assigned_docente_can_save_notes():
    # Setup roles, users, course, assignment, student
    Roles.objects.get_or_create(nombre='docente')
    Roles.objects.get_or_create(nombre='secretaria')
    docente_role = Roles.objects.get(nombre='docente')
    secretaria_role = Roles.objects.get(nombre='secretaria')

    docente = Usuarios.objects.create(nombre='Doc', email='doc2@test.com', rol=docente_role, activo=True)
    otra_docente = Usuarios.objects.create(nombre='Otro', email='otro@test.com', rol=docente_role, activo=True)
    secretaria = Usuarios.objects.create(nombre='Sec', email='sec2@test.com', rol=secretaria_role, activo=True)

    nivel = Niveles.objects.create(nombre='Primaria')
    grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
    paralelo = Paralelos.objects.create(nombre='A')
    curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
    area = Areas.objects.create(nombre='Ciencias')
    periodo = Periodos.objects.create(nombre='P1', gestion=2026, numero=1, fecha_inicio='2026-01-01', fecha_fin='2026-06-01', estado='activo')
    dim = DimensionesEvaluacion.objects.create(nombre='SABER', orden=1, gestion=2026)

    docente_model = Docentes.objects.create(usuario=docente)
    da = DocenteAsignacion.objects.create(docente=docente_model, curso=curso, area=area, gestion=2026, activo=True)

    # Create a student and inscripcion
    estudiante = Estudiantes.objects.create(rude='R900', ci='77777777', nombres='Alma', primer_apellido='Flores')
    Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026, estado='activo')

    factory = APIRequestFactory()

    # Docente creates actividad via view
    req = factory.post('/api/actividades/', {
        'docente_asignacion_id': da.id,
        'nombre': 'Prueba', 'dimension_id': dim.id,
        'periodo_id': periodo.id, 'fecha_actividad': date.today().isoformat(), 'puntaje_maximo': 100,
    }, format='json')
    req.usuario = docente
    resp = actividades_view(req)
    assert resp.status_code == 201
    actividad_id = resp.data['actividad']['id']

    # Assigned docente saves notas -> OK
    notas_payload = {'actividad_id': actividad_id, 'notas': {str(estudiante.id): 88}}
    req2 = factory.post('/api/actividades/notas/', notas_payload, format='json')
    req2.usuario = docente
    resp2 = actividades_notas_view(req2)
    assert resp2.status_code == 200

    # Otro docente (no asignado) intenta guardar notas -> forbidden
    req3 = factory.post('/api/actividades/notas/', notas_payload, format='json')
    req3.usuario = otra_docente
    resp3 = actividades_notas_view(req3)
    assert resp3.status_code == 403
