from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from core.services.schedule_service import ScheduleService
from core.models import Horarios


@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


class TestScheduleUpdateService:

    def test_actualizar_horario_success(self, admin_user):
        service = ScheduleService()
        mock_horario = MagicMock()
        mock_horario.id = 1
        mock_horario.dia_semana = 1
        mock_horario.hora_inicio = "08:00"
        mock_horario.hora_fin = "09:00"
        mock_horario.aula = "A1"
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch.object(service.audit, 'record', return_value=None):
                with patch('core.services.schedule_service.Horarios.objects.get', return_value=mock_horario):
                    result = service.actualizar_horario(admin_user, 1, {'aula': 'B2'})
                assert result['mensaje'] == 'Horario actualizado'
                assert mock_horario.aula == 'B2'

    def test_actualizar_horario_permission_error(self, admin_user):
        service = ScheduleService()
        with patch.object(service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                service.actualizar_horario(admin_user, 1, {})

    def test_actualizar_horario_not_found(self, admin_user):
        service = ScheduleService()
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.schedule_service.Horarios.objects.get', side_effect=Horarios.DoesNotExist):
                with pytest.raises(Horarios.DoesNotExist):
                    service.actualizar_horario(admin_user, 999, {})
