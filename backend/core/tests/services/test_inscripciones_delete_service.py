from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from core.services.inscripciones_service import InscripcionesService
from core.models import Inscripciones


@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


class TestInscripcionesDeleteService:

    def test_eliminar_success(self, admin_user):
        service = InscripcionesService()
        mock_inscripcion = MagicMock()
        mock_inscripcion.id = 1
        mock_inscripcion.estudiante_id = 1
        mock_inscripcion.curso_id = 1
        mock_inscripcion.gestion = 2026
        mock_inscripcion.estado = "activo"
        with patch.object(service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch('core.services.inscripciones_service.Inscripciones.objects.get', return_value=mock_inscripcion):
                with patch.object(service.audit, 'record_inscripcion_change'):
                    result = service.eliminar(admin_user, 1)
                    assert result['mensaje'] == 'Inscripcion eliminada'
                    mock_inscripcion.save.assert_called_once_with(update_fields=['activo'])

    def test_eliminar_permission_error(self, admin_user):
        service = InscripcionesService()
        with patch.object(service.ac, 'puede_gestionar_inscripciones', return_value=False):
            with pytest.raises(PermissionError):
                service.eliminar(admin_user, 1)

    def test_eliminar_not_found(self, admin_user):
        service = InscripcionesService()
        with patch.object(service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch('core.services.inscripciones_service.Inscripciones.objects.get', side_effect=Inscripciones.DoesNotExist):
                with pytest.raises(Inscripciones.DoesNotExist):
                    service.eliminar(admin_user, 999)
