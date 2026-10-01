import pytest
from django.contrib.auth.hashers import make_password

from core.models import (
    Areas, Cursos, DocenteAsignacion, Grados, Niveles, Paralelos,
    Roles, Usuarios,
)
from core.services.user_service import UserService


@pytest.mark.django_db
class TestUserService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'],
        )
        director = Usuarios.objects.create(
            nombre='Dir', email='dir@test.com',
            password_hash=make_password('123456'), rol=roles['director'],
        )
        return {'secretaria': secretaria, 'director': director, 'roles': roles}

    def test_listar_usuarios(self, setup):
        result = UserService().listar(setup['secretaria'])
        assert result['total'] >= 2

    def test_listar_usuarios_permision(self, setup):
        result = UserService().listar(setup['director'])
        assert result['total'] >= 2  # director tiene permiso

    def test_listar_usuarios_with_filters(self, setup):
        service = UserService()
        service.crear(setup['secretaria'], {
            'email': 'activo@test.com',
            'nombre': 'Activo Usuario',
            'rol': 'docente',
        })
        inactivo = service.crear(setup['secretaria'], {
            'email': 'inactivo@test.com',
            'nombre': 'Inactivo Usuario',
            'rol': 'docente',
        })
        service.eliminar(setup['secretaria'], inactivo['id'])

        filtrados = service.listar(setup['secretaria'], query='Activo', rol='docente')
        assert filtrados['total'] >= 1
        assert all(item['rol'] == 'docente' for item in filtrados['usuarios'])

        con_inactivos = service.listar(setup['secretaria'], incluir_inactivos=True)
        assert con_inactivos['total'] >= 3

    def test_crear_usuario(self, setup):
        u = UserService().crear(setup['secretaria'], {
            'email': 'nuevo@test.com',
            'nombre': 'Nuevo Usuario',
            'rol': 'docente',
        })
        assert u['email'] == 'nuevo@test.com'
        assert u['rol'] == 'docente'

    def test_crear_usuario_permision(self, setup):
        result = UserService().crear(setup['director'], {
            'email': 'x@test.com', 'nombre': 'X', 'rol': 'docente',
        })
        assert result['email'] == 'x@test.com'

    def test_crear_usuario_validation(self, setup):
        with pytest.raises(ValueError, match='Campos requeridos faltantes'):
            UserService().crear(setup['secretaria'], {'email': 'x@test.com'})

        with pytest.raises(ValueError, match='Email no tiene un formato valido'):
            UserService().crear(setup['secretaria'], {
                'email': 'bad-email', 'nombre': 'X', 'rol': 'docente',
            })

        with pytest.raises(ValueError, match='CI debe contener solo digitos'):
            UserService().crear(setup['secretaria'], {
                'email': 'ok@test.com', 'nombre': 'X', 'rol': 'docente', 'ci': 'abc',
            })

        with pytest.raises(Roles.DoesNotExist):
            UserService().crear(setup['secretaria'], {
                'email': 'ok2@test.com', 'nombre': 'X', 'rol': 'inexistente',
            })

    def test_actualizar_usuario(self, setup):
        u = UserService().crear(setup['secretaria'], {
            'email': 'act@test.com', 'nombre': 'Original', 'rol': 'docente',
        })
        updated = UserService().actualizar(setup['secretaria'], u['id'], {
            'nombre': 'Actualizado',
            'activo': False,
            'password': 'nueva123',
        })
        assert updated['nombre'] == 'Actualizado'
        assert updated['activo'] is False

    def test_eliminar_restaurar_usuario(self, setup):
        u = UserService().crear(setup['secretaria'], {
            'email': 'del@test.com', 'nombre': 'Borrar', 'rol': 'docente',
        })
        service = UserService()
        service.eliminar(setup['secretaria'], u['id'])
        assert service.obtener(setup['secretaria'], u['id'])['activo'] is False

        restored = service.restaurar(setup['secretaria'], u['id'])
        assert restored['activo'] is True

    def test_listar_page_bounds(self, setup):
        result = UserService().listar(setup['secretaria'], page=99, page_size=1)
        assert result['page'] >= 1
        assert result['page_size'] == 1

    def test_obtener_usuario(self, setup):
        result = UserService().obtener(setup['secretaria'], setup['secretaria'].id)
        assert result['email'] == 'sec@test.com'

    def test_obtener_usuario_permision(self, setup):
        result = UserService().obtener(setup['director'], setup['director'].id)
        assert result['email'] == 'dir@test.com'
