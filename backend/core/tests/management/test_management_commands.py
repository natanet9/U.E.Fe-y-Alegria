import pytest
from django.core.management import call_command

from core.models import Areas, DimensionesEvaluacion, Estudiantes, Niveles, Periodos, Roles, Usuarios


@pytest.mark.django_db
class TestManagementCommands:

    def test_seed_data_creates_core_catalogs(self):
        call_command('seed_data')

        assert Roles.objects.count() >= 5
        assert Niveles.objects.count() >= 1
        assert Areas.objects.count() >= 1
        assert Estudiantes.objects.count() >= 1
        assert Periodos.objects.count() >= 1
        assert Usuarios.objects.count() >= 1

    def test_seed_grading_dimensions_is_idempotent(self):
        call_command('seed_grading_dimensions')
        call_command('seed_grading_dimensions')

        nombres = list(DimensionesEvaluacion.objects.order_by('orden').values_list('nombre', flat=True))
        assert nombres == ['SER', 'SABER', 'HACER', 'AUTOEVALUACION']
        assert DimensionesEvaluacion.objects.count() == 4
