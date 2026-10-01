from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password

from core.models import (
    Areas, Cursos, DocenteAsignacion, Docentes, Grados, Niveles, Paralelos,
    Periodos, PeriodoCierreDocente, Roles, Usuarios,
)
from core.services.cierre_service import CierreService
from core.services.audit_service import AuditService


@pytest.mark.django_db
class TestCierreService:

    @pytest.fixture(autouse=True)
    def mock_audit(self):
        with patch.object(AuditService, 'record', return_value=None):
            yield

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        director = Usuarios.objects.create(
            nombre='Director', email='dir@test.com',
            password_hash=make_password('123456'), rol=roles['director'],
        )
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'],
        )
        docente = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash=make_password('123456'), rol=roles['docente'],
        )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Musica')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31',
        )
        return {'director': director, 'secretaria': secretaria,
                'docente': docente, 'da': da, 'periodo': periodo}

    def test_cerrar_docente(self, setup):
        result = CierreService().cerrar_docente(
            setup['director'], setup['da'].id, setup['periodo'].id,
        )
        assert result['mensaje'] == 'Periodo cerrado exitosamente para el docente'

    def test_cerrar_ya_cerrado(self, setup):
        CierreService().cerrar_docente(
            setup['director'], setup['da'].id, setup['periodo'].id,
        )
        result = CierreService().cerrar_docente(
            setup['director'], setup['da'].id, setup['periodo'].id,
        )
        assert 'ya estaba cerrado' in result['mensaje']

    def test_cerrar_permision(self, setup):
        otro_docente = Usuarios.objects.create(
            nombre='Otro', email='otro@test.com',
            password_hash=make_password('123456'), rol=setup['docente'].rol,
        )
        with pytest.raises(PermissionError):
            CierreService().cerrar_docente(
                otro_docente, setup['da'].id, setup['periodo'].id,
            )

    def test_reabrir_docente(self, setup):
        cierre = PeriodoCierreDocente.objects.create(
            periodo=setup['periodo'],
            docente_asignacion=setup['da'],
            cerrado_por=setup['secretaria'],
        )
        result = CierreService().reabrir_docente(
            setup['director'], setup['da'].id, setup['periodo'].id,
        )
        assert result['mensaje'] == 'Periodo reabierto exitosamente'

    def test_reabrir_permision(self, setup):
        cierre = PeriodoCierreDocente.objects.create(
            periodo=setup['periodo'],
            docente_asignacion=setup['da'],
            cerrado_por=setup['secretaria'],
        )
        with pytest.raises(PermissionError):
            CierreService().reabrir_docente(
                setup['docente'], setup['da'].id, setup['periodo'].id,
            )

    def test_listar_cierres(self, setup):
        CierreService().cerrar_docente(
            setup['director'], setup['da'].id, setup['periodo'].id,
        )
        result = CierreService().listar_cierres(
            setup['director'],
        )
        assert len(result) == 1
        assert result[0]['area'] == 'Musica'
