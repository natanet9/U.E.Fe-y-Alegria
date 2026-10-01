import pytest
from django.contrib.auth.hashers import make_password

from core.models import Roles, Usuarios
from core.services.auth_service import AuthService


@pytest.mark.django_db
class TestAuthService:

    @pytest.fixture
    def user(self):
        rol = Roles.objects.create(nombre='director')
        return Usuarios.objects.create(
            nombre='Test', primer_apellido='User',
            email='test@test.com',
            password_hash=make_password('123456'),
            rol=rol,
            activo=True,
        )

    def test_login_success(self, user):
        data, err = AuthService().login('test@test.com', '123456')
        assert err is None
        assert data is not None
        assert 'token' in data
        assert data['usuario']['email'] == 'test@test.com'

    def test_login_wrong_password(self, user):
        data, err = AuthService().login('test@test.com', 'wrong')
        assert data is None
        assert err == 'Credenciales invalidas'

    def test_login_nonexistent(self, user):
        data, err = AuthService().login('no@test.com', '123456')
        assert data is None
        assert err == 'Credenciales invalidas'

    def test_login_inactive(self, user):
        user.activo = False
        user.save()
        data, err = AuthService().login('test@test.com', '123456')
        assert data is None
        assert err == 'Usuario inactivo'

    def test_change_password_success(self, user):
        data, err = AuthService().change_password(user, '123456', 'nueva123')
        assert err is None
        assert data['mensaje'] == 'Contrasena cambiada exitosamente'

    def test_change_password_wrong_old(self, user):
        data, err = AuthService().change_password(user, 'wrong', 'nueva123')
        assert err == 'Contrasena actual incorrecta'

    def test_change_password_too_short(self, user):
        data, err = AuthService().change_password(user, '123456', 'ab')
        assert err == 'Nueva contrasena debe tener al menos 6 caracteres'

    def test_me(self, user):
        data = AuthService().get_me(user)
        assert data['email'] == 'test@test.com'
        assert data['rol'] == 'director'
