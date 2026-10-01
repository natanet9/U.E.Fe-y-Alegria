import pytest
from django.contrib.auth.hashers import make_password

from core.models import Periodos, Roles, Usuarios
from core.services.periodo_service import PeriodoService


@pytest.mark.django_db
class TestPeriodoService:

    @pytest.fixture
    def users(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        return {
            'director': Usuarios.objects.create(
                nombre='Director', email='dir@test.com',
                password_hash=make_password('123456'), rol=roles['director'],
            ),
            'secretaria': Usuarios.objects.create(
                nombre='Secretaria', email='sec@test.com',
                password_hash=make_password('123456'), rol=roles['secretaria'],
            ),
            'docente': Usuarios.objects.create(
                nombre='Docente', email='doc@test.com',
                password_hash=make_password('123456'), rol=roles['docente'],
            ),
        }

    def test_crear_periodo(self, users):
        p = PeriodoService().crear(users['director'], {
            'nombre': 'Test Periodo', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        assert p['nombre'] == 'Test Periodo'
        assert p['estado'] == 'pendiente'

    def test_crear_periodo_permision(self, users):
        with pytest.raises(PermissionError):
            PeriodoService().crear(users['secretaria'], {
                'nombre': 'Test', 'gestion': 2026, 'numero': 1,
                'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
            })

    def test_habilitar_periodo(self, users):
        p = PeriodoService().crear(users['director'], {
            'nombre': 'Test', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        result = PeriodoService().habilitar(users['director'], p['id'])
        assert result['estado'] == 'activo'

    def test_habilitar_docente_fails(self, users):
        p = PeriodoService().crear(users['director'], {
            'nombre': 'Test', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        with pytest.raises(PermissionError):
            PeriodoService().habilitar(users['docente'], p['id'])

    def test_cerrar_periodo(self, users):
        p = PeriodoService().crear(users['director'], {
            'nombre': 'Test', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        PeriodoService().habilitar(users['director'], p['id'])
        result = PeriodoService().cerrar(users['director'], p['id'])
        assert result['estado'] == 'cerrado'

    def test_cerrar_docente_fails(self, users):
        p = PeriodoService().crear(users['director'], {
            'nombre': 'Test', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        with pytest.raises(PermissionError):
            PeriodoService().cerrar(users['docente'], p['id'])

    def test_listar_periodos(self, users):
        PeriodoService().crear(users['director'], {
            'nombre': 'P1', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        PeriodoService().crear(users['director'], {
            'nombre': 'P2', 'gestion': 2026, 'numero': 2,
            'fecha_inicio': '2026-04-01', 'fecha_fin': '2026-06-30',
        })
        lista = PeriodoService().listar(users['director'], gestion=2026)
        assert len(lista) == 2

    def test_get_periodo_activo(self, users):
        p = PeriodoService().crear(users['director'], {
            'nombre': 'Activo', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        PeriodoService().habilitar(users['director'], p['id'])
        activo = PeriodoService().get_periodo_activo()
        assert activo is not None
        assert activo.estado == 'activo'

    def test_obtener_actualizar_y_eliminar_periodo(self, users):
        periodo = PeriodoService().crear(users['director'], {
            'nombre': 'Editable', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })

        obtenido = PeriodoService().obtener(users['director'], periodo['id'])
        assert obtenido['nombre'] == 'Editable'

        actualizado = PeriodoService().actualizar(users['director'], periodo['id'], {
            'nombre': 'Actualizado',
            'gestion': 2027,
        })
        assert actualizado['nombre'] == 'Actualizado'
        assert actualizado['gestion'] == 2027

        eliminado = PeriodoService().eliminar(users['director'], periodo['id'])
        assert eliminado['mensaje'] == 'Periodo eliminado'

    def test_obtener_periodo_permiso(self, users):
        periodo = PeriodoService().crear(users['director'], {
            'nombre': 'Editable', 'gestion': 2026, 'numero': 1,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-03-31',
        })
        with pytest.raises(PermissionError):
            PeriodoService().obtener(users['docente'], periodo['id'])
