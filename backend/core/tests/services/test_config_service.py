import pytest
from django.test import override_settings

from core.models import ConfiguracionEscuela, Roles, Usuarios
from core.services.config_service import ConfigService


@pytest.mark.django_db
class TestConfigServiceObtener:

    def _make_admin(self):
        rol = Roles.objects.create(nombre='director')
        return Usuarios.objects.create(
            nombre='Admin', email='admin@test.com',
            password_hash='hash', rol=rol,
        )

    def test_obtener_crea_config_si_no_existe(self):
        usuario = self._make_admin()
        service = ConfigService()
        result = service.obtener(usuario)
        assert result['nombre'] == 'Unidad Educativa'
        assert result['gestion_actual'] is None
        assert ConfiguracionEscuela.objects.count() == 1

    def test_obtener_devuelve_config_existente(self):
        usuario = self._make_admin()
        ConfiguracionEscuela.objects.create(
            nombre='Mi Escuela', gestion_actual=2025,
        )
        service = ConfigService()
        result = service.obtener(usuario)
        assert result['nombre'] == 'Mi Escuela'
        assert result['gestion_actual'] == 2025

    def test_obtener_sin_permiso_raises(self):
        rol = Roles.objects.create(nombre='docente')
        usuario = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash='hash', rol=rol,
        )
        service = ConfigService()
        with pytest.raises(PermissionError, match='No autorizado'):
            service.obtener(usuario)


@pytest.mark.django_db
class TestConfigServiceActualizar:

    def _make_secretaria(self):
        rol = Roles.objects.create(nombre='secretaria')
        return Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash='hash', rol=rol,
        )

    def test_actualizar_campos(self):
        usuario = self._make_secretaria()
        service = ConfigService()
        result = service.actualizar(usuario, {'nombre': 'Nuevo Nombre', 'gestion_actual': 2027})
        assert result['nombre'] == 'Nuevo Nombre'
        assert result['gestion_actual'] == 2027

        config = ConfiguracionEscuela.objects.get()
        assert config.nombre == 'Nuevo Nombre'
        assert config.gestion_actual == 2027

    def test_actualizar_solo_campos_enviados(self):
        usuario = self._make_secretaria()
        service = ConfigService()
        result = service.actualizar(usuario, {'nombre': 'Escuela X'})
        assert result['nombre'] == 'Escuela X'
        assert result['gestion_actual'] is None

    def test_actualizar_sin_permiso_raises(self):
        rol = Roles.objects.create(nombre='docente')
        usuario = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash='hash', rol=rol,
        )
        service = ConfigService()
        with pytest.raises(PermissionError, match='Solo la secretaria'):
            service.actualizar(usuario, {'nombre': 'X'})
