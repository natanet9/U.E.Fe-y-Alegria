import pytest
from django.contrib.auth.hashers import make_password
from unittest.mock import patch

from core.models import (
    Areas, Cursos, DimensionConfigPeriodo, DimensionesEvaluacion, DocenteAsignacion, Docentes, Estudiantes, Grados,
    Inscripciones, Niveles, Paralelos, Periodos, Roles, Usuarios,
)
from core.services.grades_service import GradesService


@pytest.mark.django_db
class TestGradesService:

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
        dim_auto = DimensionesEvaluacion.objects.create(nombre='AUTOEVALUACION', orden=4, gestion=2026)
        DimensionConfigPeriodo.objects.create(periodo=periodo, dimension=dim_auto, puntaje_maximo=5)
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {
            'director': director, 'docente': docente, 'da': da, 'periodo': periodo,
            'estudiante': estudiante, 'curso': curso, 'dim_auto': dim_auto,
        }

    def test_get_course_detail(self, setup):
        with patch.object(GradesService, '_get_notas_dimension', return_value={}):
            result = GradesService().get_course_detail(
                setup['docente'], setup['da'].id,
            )
        assert result['curso']['area'] == 'Matematica'
        assert len(result['estudiantes']) == 1
        assert result['actividad_notas'] == {}
        auto = next(d for d in result['dimensiones'] if d['nombre'] == 'AUTOEVALUACION')
        assert auto['puntaje_maximo'] == 5.0

    def test_get_course_detail_with_periodo(self, setup):
        with patch.object(GradesService, '_get_notas_dimension', return_value={
            str(setup['estudiante'].id): {'1': 88.5},
        }):
            result = GradesService().get_course_detail(
                setup['docente'], setup['da'].id, periodo_id=setup['periodo'].id,
            )
        assert result['curso']['area'] == 'Matematica'
        assert len(result['estudiantes']) == 1
        assert result['notas_dimension'][str(setup['estudiante'].id)]['1'] == 88.5

    def test_get_course_detail_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro', email='otro@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            GradesService().get_course_detail(otro, setup['da'].id)

    def test_get_notas_totales(self, setup):
        fake_cursor = type('Cursor', (), {
            '__enter__': lambda self: self,
            '__exit__': lambda self, exc_type, exc, tb: False,
            'execute': lambda self, sql, params=None: None,
            'fetchall': lambda self: [(setup['estudiante'].id, setup['periodo'].id, 92.0, 3)],
        })()
        with patch('core.services.grades_service.connection.cursor', return_value=fake_cursor), \
             patch('core.services.grades_service.AccessControlService.puede_editar_notas', return_value=True):
            result = GradesService().get_notas_totales(
                setup['docente'], setup['da'].id, setup['periodo'].id,
            )
        assert result == [{
            'estudiante_id': setup['estudiante'].id,
            'periodo_id': setup['periodo'].id,
            'nota_total': 92.0,
            'dimensiones_evaluadas': 3,
        }]

    def test_get_notas_por_dimension(self, setup):
        fake_cursor = type('Cursor', (), {
            '__enter__': lambda self: self,
            '__exit__': lambda self, exc_type, exc, tb: False,
            'execute': lambda self, sql, params=None: None,
            'fetchall': lambda self: [(setup['estudiante'].id, 1, 88.5, 88.5, 100, 'SABER')],
        })()
        with patch('core.services.grades_service.connection.cursor', return_value=fake_cursor), \
             patch('core.services.grades_service.AccessControlService.puede_editar_notas', return_value=True):
            result = GradesService().get_notas_por_dimension(
                setup['docente'], setup['da'].id, setup['periodo'].id,
            )
        assert result == [{
            'estudiante_id': setup['estudiante'].id,
            'dimension_id': 1,
            'nota': 88.5,
            'promedio': 88.5,
            'puntaje_maximo': 100.0,
            'dimension_nombre': 'SABER',
        }]
