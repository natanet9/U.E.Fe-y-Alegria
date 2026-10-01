import pytest
from django.contrib.auth.hashers import make_password
from unittest.mock import patch, MagicMock

from core.models import (
    Areas, Cursos, DocenteAsignacion, Docentes, Estudiantes, ExportEvent, Grados, Inscripciones,
    Niveles, Paralelos, Periodos, Roles, Usuarios,
)
from core.services.reports_service import ReportsService


@pytest.mark.django_db
class TestReportsService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'), Roles(nombre='tutor'),
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
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31',
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {
            'director': director, 'docente': docente, 'da': da,
            'periodo': periodo, 'estudiante': estudiante,
        }

    def test_export_permision(self, setup):
        # Use a user without export permissions (tutor) to assert PermissionError
        tutor = Usuarios.objects.create(
            nombre='Tutor', email='tutor@test.com',
            password_hash=make_password('123456'), rol=Roles.objects.get(nombre='tutor'),
        )
        with pytest.raises(PermissionError):
            ReportsService().export_notas_excel(
                tutor, setup['da'].id, setup['periodo'].id,
            )

    @patch('core.services.reports_service.connection')
    def test_export_excel(self, mock_conn, setup, dummy_cursor):
        mock_conn.cursor.return_value.__enter__.return_value = dummy_cursor
        buf = ReportsService().export_notas_excel(
            setup['docente'], setup['da'].id, setup['periodo'].id,
        )
        assert buf.getvalue()[:2] == b'PK'

    def test_export_history_lists_own_exports(self, setup):
        ExportEvent.objects.create(
            usuario=setup['docente'],
            periodo=setup['periodo'],
            docente_asignacion_id=setup['da'].id,
            formato='xlsx',
            filtros={'periodo_id': setup['periodo'].id},
        )

        result = ReportsService().get_export_history(setup['docente'], periodo_id=setup['periodo'].id)
        assert result['total'] == 1
        assert result['exports'][0]['formato'] == 'xlsx'
