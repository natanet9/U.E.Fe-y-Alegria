from io import BytesIO
import types

import pytest

from core.services.reports_service import ReportsService


class FakeArea:
    nombre = 'Matematicas'


class FakeUsuario:
    nombre_completo = 'Juan Perez'


class FakeCurso:
    def __str__(self):
        return 'Curso A'


class FakeDA:
    id = 1
    curso = FakeCurso()
    gestion = 2025
    area = FakeArea()
    usuario = FakeUsuario()


class FakeEstudiante:
    def __init__(self, id, rude, ci, nombres, primer_apellido):
        self.id = id
        self.rude = rude
        self.ci = ci
        self.nombres = nombres
        self.primer_apellido = primer_apellido


class FakeInscripcion:
    def __init__(self, estudiante):
        self.estudiante = estudiante


class FakePeriodo:
    nombre = 'Primer'
    gestion = 2025
    id = 1


def test_export_notas_docx_minimal(monkeypatch):
    svc = ReportsService()

    # Patch permission check
    monkeypatch.setattr('core.services.reports_service.AccessControlService.puede_exportar', lambda self, u: True)

    # Patch ORM calls
    monkeypatch.setattr('core.services.reports_service.DocenteAsignacion', types.SimpleNamespace(objects=types.SimpleNamespace(select_related=lambda *a, **k: types.SimpleNamespace(get=lambda id: FakeDA))))
    monkeypatch.setattr('core.services.reports_service.Periodos', types.SimpleNamespace(objects=types.SimpleNamespace(get=lambda id: FakePeriodo)))
    class FakeQuerySet:
        def __init__(self, items):
            self._items = items

        def select_related(self, *args, **kwargs):
            return self._items

        def __iter__(self):
            return iter(self._items)

    monkeypatch.setattr('core.services.reports_service.Inscripciones', types.SimpleNamespace(objects=types.SimpleNamespace(filter=lambda **kw: FakeQuerySet([FakeInscripcion(FakeEstudiante(1, 'R123', '123456', 'Ana', 'Lopez'))]))))

    # Patch DB lookup methods for notas
    monkeypatch.setattr(svc, '_get_notas_dim', lambda da_id, periodo_id: {1: {'SER': 10, 'SABER': 20, 'HACER': 30, 'AUTOEVALUACION': 5}})
    monkeypatch.setattr(svc, '_get_notas_tot', lambda da_id, periodo_id: {1: 65})

    buf = svc.export_notas_docx(usuario=None, docente_asignacion_id=1, periodo_id=1)
    assert isinstance(buf, BytesIO)
    data = buf.getvalue()
    # docx is a zip file; should start with PK
    assert data.startswith(b'PK')
