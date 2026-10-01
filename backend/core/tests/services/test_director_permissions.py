import pytest
from types import SimpleNamespace
from unittest.mock import patch

from core.services.access_service import AccessControlService


@pytest.fixture
def director():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Director",
                           rol=SimpleNamespace(nombre="director"))


@pytest.fixture
def secretaria():
    return SimpleNamespace(id=2, activo=True, nombre_completo="Secretaria",
                           rol=SimpleNamespace(nombre="secretaria"))


@pytest.fixture
def docente():
    return SimpleNamespace(id=3, activo=True, nombre_completo="Docente",
                           rol=SimpleNamespace(nombre="docente"))


@pytest.fixture
def regente():
    return SimpleNamespace(id=4, activo=True, nombre_completo="Regente",
                           rol=SimpleNamespace(nombre="regente"))


@pytest.fixture
def tutor():
    return SimpleNamespace(id=5, activo=True, nombre_completo="Tutor",
                           rol=SimpleNamespace(nombre="tutor"))


class TestDirectorPermissions:

    def test_puede_modificar_notas_con_motivo_director(self, director):
        ac = AccessControlService()
        assert ac.puede_modificar_notas_con_motivo(director) is True

    def test_puede_modificar_notas_con_motivo_secretaria(self, secretaria):
        ac = AccessControlService()
        assert ac.puede_modificar_notas_con_motivo(secretaria) is False

    def test_puede_modificar_notas_con_motivo_docente(self, docente):
        ac = AccessControlService()
        assert ac.puede_modificar_notas_con_motivo(docente) is False

    def test_puede_modificar_notas_con_motivo_regente(self, regente):
        ac = AccessControlService()
        assert ac.puede_modificar_notas_con_motivo(regente) is False

    def test_puede_modificar_notas_con_motivo_tutor(self, tutor):
        ac = AccessControlService()
        assert ac.puede_modificar_notas_con_motivo(tutor) is False

    def test_puede_modificar_notas_con_motivo_none(self):
        ac = AccessControlService()
        assert ac.puede_modificar_notas_con_motivo(None) is False

    def test_puede_aprobar_licencia_directa_director_any(self, director):
        ac = AccessControlService()
        assert ac.puede_aprobar_licencia_directa(director, 1) is True
        assert ac.puede_aprobar_licencia_directa(director, 3) is True
        assert ac.puede_aprobar_licencia_directa(director, 10) is True
        assert ac.puede_aprobar_licencia_directa(director, 100) is True

    def test_puede_aprobar_licencia_directa_secretaria_any(self, secretaria):
        ac = AccessControlService()
        assert ac.puede_aprobar_licencia_directa(secretaria, 1) is True
        assert ac.puede_aprobar_licencia_directa(secretaria, 5) is True
        assert ac.puede_aprobar_licencia_directa(secretaria, 30) is True

    def test_puede_aprobar_licencia_directa_regente_max_3(self, regente):
        ac = AccessControlService()
        assert ac.puede_aprobar_licencia_directa(regente, 1) is True
        assert ac.puede_aprobar_licencia_directa(regente, 3) is True
        assert ac.puede_aprobar_licencia_directa(regente, 4) is False
        assert ac.puede_aprobar_licencia_directa(regente, 10) is False

    def test_puede_aprobar_licencia_directa_docente(self, docente):
        ac = AccessControlService()
        assert ac.puede_aprobar_licencia_directa(docente, 1) is False
        assert ac.puede_aprobar_licencia_directa(docente, 3) is False
        assert ac.puede_aprobar_licencia_directa(docente, 5) is False

    def test_puede_aprobar_licencia_directa_tutor(self, tutor):
        ac = AccessControlService()
        assert ac.puede_aprobar_licencia_directa(tutor, 1) is False
        assert ac.puede_aprobar_licencia_directa(tutor, 3) is False

    def test_puede_aprobar_licencia_directa_none(self):
        ac = AccessControlService()
        assert ac.puede_aprobar_licencia_directa(None, 1) is False
