from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from datetime import date

import pytest

from core.services.dashboard_service import DashboardService


@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


@pytest.fixture
def director_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Director", email="dir@test.com",
                           rol=SimpleNamespace(nombre="director"))


@pytest.fixture
def docente_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Docente", email="doc@test.com",
                           rol=SimpleNamespace(nombre="docente"))


class TestDashboardSQLQueries:

    def test_promedio_por_asignatura_with_data(self, director_user):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("Matematicas", 85.5), ("Lenguaje", 78.3)]
        mock_periodo = MagicMock(id=1, nombre="Bim1", gestion=2026)
        with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_periodos:
            mock_periodos.return_value.order_by.return_value.first.return_value = mock_periodo
            with patch.object(service.ac, 'get_role_name', return_value='director'):
                with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
                    result = service._dashboard_director()
                    assert 'promedio_por_asignatura' in result
                    assert result['promedio_por_asignatura']['labels'] == ["Matematicas", "Lenguaje"]
                    assert result['promedio_por_asignatura']['data'] == [85.5, 78.3]

    def test_promedio_por_asignatura_sin_periodo(self, director_user):
        service = DashboardService()
        with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_periodos:
            mock_periodos.return_value.order_by.return_value.first.return_value = None
            with patch.object(service.ac, 'get_role_name', return_value='director'):
                result = service._dashboard_director()
                assert result['promedio_por_asignatura'] == {'labels': [], 'data': []}

    def test_promedio_por_asignatura_operational_error(self, director_user):
        service = DashboardService()
        mock_periodo = MagicMock(id=1)
        with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_periodos:
            mock_periodos.return_value.order_by.return_value.first.return_value = mock_periodo
            with patch.object(service.ac, 'get_role_name', return_value='director'):
                with patch('core.services.dashboard_service.connection.cursor', side_effect=Exception('no view')):
                    result = service._dashboard_director()
                    assert result['promedio_por_asignatura'] == {'labels': [], 'data': []}

    def test_distribucion_rendimiento_with_data(self):
        """Test the SQL query for _distribucion_rendimiento with mock cursor data."""
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(97.0,), (85.0,), (75.0,), (60.0,), (45.0,), (None,)]
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            periodo = MagicMock(id=1)
            result = service._distribucion_rendimiento(periodo)
            assert len(result) == 5
            # 97 -> Excelente, 85 -> Sobresaliente, 75 -> Bueno, 60 -> Regular, 45 -> Reprobado, None -> Reprobado
            assert result[0]['label'] == 'Excelente'
            assert result[0]['count'] == 1
            assert result[1]['label'] == 'Sobresaliente'
            assert result[1]['count'] == 1
            assert result[2]['label'] == 'Bueno'
            assert result[2]['count'] == 1
            assert result[3]['label'] == 'Regular'
            assert result[3]['count'] == 1
            assert result[4]['label'] == 'Reprobado'
            assert result[4]['count'] == 2

    def test_distribucion_rendimiento_sin_periodo(self):
        service = DashboardService()
        result = service._distribucion_rendimiento(None)
        assert all(s['value'] == 0 for s in result)

    def test_distribucion_rendimiento_operational_error(self):
        service = DashboardService()
        with patch('core.services.dashboard_service.connection.cursor', side_effect=Exception('no view')):
            periodo = MagicMock(id=1)
            result = service._distribucion_rendimiento(periodo)
            assert all(s['value'] == 0 for s in result)

    def test_estudiantes_destacados_with_data(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 98.0), (2, 95.5)]
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            with patch('core.services.dashboard_service.Estudiantes.objects.filter') as mock_est:
                mock_est1 = MagicMock(id=1, nombres="Juan", primer_apellido="Perez")
                mock_est2 = MagicMock(id=2, nombres="Maria", primer_apellido="Lopez")
                mock_est.return_value = MagicMock()
                mock_est.return_value.__iter__.return_value = [mock_est1, mock_est2]
                result = service._estudiantes_destacados(MagicMock(id=1, nombre="B1", gestion=2026))
                assert len(result) == 2
                assert 'Juan' in result[0]['nombre']
                assert result[0]['promedio'] == 98.0

    def test_estudiantes_destacados_no_data(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            result = service._estudiantes_destacados(MagicMock(id=1))
            assert result == []

    def test_estudiantes_destacados_sin_periodo(self):
        service = DashboardService()
        result = service._estudiantes_destacados(None)
        assert result == []

    def test_estudiantes_con_notas_success(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (25,)
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            result = service._estudiantes_con_notas(MagicMock(id=1))
            assert result == 25

    def test_estudiantes_con_notas_sin_periodo(self):
        service = DashboardService()
        result = service._estudiantes_con_notas(None)
        assert result == 0

    def test_estudiantes_con_notas_operational_error(self):
        service = DashboardService()
        with patch('core.services.dashboard_service.connection.cursor', side_effect=Exception('no view')):
            result = service._estudiantes_con_notas(MagicMock(id=1))
            assert result == 0

    def test_promedio_por_curso_with_data(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("6to A", 72.5), ("5to B", 68.3)]
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            result = service._promedio_por_curso(MagicMock(id=1))
            assert result['labels'] == ["6to A", "5to B"]
            assert result['data'] == [72.5, 68.3]

    def test_promedio_por_curso_sin_periodo(self):
        service = DashboardService()
        result = service._promedio_por_curso(None)
        assert result == {'labels': [], 'data': []}

    def test_promedio_por_curso_operational_error(self):
        service = DashboardService()
        with patch('core.services.dashboard_service.connection.cursor', side_effect=Exception('no view')):
            result = service._promedio_por_curso(MagicMock(id=1))
            assert result == {'labels': [], 'data': []}

    def test_asistencia_por_curso_semanal_with_data(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("6to A", 95.0), ("5to B", 82.5)]
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            result = service._asistencia_por_curso_semanal()
            assert result['labels'] == ["6to A", "5to B"]
            assert result['data'] == [95.0, 82.5]

    def test_asistencia_por_curso_semanal_operational_error(self):
        service = DashboardService()
        with patch('core.services.dashboard_service.connection.cursor', side_effect=Exception('no view')):
            result = service._asistencia_por_curso_semanal()
            assert result == {'labels': [], 'data': []}

    def test_estudiantes_riesgo_with_data(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 42.0), (2, 38.5)]
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            with patch('core.services.dashboard_service.Estudiantes.objects.filter') as mock_est:
                mock_est1 = MagicMock(id=1, nombres="Pedro", primer_apellido="Lopez")
                mock_est2 = MagicMock(id=2, nombres="Ana", primer_apellido="Mamani")
                mock_est.return_value = MagicMock()
                mock_est.return_value.__iter__.return_value = [mock_est1, mock_est2]
                result = service._estudiantes_riesgo(MagicMock(id=1, nombre="B1", gestion=2026))
                assert len(result) == 2
                assert 'Pedro' in result[0]['nombre']
                assert result[0]['promedio'] == 42.0

    def test_estudiantes_riesgo_no_data(self):
        service = DashboardService()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        with patch('core.services.dashboard_service.connection.cursor', return_value=mock_cursor):
            result = service._estudiantes_riesgo(MagicMock(id=1))
            assert result == []

    def test_estudiantes_riesgo_sin_periodo(self):
        service = DashboardService()
        result = service._estudiantes_riesgo(None)
        assert result == []

    def test_estudiantes_riesgo_operational_error(self):
        service = DashboardService()
        with patch('core.services.dashboard_service.connection.cursor', side_effect=Exception('no view')):
            result = service._estudiantes_riesgo(MagicMock(id=1))
            assert result == []

    def test_docentes_sin_cierre(self):
        service = DashboardService()
        mock_periodo = MagicMock(id=1, gestion=2026, estado="activo")
        with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_filter:
            mock_filter.return_value.first.return_value = mock_periodo
            with patch('core.services.dashboard_service.DocenteAsignacion.objects.filter') as mock_da:
                mock_da.return_value.exclude.return_value.select_related.return_value.__getitem__.return_value = []
                result = service._docentes_sin_cierre()
                assert isinstance(result, list)

    def test_docentes_sin_cierre_sin_periodo(self):
        service = DashboardService()
        with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_filter:
            mock_filter.return_value.first.return_value = None
            result = service._docentes_sin_cierre()
            assert result == []

    def test_dashboard_docente_sin_asignaciones(self, docente_user):
        service = DashboardService()
        with patch.object(service.ac, 'get_role_name', return_value='docente'):
            with patch.object(service.ac, 'get_asignaciones_docente', return_value=[]):
                with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_p:
                    mock_p.return_value.order_by.return_value.first.return_value = None
                    result = service.build_dashboard(docente_user)
                    assert 'asignaciones' in result
                    assert result['asignaciones'] == []

    def test_dashboard_docente_with_asignaciones(self, docente_user):
        service = DashboardService()
        mock_da = MagicMock(id=1, curso=MagicMock(__str__=lambda s: "Curso A"), area=MagicMock(nombre="Mate"), gestion=2026)
        with patch.object(service.ac, 'get_role_name', return_value='docente'):
            with patch.object(service.ac, 'get_asignaciones_docente', return_value=[mock_da]):
                with patch('core.services.dashboard_service.Inscripciones.objects.filter') as mock_ins:
                    mock_ins.return_value.values.return_value.distinct.return_value.count.return_value = 20
                    with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_p:
                        mock_p.return_value.order_by.return_value.first.return_value = None
                        with patch('core.services.dashboard_service.connection.cursor') as mock_cursor:
                            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (15,)
                            mock_cursor.return_value.fetchone.return_value = (15,)
                            with patch('core.services.dashboard_service.Actividades.objects.filter') as mock_acts:
                                mock_acts.return_value.count.return_value = 5
                                result = service.build_dashboard(docente_user)
                                assert result['total_estudiantes'] == 20

    def test_dashboard_director(self, director_user):
        service = DashboardService()
        with patch.object(service.ac, 'get_role_name', return_value='director'):
            with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_p:
                mock_p.return_value.order_by.return_value.first.return_value = None
                with patch.object(service, '_global_stats', return_value={}):
                    with patch.object(service, '_periodo_activo_info', return_value=None):
                        with patch.object(service, '_alertas', return_value=[]):
                            with patch.object(service, '_licencias_pendientes_count', return_value=0):
                                with patch.object(service, '_promedio_por_asignatura', return_value={'labels': [], 'data': []}):
                                    with patch.object(service, '_promedio_por_curso', return_value={'labels': [], 'data': []}):
                                        with patch.object(service, '_asistencia_por_curso_semanal', return_value={'labels': [], 'data': []}):
                                            with patch.object(service, '_distribucion_rendimiento', return_value=[]):
                                                with patch.object(service, '_estudiantes_destacados', return_value=[]):
                                                    with patch.object(service, '_estudiantes_riesgo', return_value=[]):
                                                        with patch.object(service, '_estudiantes_con_notas', return_value=0):
                                                            with patch.object(service, '_docentes_sin_cierre', return_value=[]):
                                                                with patch('core.services.dashboard_service.Usuarios.objects.filter') as mock_u:
                                                                    mock_u.return_value.order_by.return_value[:5] = []
                                                                    result = service.build_dashboard(director_user)
                                                                    assert 'stats' in result

    def test_dashboard_secretaria(self, admin_user):
        service = DashboardService()
        with patch.object(service.ac, 'get_role_name', return_value='secretaria'):
            with patch.object(service, '_global_stats', return_value={}):
                with patch.object(service, '_periodo_activo_info', return_value=None):
                    with patch.object(service, '_docentes_sin_cierre', return_value=[]):
                        result = service.build_dashboard(admin_user)
                        assert 'docentes_sin_cierre' in result

    def test_dashboard_default(self):
        service = DashboardService()
        tutor_user = SimpleNamespace(id=1, activo=True, nombre_completo="Tutor",
                                      ci="12345678",
                                      rol=SimpleNamespace(nombre="tutor"))
        with patch.object(service.ac, 'get_role_name', return_value='tutor'):
            with patch.object(service, '_dashboard_tutor', return_value={'estudiantes': [], 'total_estudiantes': 0}):
                result = service.build_dashboard(tutor_user)
                assert 'estudiantes' in result

    def test_dashboard_regente(self):
        service = DashboardService()
        regente_user = SimpleNamespace(id=1, activo=True, nombre_completo="Regente",
                                        rol=SimpleNamespace(nombre="regente"))
        with patch.object(service.ac, 'get_role_name', return_value='regente'):
            with patch.object(service, '_licencias_pendientes_count', return_value=3):
                with patch('core.services.dashboard_service.Licencias.objects.filter') as mock_lic:
                    mock_lic.return_value.count.return_value = 1
                    with patch('core.services.dashboard_service.Periodos.objects.filter') as mock_p:
                        mock_p.return_value.first.return_value = None
                        result = service.build_dashboard(regente_user)
                        assert 'licencias_pendientes' in result
                        assert result['licencias_pendientes'] == 3
                        assert 'licencias_ultima_semana' in result
