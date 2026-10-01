import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from core.services.periodo_service import PeriodoService


@pytest.fixture
def director():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Director",
                           email="dir@test.com",
                           rol=SimpleNamespace(nombre="director"))


class TestPeriodoServiceDirector:

    def test_cerrar_raises_when_not_director(self):
        service = PeriodoService()
        docente = SimpleNamespace(id=2, rol=SimpleNamespace(nombre="docente"),
                                  activo=True, nombre_completo="Docente")
        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=False):
            with pytest.raises(PermissionError):
                service.cerrar(docente, 1)

    def test_cerrar_raises_when_not_active(self, director):
        service = PeriodoService()
        mock_periodo = MagicMock(estado='pendiente')
        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with pytest.raises(ValueError, match='Solo se puede cerrar un periodo activo'):
                    service.cerrar(director, 1)

    def test_cerrar_raises_when_docentes_pending_cierre(self, director):
        service = PeriodoService()
        mock_periodo = MagicMock(id=1, estado='activo', nombre='Bim1', gestion=2026)

        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_acts.return_value.only.return_value = []
                    with patch('core.services.periodo_service.PeriodoCierreDocente.objects.filter') as mock_pcd:
                        mock_pcd.return_value.values.return_value = []
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da:
                            mock_da.return_value.exclude.return_value.select_related.return_value.exists.return_value = True
                            mock_da.return_value.exclude.return_value.select_related.return_value.__getitem__.return_value = [
                                MagicMock(
                                    usuario=MagicMock(nombre_completo="Docente A"),
                                    area=MagicMock(nombre="Matematicas")
                                )
                            ]
                            mock_da.return_value.exclude.return_value.select_related.return_value.count.return_value = 1
                            with pytest.raises(ValueError, match='No se puede cerrar el periodo'):
                                service.cerrar(director, 1)

    def test_cerrar_success(self, director):
        service = PeriodoService()
        mock_periodo = MagicMock(id=1, estado='activo', nombre='Bim1', gestion=2026)

        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_acts.return_value.only.return_value = []
                    with patch('core.services.periodo_service.PeriodoCierreDocente.objects.filter') as mock_pcd:
                        mock_pcd.return_value.values.return_value = [1, 2]
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da:
                            mock_da.return_value.exclude.return_value.select_related.return_value.exists.return_value = False
                            with patch.object(service.audit, 'record', return_value=None):
                                result = service.cerrar(director, 1)
                            assert mock_periodo.estado == 'cerrado'
                            assert mock_periodo.cerrado_por == director

    def test_cerrar_raises_when_actividades_sin_notas(self, director):
        service = PeriodoService()
        mock_periodo = MagicMock(id=1, estado='activo', nombre='Bim1', gestion=2026)

        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_act = MagicMock(id=10, nombre="Examen 1", docente_asignacion_id=100)
                    mock_acts.return_value.only.return_value = [mock_act]
                    with patch('core.services.periodo_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.exists.return_value = False
                        with patch('core.services.periodo_service.PeriodoCierreDocente.objects.filter') as mock_pcd:
                            mock_pcd.return_value.values.return_value = [1, 2]
                            with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da:
                                mock_da.return_value.exclude.return_value.select_related.return_value.exists.return_value = False
                                with pytest.raises(ValueError, match='actividades no tienen notas'):
                                    service.cerrar(director, 1)
