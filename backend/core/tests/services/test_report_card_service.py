import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from core.services.report_card_service import ReportCardService


@pytest.fixture
def director():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Director",
                           rol=SimpleNamespace(nombre="director"))


@pytest.fixture
def docente():
    return SimpleNamespace(id=2, activo=True, nombre_completo="Docente",
                           rol=SimpleNamespace(nombre="docente"))


class TestReportCardService:

    def test_boletin_consolidado_permiso_denied(self, docente):
        service = ReportCardService()
        with patch.object(service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError, match='No autorizado'):
                service.boletin_consolidado_gestion(docente)

    def test_boletin_consolidado_sin_periodos(self, director):
        service = ReportCardService()
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.models.Periodos.objects.filter') as mock_p:
                mock_p.return_value.order_by.return_value.first.return_value = None
                with pytest.raises(ValueError, match='No hay periodos activos'):
                    service.boletin_consolidado_gestion(director)

    def test_boletin_consolidado_sin_cursos(self, director):
        service = ReportCardService()
        mock_periodos = [
            MagicMock(id=1, nombre="Bim1"),
            MagicMock(id=2, nombre="Bim2"),
        ]
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.models.Cursos.objects.filter') as mock_cursos:
                mock_cursos.return_value.select_related.return_value.order_by.return_value = []
                with patch('core.models.Periodos.objects.filter') as mock_p:
                    mock_p.return_value.order_by.return_value = mock_periodos
                    result = service.boletin_consolidado_gestion(director, gestion=2026)
                    assert result['gestion'] == 2026
                    assert len(result['periodos']) == 2
                    assert result['cursos'] == []

    def test_boletin_consolidado_con_datos(self, director):
        service = ReportCardService()
        mock_curso = MagicMock(id=10, gestion=2026, activo=True)
        mock_curso.grado = MagicMock(nombre="Primero")
        mock_curso.paralelo = MagicMock(nombre="A")
        mock_curso.__str__ = lambda s: "Primero A"

        mock_estudiante = MagicMock(id=100, rude="RUD001", nombres="Juan",
                                     primer_apellido="Perez", segundo_apellido="")
        mock_inscripcion = MagicMock(estudiante_id=100, estudiante=mock_estudiante,
                                      curso=mock_curso, gestion=2026)

        mock_periodos = [
            MagicMock(id=1, nombre="Bim1"),
            MagicMock(id=2, nombre="Bim2"),
        ]

        mock_boletin = {
            'materias': [
                {'notas_por_periodo': {'1': 85.0, '2': 90.0}},
                {'notas_por_periodo': {'1': 75.0, '2': 80.0}},
            ]
        }

        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.models.Cursos.objects.filter') as mock_cursos:
                mock_cursos.return_value.select_related.return_value.order_by.return_value = [mock_curso]
                with patch('core.models.Inscripciones.objects.filter') as mock_ins:
                    mock_ins.return_value.select_related.return_value = [mock_inscripcion]
                    with patch('core.models.Periodos.objects.filter') as mock_p:
                        mock_p.return_value.order_by.return_value = mock_periodos
                        with patch.object(service, 'generar_boletin', return_value=mock_boletin):
                            result = service.boletin_consolidado_gestion(director, gestion=2026)
                            assert result['gestion'] == 2026
                            assert len(result['cursos']) == 1
                            curso_data = result['cursos'][0]
                            assert curso_data['curso'] == "Primero A"
                            assert len(curso_data['estudiantes']) == 1
                            est = curso_data['estudiantes'][0]
                            assert est['rude'] == "RUD001"
                            assert est['promedios_por_periodo']['1'] == 80.0
                            assert est['promedios_por_periodo']['2'] == 85.0
                            assert est['promedio_general'] == 82.5

    def test_boletin_consolidado_con_estudiante_sin_notas(self, director):
        service = ReportCardService()
        mock_curso = MagicMock(id=10, gestion=2026, activo=True)
        mock_curso.grado = MagicMock(nombre="Primero")
        mock_curso.paralelo = MagicMock(nombre="A")
        mock_curso.__str__ = lambda s: "Primero A"

        mock_estudiante = MagicMock(id=100, rude="RUD001", nombres="Juan",
                                     primer_apellido="Perez", segundo_apellido="")
        mock_inscripcion = MagicMock(estudiante_id=100, estudiante=mock_estudiante,
                                      curso=mock_curso, gestion=2026)

        mock_periodos = [MagicMock(id=1, nombre="Bim1")]

        mock_boletin = {
            'materias': [
                {'notas_por_periodo': {'1': None}},
            ]
        }

        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.models.Cursos.objects.filter') as mock_cursos:
                mock_cursos.return_value.select_related.return_value.order_by.return_value = [mock_curso]
                with patch('core.models.Inscripciones.objects.filter') as mock_ins:
                    mock_ins.return_value.select_related.return_value = [mock_inscripcion]
                    with patch('core.models.Periodos.objects.filter') as mock_p:
                        mock_p.return_value.order_by.return_value = mock_periodos
                        with patch.object(service, 'generar_boletin', return_value=mock_boletin):
                            result = service.boletin_consolidado_gestion(director, gestion=2026)
                            est = result['cursos'][0]['estudiantes'][0]
                            assert est['promedios_por_periodo']['1'] in (None, 0.0)
                            assert est['promedio_general'] in (None, 0.0)

    def test_boletin_consolidado_skip_error_estudiante(self, director):
        service = ReportCardService()
        mock_curso = MagicMock(id=10, gestion=2026, activo=True)
        mock_curso.grado = MagicMock(nombre="Primero")
        mock_curso.paralelo = MagicMock(nombre="A")
        mock_curso.__str__ = lambda s: "Primero A"

        mock_estudiante = MagicMock(id=100, rude="RUD001", nombres="Juan",
                                     primer_apellido="Perez", segundo_apellido="")
        mock_inscripcion = MagicMock(estudiante_id=100, estudiante=mock_estudiante,
                                      curso=mock_curso, gestion=2026)

        mock_periodos = [MagicMock(id=1, nombre="Bim1")]

        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.models.Cursos.objects.filter') as mock_cursos:
                mock_cursos.return_value.select_related.return_value.order_by.return_value = [mock_curso]
                with patch('core.models.Inscripciones.objects.filter') as mock_ins:
                    mock_ins.return_value.select_related.return_value = [mock_inscripcion]
                    with patch('core.models.Periodos.objects.filter') as mock_p:
                        mock_p.return_value.order_by.return_value = mock_periodos
                        with patch.object(service, 'generar_boletin', side_effect=Exception("DB error")):
                            result = service.boletin_consolidado_gestion(director, gestion=2026)
                            assert len(result['cursos']) == 0
