from datetime import date

import pytest
from django.contrib.auth.hashers import make_password

from core.models import (
    Actividades, ActividadNotas, Areas, Cursos, DimensionesEvaluacion,
    DocenteAsignacion, Docentes, Estudiantes, Grados, Inscripciones, Niveles,
    Paralelos, Periodos, Roles, Usuarios,
)
from core.services.activity_service import ActivityService


@pytest.mark.django_db
class TestActivityService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        director = Usuarios.objects.create(
            nombre='Director', email='dir@test.com',
            password_hash=make_password('123456'), rol=roles['director'],
        )
        docente = Usuarios.objects.create(
            nombre='Docente', email='doc@test.com',
            password_hash=make_password('123456'), rol=roles['docente'],
        )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematica')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        periodo = Periodos.objects.create(
            nombre='Trimestre 1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31', estado='activo',
        )
        dim = DimensionesEvaluacion.objects.create(nombre='SABER', orden=2, gestion=2026)
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {
            'director': director, 'docente': docente, 'da': da, 'periodo': periodo,
            'dimension': dim, 'estudiante': estudiante, 'curso': curso,
        }

    def test_crear_actividad(self, setup):
        data = {
            'docente_asignacion_id': setup['da'].id,
            'nombre': 'Examen 1', 'dimension_id': setup['dimension'].id,
            'periodo_id': setup['periodo'].id, 'fecha_actividad': date.today().isoformat(),
            'puntaje_maximo': 45,
        }
        result = ActivityService().crear_actividad(setup['docente'], data)
        assert result['nombre'] == 'Examen 1'
        assert float(result['puntaje_maximo']) == 45

    def test_crear_actividad_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro', email='otro@test.com',
            password_hash=make_password('123456'),
            rol=otro_rol,
        )
        data = {
            'docente_asignacion_id': setup['da'].id,
            'nombre': 'Examen', 'dimension_id': setup['dimension'].id,
            'periodo_id': setup['periodo'].id, 'fecha_actividad': date.today().isoformat(),
        }
        with pytest.raises(PermissionError):
            ActivityService().crear_actividad(otro, data)

    def test_crear_actividad_autoevaluacion_fails(self, setup):
        dim_auto = DimensionesEvaluacion.objects.create(nombre='AUTOEVALUACION', orden=1, gestion=2026)
        with pytest.raises(ValueError, match='autoevaluacion'):
            ActivityService().crear_actividad(setup['docente'], {
                'docente_asignacion_id': setup['da'].id,
                'nombre': 'Auto', 'dimension_id': dim_auto.id,
                'periodo_id': setup['periodo'].id, 'fecha_actividad': date.today().isoformat(),
            })

    def test_crear_actividad_validation(self, setup):
        with pytest.raises(ValueError, match='Campos requeridos faltantes'):
            ActivityService().crear_actividad(setup['docente'], {
                'docente_asignacion_id': setup['da'].id,
            })

    def test_eliminar_actividad(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        ActivityService().eliminar_actividad(setup['docente'], act.id)
        act.refresh_from_db()
        assert act.activo is False
        assert Actividades.objects.filter(id=act.id, activo=True).count() == 0

    def test_eliminar_actividad_permision(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro2', email='otro2@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            ActivityService().eliminar_actividad(otro, act.id)

    def test_obtener_y_actualizar_actividad(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        data = ActivityService().obtener_actividad(setup['docente'], act.id)
        assert data['nombre'] == 'Test'

        updated = ActivityService().actualizar_actividad(setup['docente'], act.id, {
            'nombre': 'Nuevo',
            'puntaje_maximo': 15,
        })
        assert updated['nombre'] == 'Nuevo'
        assert float(updated['puntaje_maximo']) == 15

    def test_actualizar_actividad_permision(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro5', email='otro5@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            ActivityService().actualizar_actividad(otro, act.id, {'nombre': 'X'})

    def test_guardar_notas_actividad(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        ActivityService().guardar_notas_actividad(
            setup['docente'], act.id,
            {str(setup['estudiante'].id): 8.5},
        )
        an = ActividadNotas.objects.get(actividad=act, estudiante=setup['estudiante'])
        assert float(an.valor) == 8.5

    def test_guardar_notas_permision(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro3', email='otro3@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            ActivityService().guardar_notas_actividad(otro, act.id, {})

    def test_get_notas_estudiante(self, setup):
        act = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Test',
            puntaje_maximo=10, fecha_actividad=date.today().isoformat(),
        )
        ActividadNotas.objects.create(
            actividad=act, estudiante=setup['estudiante'], valor=7.5,
        )
        result = ActivityService().get_notas_estudiante(
            setup['docente'], setup['da'].id, setup['estudiante'].id,
        )
        assert str(act.id) in result
        assert float(result[str(act.id)]) == 7.5

    def test_get_notas_estudiante_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro4', email='otro4@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            ActivityService().get_notas_estudiante(otro, setup['da'].id, 1)

    def test_update_notas_directo(self, setup):
        estudiante_2 = Estudiantes.objects.create(
            rude='RUD002', ci='87654321', nombres='Maria',
            primer_apellido='Lopez',
        )
        Inscripciones.objects.create(estudiante=estudiante_2, curso=setup['curso'], gestion=2026)

        act_1 = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Act1',
            puntaje_maximo=100, fecha_actividad=date.today().isoformat(),
        )
        act_2 = Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Act2',
            puntaje_maximo=100, fecha_actividad=date.today().isoformat(),
        )
        result = ActivityService().update_notas_directo(setup['docente'], {
            'docente_asignacion_id': setup['da'].id,
            'periodo_id': setup['periodo'].id,
            'notas': {str(setup['estudiante'].id): 85, str(estudiante_2.id): 90},
        })
        assert 'estudiantes' in result['mensaje']
        assert ActividadNotas.objects.filter(actividad__in=[act_1, act_2]).count() == 4
        assert float(ActividadNotas.objects.get(actividad=act_1, estudiante=setup['estudiante']).valor) == 85
        assert float(ActividadNotas.objects.get(actividad=act_2, estudiante=estudiante_2).valor) == 90

    def test_update_notas_directo_validation(self, setup):
        with pytest.raises(ValueError, match='Debe enviar'):
            ActivityService().update_notas_directo(setup['docente'], {})

    def test_list_actividades(self, setup):
        Actividades.objects.create(
            docente_asignacion=setup['da'], periodo=setup['periodo'],
            dimension=setup['dimension'], nombre='Act1',
            puntaje_maximo=100, fecha_actividad=date.today().isoformat(),
        )
        result = ActivityService()._list_actividades(setup['da'].id)
        assert len(result) == 1
        assert result[0]['nombre'] == 'Act1'
