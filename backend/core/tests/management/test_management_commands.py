import pytest
from django.core.management import call_command

from core.models import Areas, DimensionesEvaluacion, Estudiantes, Niveles, Periodos, Roles, Usuarios, Tutores


@pytest.mark.django_db
class TestManagementCommands:

    def test_seed_creates_core_catalogs_and_users(self):
        call_command('seed')

        assert Roles.objects.count() >= 5
        assert Niveles.objects.count() >= 2
        assert Areas.objects.count() >= 5
        assert Estudiantes.objects.count() >= 10
        assert Tutores.objects.count() >= 5
        assert Periodos.objects.count() >= 2
        assert Usuarios.objects.count() >= 10

    def test_seed_dimensiones_is_consistent(self):
        call_command('seed')

        nombres = list(DimensionesEvaluacion.objects.filter(gestion=2026).order_by('orden').values_list('nombre', flat=True))
        assert nombres == ['SER', 'SABER', 'HACER', 'AUTOEVALUACION']
