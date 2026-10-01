import pytest

from core.models import Roles, Usuarios


@pytest.mark.django_db
class TestUsuarios:
    def test_create_usuario(self):
        rol = Roles.objects.create(nombre='director')
        u = Usuarios.objects.create(
            nombre='Test', primer_apellido='User',
            email='test@test.com',
            password_hash='hash',
            rol=rol,
        )
        assert u.nombre_completo == 'Test User'
        assert u.activo is True

    def test_str(self):
        rol = Roles.objects.create(nombre='director')
        u = Usuarios.objects.create(
            nombre='Test', primer_apellido='User', email='t@t.com',
            password_hash='hash', rol=rol,
        )
        assert str(u) == 'Test User'
