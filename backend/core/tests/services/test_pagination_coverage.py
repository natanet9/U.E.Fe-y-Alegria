import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from core.services.catalog_service import CatalogService
from core.services.inscripciones_service import InscripcionesService
from core.services.tutores_service import TutoresService
from core.services.schedule_service import ScheduleService
from core.services.periodo_service import PeriodoService
from core.services.attendance_service import AttendanceService
from core.services.activity_service import ActivityService


# These tests use mocked QuerySets to exercise the pagination code paths
# without needing real DB data. They ensure pagination branch coverage.


class MockQuerySet:
    """A minimal mock that behaves like a Django QuerySet for pagination."""
    def __init__(self, items=None):
        self.items = items or []
        self._ordered = True

    def count(self):
        return len(self.items)

    def order_by(self, *args):
        return self

    def select_related(self, *args):
        return self

    def all(self):
        return self

    def filter(self, **kwargs):
        if self.items:
            filtered = [x for x in self.items if all(getattr(x, k, None) == v for k, v in kwargs.items())]
        else:
            filtered = []
        return MockQuerySet(filtered)

    def __getitem__(self, s):
        if isinstance(s, slice):
            return self.items[s]
        return self.items[s]

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __bool__(self):
        return len(self.items) > 0


@pytest.fixture
def admin_user():
    from types import SimpleNamespace
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


# ── CatalogService pagination ──

class TestCatalogServicePagination:

    def test_listar_niveles_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, nombre=f"Nivel{i}") for i in range(1, 11)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Niveles.objects.all', return_value=mock_qs):
                result = service.listar_niveles(admin_user, page=1, page_size=5)
                assert result['total'] == 10
                assert result['total_pages'] == 2
                assert len(result['data']) == 5
                assert 'page' in result

    def test_listar_grados_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, nombre=f"Grado{i}", numero=i, nivel_id=1, nivel=MagicMock(nombre="Nivel")) for i in range(1, 11)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Grados.objects.select_related') as mock_sr:
                mock_sr.return_value.all.return_value = mock_qs
                result = service.listar_grados(admin_user, page=1, page_size=3)
                assert result['total'] == 10
                assert result['total_pages'] == 4
                assert len(result['data']) == 3

    def test_listar_grados_with_nivel_filter_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, nombre=f"Grado{i}", numero=i, nivel_id=1, nivel=MagicMock(nombre="Nivel")) for i in range(1, 6)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Grados.objects.select_related') as mock_sr:
                mock_sr.return_value.all.return_value = mock_qs
                result = service.listar_grados(admin_user, nivel_id=1, page=1, page_size=10)
                assert 'data' in result

    def test_listar_paralelos_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, nombre=f"Paralelo{i}") for i in range(1, 8)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Paralelos.objects.all', return_value=mock_qs):
                result = service.listar_paralelos(admin_user, page=2, page_size=3)
                assert result['total'] == 7
                assert result['total_pages'] == 3
                assert result['page'] == 2

    def test_listar_cursos_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, grado_id=1, paralelo_id=1, grado=MagicMock(nombre="Grado"), paralelo=MagicMock(nombre="A"), __str__=lambda s: "Grado A") for i in range(1, 15)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Cursos.objects.select_related') as mock_sr:
                mock_sr.return_value.all.return_value = mock_qs
                result = service.listar_cursos(admin_user, page=1, page_size=10)
                assert result['total'] == 14

    def test_listar_areas_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, nombre=f"Area{i}") for i in range(1, 6)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Areas.objects.all', return_value=mock_qs):
                result = service.listar_areas(admin_user, page=1, page_size=2)
                assert result['total'] == 5

    def test_listar_dimensiones_paginated(self, admin_user):
        service = CatalogService()
        mock_qs = MockQuerySet([MagicMock(id=i, nombre=f"Dim{i}", orden=i, gestion=2026) for i in range(1, 10)])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.DimensionesEvaluacion.objects.all', return_value=mock_qs):
                result = service.listar_dimensiones(admin_user, page=1, page_size=4)
                assert result['total'] == 9


# ── InscripcionesService pagination ──

class TestInscripcionesServicePagination:

    def test_listar_paginated(self, admin_user):
        service = InscripcionesService()
        mock_items = []
        for i in range(1, 26):
            e = MagicMock(id=i, nombres=f"Nombre{i}", primer_apellido=f"Apellido{i}")
            c = MagicMock(id=1, grado=MagicMock(nombre="Grado"), paralelo=MagicMock(nombre="A"), __str__=lambda s: "Grado A")
            ins = MagicMock(id=i, estudiante=e, estudiante_id=i, curso=c, curso_id=1, gestion=2026, fecha_inscripcion="2026-01-15", estado="activo")
            mock_items.append(ins)
        mock_qs = MockQuerySet(mock_items)
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.inscripciones_service.Inscripciones.objects.select_related') as mock_sr:
                mock_sr.return_value.filter.return_value.order_by.return_value = mock_qs
                result = service.listar(admin_user, page=1, page_size=10)
                assert result['total'] == 25
                assert len(result['data']) == 10

    def test_listar_with_filters_paginated(self, admin_user):
        service = InscripcionesService()
        mock_qs = MockQuerySet([MagicMock(id=1, estudiante=MagicMock(id=1, nombres="A", primer_apellido="B"), estudiante_id=1, curso=MagicMock(id=1, grado=MagicMock(nombre="G"), paralelo=MagicMock(nombre="P"), __str__=lambda s: "G P"), curso_id=1, gestion=2026, fecha_inscripcion="2026-01-15", estado="activo")])
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.inscripciones_service.Inscripciones.objects.select_related') as mock_sr:
                mock_sr.return_value.filter.return_value.order_by.return_value = mock_qs
                result = service.listar(admin_user, curso_id=1, gestion=2026, estado="activo", page=1, page_size=20)
                assert 'data' in result


# ── TutoresService pagination ──

class TestTutoresServicePagination:

    def test_listar_paginated(self, admin_user):
        service = TutoresService()
        mock_items = [MagicMock(id=i, ci=f"{i:08d}", tipo_documento="CI", primer_apellido=f"Ap{i}", segundo_apellido="", nombres=f"Nom{i}", parentesco="Padre", celular="777", idioma_frecuente="ES", fecha_nacimiento=None, activo=True) for i in range(1, 21)]
        mock_qs = MockQuerySet(mock_items)
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.tutores_service.Tutores.objects.all', return_value=mock_qs):
                result = service.listar(admin_user, page=1, page_size=5)
                assert result['total'] == 20
                assert len(result['data']) == 5

    def test_listar_with_query_paginated(self, admin_user):
        service = TutoresService()
        mock_items = [MagicMock(id=1, ci="12345678", tipo_documento="CI", primer_apellido="Lopez", segundo_apellido="", nombres="Juan", parentesco="Padre", celular="777", idioma_frecuente="ES", fecha_nacimiento=None, activo=True)]
        mock_qs = MockQuerySet(mock_items)
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.tutores_service.Tutores.objects.all', return_value=mock_qs):
                result = service.listar(admin_user, query="Lopez", page=1, page_size=10)
                assert 'data' in result


# ── ScheduleService pagination ──

class TestScheduleServicePagination:

    def test_listar_horarios_paginated(self, admin_user):
        service = ScheduleService()
        mock_da_qs = MockQuerySet([MagicMock(id=i, curso_id=1, activo=True) for i in range(1, 6)])
        mock_horarios = []
        for i in range(1, 16):
            da = MagicMock(id=1, curso=MagicMock(id=1, grado=MagicMock(nombre="Grado", nivel=MagicMock(nombre="Nivel")), paralelo=MagicMock(nombre="A")), area=MagicMock(nombre="Mate"), usuario=MagicMock(nombre_completo="Doc"))
            h = MagicMock(id=i, docente_asignacion=da, dia_semana=1, hora_inicio="08:00", hora_fin="09:00", aula="A1")
            mock_horarios.append(h)
        mock_horarios_qs = MockQuerySet(mock_horarios)
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.schedule_service.DocenteAsignacion.objects.filter', return_value=mock_da_qs):
                with patch('core.services.schedule_service.Horarios.objects.select_related') as mock_sr:
                    mock_sr.return_value.filter.return_value.order_by.return_value = mock_horarios_qs
                    result = service.listar_horarios(admin_user, page=1, page_size=5)
                    assert result['total'] == 15
                    assert result['total_pages'] == 3


# ── PeriodoService pagination ──

class TestPeriodoServicePagination:

    def test_listar_paginated(self, admin_user):
        service = PeriodoService()
        mock_items = []
        for i in range(1, 20):
            p = MagicMock(id=i, nombre=f"Periodo{i}", gestion=2026, estado="pendiente", fecha_inicio="2026-01-01", fecha_fin="2026-12-31", marcado_como_enviado=False, enviado_por=None, enviado_en=None)
            mock_items.append(p)
        mock_qs = MockQuerySet(mock_items)
        with patch('core.services.periodo_service.Periodos.objects.all', return_value=mock_qs):
            result = service.listar(admin_user, page=1, page_size=5)
            assert result['total'] == 19
            assert len(result['data']) == 5

    def test_listar_with_gestion_filter_paginated(self, admin_user):
        service = PeriodoService()
        mock_qs = MockQuerySet([MagicMock(id=1, nombre="P1", gestion=2026, estado="activo", fecha_inicio="2026-01-01", fecha_fin="2026-12-31", marcado_como_enviado=False, enviado_por=None, enviado_en=None)])
        with patch('core.services.periodo_service.Periodos.objects.all', return_value=mock_qs):
            result = service.listar(admin_user, gestion=2026, page=1, page_size=10)
            assert 'data' in result


# ── AttendanceService pagination ──

class TestAttendanceServicePagination:

    def test_listar_asistencias_paginated(self, admin_user):
        service = AttendanceService()
        mock_estudiantes = MockQuerySet([MagicMock(estudiante=MagicMock(id=i, nombres=f"N{i}", primer_apellido=f"A{i}")) for i in range(1, 31)])
        with patch.object(service.ac, 'puede_editar_notas', return_value=True):
            with patch('core.services.attendance_service.DocenteAsignacion.objects.get') as mock_da_get:
                mock_da_get.return_value = MagicMock(id=1, curso=MagicMock(id=1), gestion=2026)
                with patch('core.services.attendance_service.Inscripciones.objects.filter') as mock_ins_filter:
                    mock_ins_filter.return_value.select_related.return_value = mock_estudiantes
                    with patch('core.services.attendance_service.Asistencias.objects.filter') as mock_asist:
                        mock_asist.return_value.first.return_value = SimpleNamespace(estado="presente")
                        result = service.listar_asistencias(admin_user, 1, fecha="2026-05-01", page=1, page_size=10)
                        assert result['total'] == 30
                        assert len(result['data']) == 10

    def test_listar_asistencias_admin_paginated(self, admin_user):
        service = AttendanceService()
        mock_items = []
        for i in range(1, 21):
            a = MagicMock(id=i, estudiante_id=i, estudiante=MagicMock(nombres=f"N{i}", primer_apellido=f"A{i}"), docente_asignacion_id=1, docente_asignacion=MagicMock(id=1, curso=MagicMock(__str__=lambda s: "Curso A"), area=MagicMock(nombre="Mate")), estado="presente")
            mock_items.append(a)
        mock_qs = MockQuerySet(mock_items)
        with patch.object(service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.attendance_service.Asistencias.objects.filter') as mock_filter:
                mock_filter.return_value.select_related.return_value = mock_qs
                result = service.listar_asistencias_admin(admin_user, fecha="2026-05-01", page=1, page_size=5)
                assert result['total'] == 20


# ── ActivityService pagination ──

class TestActivityServicePagination:

    def test_list_actividades_paginated(self, admin_user):
        service = ActivityService()
        mock_items = [MagicMock(id=i, nombre=f"Act{i}", descripcion="", puntaje_maximo=100, dimension_id=1, dimension=MagicMock(nombre="Dim"), periodo_id=1, fecha_actividad="2026-05-01", activo=True) for i in range(1, 13)]
        mock_qs = MockQuerySet(mock_items)
        with patch('core.services.activity_service.Actividades.objects.filter') as mock_filter:
            mock_filter.return_value.order_by.return_value = mock_qs
            result = service._list_actividades(1, page=1, page_size=5)
            assert result['total'] == 12
            assert len(result['data']) == 5
