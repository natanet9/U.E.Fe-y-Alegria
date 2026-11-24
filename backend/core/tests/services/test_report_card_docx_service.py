from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.services.report_card_docx_service import (
    _numero_a_texto,
    ReportCardDOCXService,
    get_boletin_template_path,
)


def test_numero_a_texto():
    assert _numero_a_texto(0) == 'CERO'
    assert _numero_a_texto(1) == 'UNO'
    assert _numero_a_texto(5) == 'CINCO'
    assert _numero_a_texto(9) == 'NUEVE'
    assert _numero_a_texto(10) == 'DIEZ'
    assert _numero_a_texto(11) == 'ONCE'
    assert _numero_a_texto(15) == 'QUINCE'
    assert _numero_a_texto(16) == 'DIECISEIS'
    assert _numero_a_texto(20) == 'VEINTE'
    assert _numero_a_texto(21) == 'VEINTIUNO'
    assert _numero_a_texto(25) == 'VEINTICINCO'
    assert _numero_a_texto(30) == 'TREINTA'
    assert _numero_a_texto(35) == 'TREINTA Y CINCO'
    assert _numero_a_texto(50) == 'CINCUENTA'
    assert _numero_a_texto(55) == 'CINCUENTA Y CINCO'
    assert _numero_a_texto(100) == 'CIEN'


def test_get_boletin_template_path():
    path = get_boletin_template_path()
    assert path.is_file()
    assert path.name == 'boletin_template.docx'


def test_generar_docx_mocked():
    service = ReportCardDOCXService()
    mock_data = {
        'estudiante': {
            'rude': 'RUD123',
            'primer_apellido': 'Perez',
            'segundo_apellido': 'Lopez',
            'nombres': 'Juan'
        },
        'curso': {
            'grado': 'Primero',
            'paralelo': 'A'
        },
        'periodos': [{'id': 1, 'nombre': 'Primer Trimestre'}],
        'materias': [
            {
                'area': 'Matematicas',
                'notas_por_periodo': {'1': 85.5},
                'promedio_final': 85.5
            }
        ],
        'asistencias': [],
        'gestion': 2026
    }

    # Patch template path and Document
    with patch('core.services.report_card_docx_service.Document') as mock_doc:
        mock_instance = mock_doc.return_value
        def fake_save(buf):
            buf.write(b'PK\x03\x04mock_docx')
        mock_instance.save.side_effect = fake_save
        mock_instance.paragraphs = []

        mock_rows = []
        for _ in range(15):
            mock_cells = []
            for _ in range(10):
                cell = MagicMock()
                p = MagicMock()
                cell.paragraphs = [p]
                mock_cells.append(cell)
            mock_rows.append(MagicMock(cells=mock_cells))

        mock_table = MagicMock()
        mock_table.rows = mock_rows
        mock_instance.tables = [MagicMock(), MagicMock(), mock_table, mock_table]

        with patch.object(service._rcs, 'generar_boletin', return_value=mock_data):
            result = service.generar_docx(SimpleNamespace(), estudiante_id=1)
            assert isinstance(result, bytes)
            assert len(result) > 0


def test_generar_docx_real_template():
    service = ReportCardDOCXService()
    mock_data = {
        'estudiante': {
            'rude': 'RUD123',
            'primer_apellido': 'Perez',
            'segundo_apellido': 'Lopez',
            'nombres': 'Juan'
        },
        'curso': {
            'grado': 'Primero',
            'paralelo': 'A'
        },
        'periodos': [{'id': 1, 'nombre': 'Primer Trimestre'}],
        'materias': [
            {
                'area': 'Matematicas',
                'notas_por_periodo': {'1': 85.5},
                'promedio_final': 85.5
            }
        ],
        'asistencias': [],
        'gestion': 2026
    }

    with patch.object(service._rcs, 'generar_boletin', return_value=mock_data):
        result = service.generar_docx(SimpleNamespace(), estudiante_id=1)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result.startswith(b'PK')
