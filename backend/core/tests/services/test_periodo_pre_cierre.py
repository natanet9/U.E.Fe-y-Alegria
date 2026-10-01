from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from core.services.periodo_service import PeriodoService


@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


class TestPeriodoPreCierreValidation:

    def test_cerrar_con_actividades_sin_notas_rechaza(self, admin_user):
        service = PeriodoService()
        mock_periodo = MagicMock()
        mock_periodo.id = 1
        mock_periodo.estado = 'activo'
        mock_act = MagicMock()
        mock_act.id = 10
        mock_act.nombre = "Actividad 1"
        mock_act.docente_asignacion_id = 5
        mock_da = MagicMock()
        mock_da.curso = MagicMock(__str__=lambda s: "Curso A")
        mock_da.area = MagicMock(nombre="Matematicas")
        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_acts.return_value.only.return_value = [mock_act]
                    with patch('core.services.periodo_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.exists.return_value = False
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da_filter:
                            mock_da_filter.return_value.select_related.return_value.first.return_value = mock_da
                            with pytest.raises(ValueError, match='No se puede cerrar'):
                                service.cerrar(admin_user, 1)
                            mock_periodo.save.assert_not_called()

    def test_cerrar_con_multiples_actividades_sin_notas(self, admin_user):
        service = PeriodoService()
        mock_periodo = MagicMock()
        mock_periodo.id = 1
        mock_periodo.estado = 'activo'
        mock_acts = []
        for i in range(1, 26):
            a = MagicMock()
            a.id = i
            a.nombre = f"Act {i}"
            a.docente_asignacion_id = 5
            mock_acts.append(a)
        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts_filter:
                    mock_acts_filter.return_value.only.return_value = mock_acts
                    with patch('core.services.periodo_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.exists.return_value = False
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da_filter:
                            mock_da_filter.return_value.select_related.return_value.first.return_value = MagicMock(
                                curso=MagicMock(__str__=lambda s: "Curso"),
                                area=MagicMock(nombre="Area"),
                            )
                            with pytest.raises(ValueError, match='y 5 mas'):
                                service.cerrar(admin_user, 1)

    def test_cerrar_con_todas_notas_exito(self, admin_user):
        service = PeriodoService()
        mock_periodo = MagicMock()
        mock_periodo.id = 1
        mock_periodo.estado = 'activo'
        mock_periodo.gestion = 2026
        mock_act = MagicMock()
        mock_act.id = 10
        mock_act.nombre = "Actividad 1"
        mock_act.docente_asignacion_id = 5
        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_acts.return_value.only.return_value = [mock_act]
                    with patch('core.services.periodo_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.exists.return_value = True
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da:
                            mock_da.return_value.exclude.return_value.select_related.return_value.exists.return_value = False
                            with patch('core.services.periodo_service.PeriodoCierreDocente.objects.filter') as mock_pcd:
                                mock_pcd.return_value.values.return_value = []
                                with patch.object(service.audit, 'record', return_value=None):
                                    result = service.cerrar(admin_user, 1)
                                assert mock_periodo.estado == 'cerrado'
                                assert mock_periodo.cerrado_por == admin_user

    def test_cerrar_ya_cerrado(self, admin_user):
        service = PeriodoService()
        mock_periodo = MagicMock()
        mock_periodo.id = 1
        mock_periodo.estado = 'cerrado'
        with patch.object(service.ac, 'puede_cerrar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with pytest.raises(ValueError, match='Solo se puede cerrar un periodo activo'):
                    service.cerrar(admin_user, 1)

    def test_habilitar_cascada_desactiva_otros(self, admin_user):
        """Habilitar un periodo cierra el periodo activo anterior de la misma gestion."""
        service = PeriodoService()
        mock_periodo = MagicMock()
        mock_periodo.id = 2
        mock_periodo.estado = 'pendiente'
        mock_periodo.gestion = 2026
        mock_anterior = MagicMock()
        mock_anterior.estado = 'activo'
        with patch.object(service.ac, 'puede_habilitar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Periodos.objects.filter') as mock_filter:
                    mock_filter.return_value.exclude.return_value.first.return_value = mock_anterior
                    with patch.object(service.audit, 'record', return_value=None):
                        result = service.habilitar(admin_user, 2)
                    assert mock_periodo.estado == 'activo'
                    assert mock_anterior.estado == 'cerrado'
                    assert mock_anterior.cerrado_por == admin_user
                    mock_anterior.save.assert_called_once_with(
                        update_fields=['estado', 'cerrado_por', 'cerrado_en']
                    )

    def test_habilitar_ya_activo(self, admin_user):
        service = PeriodoService()
        mock_periodo = MagicMock()
        mock_periodo.id = 1
        mock_periodo.estado = 'activo'
        with patch.object(service.ac, 'puede_habilitar_periodo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with pytest.raises(ValueError, match='no se puede habilitar'):
                    service.habilitar(admin_user, 1)
