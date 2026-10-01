import pytest
from unittest.mock import patch
from django.contrib.auth.hashers import make_password

from core.models import (
    Areas, Cursos, DocenteAsignacion, Docentes, Estudiantes, Grados, Inscripciones,
    Niveles, Paralelos, Periodos, Roles, Usuarios, Tutores, EstudianteTutor,
)
from core.services.dashboard_service import DashboardService


@pytest.mark.django_db
class TestDashboardService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'),
            Roles(nombre='docente'), Roles(nombre='regente'),
            Roles(nombre='tutor'),
        ])}
        users = {}
        for name, r in roles.items():
            ci = '12345678' if name == 'tutor' else None
            users[name] = Usuarios.objects.create(
                ci=ci,
                nombre=name.title(), email=f'{name}@test.com',
                password_hash=make_password('123456'), rol=r,
            )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Ciencias')
        docente_model = Docentes.objects.create(usuario=users['docente'])
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026, estado='activo')
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31',
            estado='activo',
        )
        # Crear tutor y relacionarlo con el estudiante
        tutor = Tutores.objects.create(
            ci='12345678', nombres='Tutor', primer_apellido='Test'
        )
        EstudianteTutor.objects.create(
            estudiante=estudiante, tutor=tutor, activo=True
        )
        return {'users': users, 'da': da, 'periodo': periodo, 'estudiante': estudiante}

    def test_dashboard_director(self, setup):
        dash = DashboardService().build_dashboard(setup['users']['director'])
        assert 'stats' in dash
        assert 'periodo_activo' in dash
        assert dash['periodo_activo']['nombre'] == 'T1'
        assert dash['stats']['total_estudiantes'] == 1

    def test_dashboard_secretaria(self, setup):
        dash = DashboardService().build_dashboard(setup['users']['secretaria'])
        assert 'stats' in dash
        assert 'docentes_sin_cierre' in dash

    @patch('core.services.dashboard_service.connection')
    def test_dashboard_docente(self, mock_conn, setup, dummy_cursor):
        # Patch the module's connection object (not the global cursor method)
        # and provide a dummy cursor instance so ORM queries are unaffected.
        mock_conn.cursor.return_value.__enter__.return_value = dummy_cursor
        # dummy_cursor.fetchone() already returns (0,) and fetchmany returns []
        dash = DashboardService().build_dashboard(setup['users']['docente'])
        assert 'asignaciones' in dash
        assert dash['total_estudiantes'] == 1
        assert dash['periodo_activo'] is not None

    def test_dashboard_regente(self, setup):
        dash = DashboardService().build_dashboard(setup['users']['regente'])
        assert 'licencias_pendientes' in dash

    def test_dashboard_tutor(self, setup):
        dash = DashboardService().build_dashboard(setup['users']['tutor'])
        assert 'estudiantes' in dash
        assert dash['total_estudiantes'] == 1
        assert len(dash['estudiantes']) == 1
        assert dash['estudiantes'][0]['id'] == setup['estudiante'].id
        assert 'periodo_activo' in dash
