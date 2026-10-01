from core.services.grades_page_service import NORMALIZACION_MATERIAS


class TestNORMALIZACION_MATERIAS:
    """Verify the normalization map handles all expected subject names."""

    def test_expected_keys_present(self):
        expected = {
            "Artes Plasticas": "Artes Plásticas",
            "Educacion Fisica": "Educación Física",
            "Lenguaje y Comunicacion": "Lenguaje y Comunicación",
            "Matematicas": "Matemáticas",
            "Tecnica Tecnologica": "Técnica Tecnológica",
        }
        assert NORMALIZACION_MATERIAS == expected

    def test_get_returns_normalized_name(self):
        assert NORMALIZACION_MATERIAS.get("Matematicas") == "Matemáticas"

    def test_get_returns_none_for_unknown(self):
        assert NORMALIZACION_MATERIAS.get("Historia") is None

    def test_get_with_default_passthrough(self):
        assert NORMALIZACION_MATERIAS.get("Historia", "Historia") == "Historia"

    def test_all_normalized_names_different_from_originals(self):
        for original, normalized in NORMALIZACION_MATERIAS.items():
            assert original != normalized, f"{original} should differ from its normalized form"
