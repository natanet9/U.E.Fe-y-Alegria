from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from core.services.catalog_service import CatalogService


@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


class TestCatalogUpdateService:

    def test_actualizar_nivel(self, admin_user):
        service = CatalogService()
        mock_nivel = MagicMock()
        mock_nivel.id = 1
        mock_nivel.nombre = "Original"
        with patch.object(service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(service.audit, 'record', return_value=None):
                with patch('core.services.catalog_service.Niveles.objects.get', return_value=mock_nivel):
                    result = service.actualizar_nivel(admin_user, 1, {'nombre': 'Actualizado'})
                assert mock_nivel.nombre == 'Actualizado'
                assert result['nombre'] == 'Actualizado'

    def test_actualizar_curso(self, admin_user):
        service = CatalogService()
        mock_curso = MagicMock()
        mock_curso.id = 1
        mock_curso.grado_id = 1
        mock_curso.paralelo_id = 1
        mock_curso.__str__ = lambda s: "Curso A"
        with patch.object(service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(service.audit, 'record', return_value=None):
                with patch('core.services.catalog_service.Cursos.objects.get', return_value=mock_curso):
                    result = service.actualizar_curso(admin_user, 1, {'grado_id': 2})
                assert mock_curso.grado_id == 2
                assert 'nombre_completo' in result

    def test_eliminar_nivel_soft(self, admin_user):
        service = CatalogService()
        with patch.object(service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(service.audit, 'record', return_value=None):
                with patch('core.services.catalog_service.Niveles.objects.filter') as mock_filter:
                    result = service.eliminar_nivel(admin_user, 1)
                mock_filter.return_value.update.assert_called_once_with(activo=False)
                assert result['mensaje'] == 'Nivel eliminado'
