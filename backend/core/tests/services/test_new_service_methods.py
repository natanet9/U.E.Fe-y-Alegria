from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from core.services.activity_service import ActivityService
from core.services.attendance_service import AttendanceService
from core.services.audit_service import AuditService
from core.services.catalog_service import CatalogService
from core.services.course_service import CourseService
from core.services.dimension_config_service import DimensionConfigService
from core.services.estudiante_tutor_service import EstudianteTutorService
from core.services.inscripciones_service import InscripcionesService
from core.services.license_service import LicenseService
from core.services.periodo_service import PeriodoService
from core.services.reports_service import ReportsService
from core.services.schedule_service import ScheduleService
from core.services.tutores_service import TutoresService


# ── User fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin",
                           email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


@pytest.fixture
def director_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Director",
                           email="dir@test.com",
                           rol=SimpleNamespace(nombre="director"))


@pytest.fixture
def docente_user():
    return SimpleNamespace(id=2, activo=True, nombre_completo="Docente",
                           email="doc@test.com",
                           rol=SimpleNamespace(nombre="docente"))


# ── Service fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def activity_service():
    return ActivityService()


@pytest.fixture
def course_service():
    return CourseService()


@pytest.fixture
def license_service():
    return LicenseService()


@pytest.fixture
def periodo_service():
    return PeriodoService()


@pytest.fixture
def inscripciones_service():
    return InscripcionesService()


@pytest.fixture
def tutores_service():
    return TutoresService()


@pytest.fixture
def estudiante_tutor_service():
    return EstudianteTutorService()


@pytest.fixture
def catalog_service():
    return CatalogService()


@pytest.fixture
def dimension_config_service():
    return DimensionConfigService()


@pytest.fixture
def schedule_service():
    return ScheduleService()


@pytest.fixture
def attendance_service():
    return AttendanceService()


@pytest.fixture
def audit_service():
    return AuditService()


@pytest.fixture
def reports_service():
    return ReportsService()


# ═══════════════════════════════════════════════════════════════════════════
# ActivityService.new methods
# ═══════════════════════════════════════════════════════════════════════════

class TestActivityServiceNewMethods:

    def test_obtener_actividad_success(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=True):
            with patch('core.services.activity_service.Actividades.objects') as mock_objects:
                mock_objects.select_related.return_value.get.return_value = SimpleNamespace(
                    id=1, docente_asignacion_id=10, periodo_id=5, dimension_id=3,
                    nombre="Examen", descripcion="Desc", puntaje_maximo=20,
                    fecha_actividad=date(2026, 2, 15), activo=True,
                )
                result = activity_service.obtener_actividad(admin_user, 1)
        assert result['id'] == 1
        assert result['nombre'] == "Examen"
        assert result['docente_asignacion_id'] == 10
        assert result['activo'] is True

    def test_obtener_actividad_permission_error(self, activity_service, docente_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=False):
            with pytest.raises(PermissionError):
                activity_service.obtener_actividad(docente_user, 1)

    def test_obtener_actividad_not_found(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=True):
            with patch('core.services.activity_service.Actividades.objects') as mock_objects:
                mock_objects.select_related.return_value.get.side_effect = (
                    __import__('core.models', fromlist=['Actividades']).Actividades.DoesNotExist
                )
                with pytest.raises(__import__('core.models', fromlist=['Actividades']).Actividades.DoesNotExist):
                    activity_service.obtener_actividad(admin_user, 999)

    def test_actualizar_actividad_success(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas_libremente', return_value=True):
            with patch.object(activity_service.audit, 'record_actividad_change', return_value=None):
                with patch('core.services.activity_service.Actividades.objects') as mock_objects:
                    actividad = SimpleNamespace(
                        id=1, docente_asignacion_id=10, nombre="Antes",
                        descripcion="", puntaje_maximo=10,
                        fecha_actividad=date(2026, 2, 15), save=lambda: None,
                    )
                    mock_objects.select_related.return_value.get.return_value = actividad
                    result = activity_service.actualizar_actividad(admin_user, 1, {
                        'nombre': 'Despues', 'puntaje_maximo': 15,
                    })
        assert result['nombre'] == 'Despues'

    def test_actualizar_actividad_permission_error(self, activity_service, docente_user):
        with patch.object(activity_service.ac, 'puede_editar_notas_libremente', return_value=False):
            with pytest.raises(PermissionError):
                activity_service.actualizar_actividad(docente_user, 1, {'nombre': 'X'})

    def test_actualizar_actividad_value_error(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas_libremente', return_value=True):
            with patch('core.services.activity_service.Actividades.objects') as mock_objects:
                actividad = SimpleNamespace(
                    id=1, docente_asignacion_id=10, nombre="A",
                    descripcion="", puntaje_maximo=10,
                    fecha_actividad=date(2026, 2, 15), save=lambda: None,
                )
                mock_objects.select_related.return_value.get.return_value = actividad
                with pytest.raises(ValueError):
                    activity_service.actualizar_actividad(admin_user, 1, {'puntaje_maximo': -5})

    def test_obtener_nota_success(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=True):
            with patch('core.services.activity_service.ActividadNotas.objects') as mock_objects:
                now = datetime(2026, 3, 1, 10, 0, 0)
                mock_objects.select_related.return_value.get.return_value = SimpleNamespace(
                    id=1, actividad_id=5,
                    actividad=SimpleNamespace(docente_asignacion_id=10, nombre="Act1"),
                    estudiante_id=100, estudiante=SimpleNamespace(
                        nombres="Juan", primer_apellido="Perez",
                    ),
                    valor=8.5, registrado_en=now,
                )
                result = activity_service.obtener_nota(admin_user, 1)
        assert result['id'] == 1
        assert result['actividad_id'] == 5
        assert result['valor'] == 8.5

    def test_obtener_nota_permission_error(self, activity_service, docente_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=False):
            with pytest.raises(PermissionError):
                activity_service.obtener_nota(docente_user, 1)

    def test_obtener_nota_not_found(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=True):
            with patch('core.services.activity_service.ActividadNotas.objects') as mock_objects:
                mock_objects.select_related.return_value.get.side_effect = (
                    __import__('core.models', fromlist=['ActividadNotas']).ActividadNotas.DoesNotExist
                )
                with pytest.raises(__import__('core.models', fromlist=['ActividadNotas']).ActividadNotas.DoesNotExist):
                    activity_service.obtener_nota(admin_user, 999)

    def test_eliminar_nota_success(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=True):
            with patch.object(activity_service.ac, 'puede_editar_notas_libremente', return_value=True):
                with patch.object(activity_service.audit, 'record', return_value=None):
                    with patch('core.services.activity_service.ActividadNotas.objects') as mock_objects:
                        nota = MagicMock(
                            id=1, actividad_id=5, valor=8.5,
                            actividad=MagicMock(docente_asignacion_id=10),
                        )
                        mock_objects.select_related.return_value.get.return_value = nota
                        result = activity_service.eliminar_nota(admin_user, 1)
        assert result['mensaje'] == 'Nota eliminada'
        nota.save.assert_called_once_with(update_fields=['activo'])

    def test_eliminar_nota_permission_error(self, activity_service, docente_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=False):
            with pytest.raises(PermissionError):
                activity_service.eliminar_nota(docente_user, 1)

    def test_eliminar_nota_not_found(self, activity_service, admin_user):
        with patch.object(activity_service.ac, 'puede_editar_notas', return_value=True):
            with patch('core.services.activity_service.ActividadNotas.objects') as mock_objects:
                mock_objects.select_related.return_value.get.side_effect = (
                    __import__('core.models', fromlist=['ActividadNotas']).ActividadNotas.DoesNotExist
                )
                with pytest.raises(__import__('core.models', fromlist=['ActividadNotas']).ActividadNotas.DoesNotExist):
                    activity_service.eliminar_nota(admin_user, 999)


# ═══════════════════════════════════════════════════════════════════════════
# CourseService new methods
# ═══════════════════════════════════════════════════════════════════════════

class TestCourseServiceNewMethods:

    def test_actualizar_asignacion_success(self, course_service, admin_user):
        with patch.object(course_service.ac, 'puede_editar_notas', return_value=True):
            with patch.object(course_service.audit, 'record', return_value=None):
                with patch('core.services.course_service.DocenteAsignacion.objects') as mock_da:
                    da = SimpleNamespace(
                        id=1, docente_id=None, curso_id=1, area_id=1, activo=True,
                        usuario=SimpleNamespace(nombre_completo="Doc"),
                        curso=SimpleNamespace(__str__=lambda s: "1ro A"),
                        area=SimpleNamespace(nombre="Matematica"),
                        docente=None, gestion=2026, save=lambda: None,
                    )
                    mock_da.get.return_value = da
                    result = course_service.actualizar_asignacion(admin_user, 1, {'gestion': 2027})
        assert result['id'] == 1
        assert result['gestion'] == 2027

    def test_actualizar_asignacion_permission_error(self, course_service, docente_user):
        with patch.object(course_service.ac, 'puede_editar_notas', return_value=False):
            with pytest.raises(PermissionError):
                course_service.actualizar_asignacion(docente_user, 1, {})

    def test_restaurar_success(self, course_service, admin_user):
        with patch.object(course_service.ac, 'puede_editar_notas', return_value=True):
            with patch.object(course_service.audit, 'record', return_value=None):
                with patch('core.services.course_service.DocenteAsignacion.objects') as mock_da:
                    da = SimpleNamespace(
                        id=1, activo=False, docente_id=None, curso_id=1, area_id=1,
                        usuario=SimpleNamespace(id=10, nombre_completo="Doc"),
                        curso=SimpleNamespace(__str__=lambda s: "1ro A"),
                        area=SimpleNamespace(nombre="Matematica"),
                        docente=SimpleNamespace(usuario=SimpleNamespace(id=10, nombre_completo="Doc")),
                        gestion=2026, save=lambda self=None, **kw: None,
                    )
                    mock_da.get.return_value = da
                    result = course_service.restaurar(admin_user, 1)
        assert result['id'] == 1
        assert da.activo is True

    def test_restaurar_permission_error(self, course_service, docente_user):
        with patch.object(course_service.ac, 'puede_editar_notas', return_value=False):
            with pytest.raises(PermissionError):
                course_service.restaurar(docente_user, 1)


# ═══════════════════════════════════════════════════════════════════════════
# LicenseService new methods
# ═══════════════════════════════════════════════════════════════════════════

class TestLicenseServiceNewMethods:

    def test_obtener_success(self, license_service, admin_user):
        with patch.object(license_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.license_service.Licencias.objects') as mock_objects:
                mock_objects.select_related.return_value.get.return_value = SimpleNamespace(
                    id=1, estudiante_id=10,
                    estudiante=SimpleNamespace(nombres="Juan", primer_apellido="Perez"),
                    tutor_solicitante_id=20, motivo="Enfermedad",
                    fecha_inicio=date(2026, 5, 1), fecha_fin=date(2026, 5, 3),
                    requiere_respaldo=False, respaldo_presentado=False,
                    estado="pendiente", observaciones="",
                )
                result = license_service.obtener(admin_user, 1)
        assert result['id'] == 1
        assert result['motivo'] == "Enfermedad"

    def test_obtener_permission_error(self, license_service, docente_user):
        with patch.object(license_service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                license_service.obtener(docente_user, 1)

    def test_obtener_not_found(self, license_service, admin_user):
        with patch.object(license_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.license_service.Licencias.objects') as mock_objects:
                mock_objects.select_related.return_value.get.side_effect = (
                    __import__('core.models', fromlist=['Licencias']).Licencias.DoesNotExist
                )
                with pytest.raises(__import__('core.models', fromlist=['Licencias']).Licencias.DoesNotExist):
                    license_service.obtener(admin_user, 999)

    def test_actualizar_success(self, license_service, admin_user):
        with patch.object(license_service.ac, 'puede_gestionar_licencias', return_value=True):
            with patch.object(license_service.audit, 'record_licencia_change', return_value=None):
                with patch('core.services.license_service.Licencias.objects') as mock_objects:
                    lic = SimpleNamespace(id=1, motivo="Viejo", save=lambda: None)
                    mock_objects.get.return_value = lic
                    result = license_service.actualizar(admin_user, 1, {'motivo': 'Nuevo'})
        assert result['id'] == 1
        assert lic.motivo == 'Nuevo'

    def test_actualizar_permission_error(self, license_service, docente_user):
        with patch.object(license_service.ac, 'puede_gestionar_licencias', return_value=False):
            with pytest.raises(PermissionError):
                license_service.actualizar(docente_user, 1, {})

    def test_eliminar_success(self, license_service, admin_user):
        with patch.object(license_service.ac, 'puede_gestionar_licencias', return_value=True):
            with patch.object(license_service.audit, 'record_licencia_change', return_value=None):
                with patch('core.services.license_service.Licencias.objects') as mock_objects:
                    lic = MagicMock(id=1, motivo="Test")
                    mock_objects.get.return_value = lic
                    result = license_service.eliminar(admin_user, 1)
        assert result['mensaje'] == 'Licencia eliminada'
        lic.save.assert_called_once_with(update_fields=['activo'])

    def test_eliminar_permission_error(self, license_service, docente_user):
        with patch.object(license_service.ac, 'puede_gestionar_licencias', return_value=False):
            with pytest.raises(PermissionError):
                license_service.eliminar(docente_user, 1)


# ═══════════════════════════════════════════════════════════════════════════
# PeriodoService new methods
# ═══════════════════════════════════════════════════════════════════════════

class TestPeriodoServiceNewMethods:

    def test_obtener_success(self, periodo_service, director_user):
        with patch.object(periodo_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects') as mock_objects:
                mock_objects.get.return_value = SimpleNamespace(
                    id=1, nombre="Trimestre 1", gestion=2026, estado="activo", numero=1,
                    fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 3, 31),
                    marcado_como_enviado=False,
                    habilitado_por=None, cerrado_por=None,
                    enviado_por=None, enviado_en=None,
                )
                result = periodo_service.obtener(director_user, 1)
        assert result['id'] == 1
        assert result['nombre'] == "Trimestre 1"

    def test_obtener_permission_error(self, periodo_service, docente_user):
        with patch.object(periodo_service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                periodo_service.obtener(docente_user, 1)

    def test_obtener_not_found(self, periodo_service, director_user):
        with patch.object(periodo_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.periodo_service.Periodos.objects') as mock_objects:
                mock_objects.get.side_effect = (
                    __import__('core.models', fromlist=['Periodos']).Periodos.DoesNotExist
                )
                with pytest.raises(__import__('core.models', fromlist=['Periodos']).Periodos.DoesNotExist):
                    periodo_service.obtener(director_user, 999)

    def test_actualizar_success(self, periodo_service, director_user):
        with patch.object(periodo_service.ac, 'puede_habilitar_periodo', return_value=True):
            with patch.object(periodo_service.audit, 'record', return_value=None):
                with patch('core.services.periodo_service.Periodos.objects') as mock_objects:
                    periodo = SimpleNamespace(
                        id=1, nombre="Viejo", gestion=2026, estado="pendiente", numero=1,
                        fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 3, 31),
                        marcado_como_enviado=False,
                        habilitado_por=None, cerrado_por=None,
                        enviado_por=None, enviado_en=None,
                        save=lambda: None,
                    )
                    mock_objects.get.return_value = periodo
                    result = periodo_service.actualizar(director_user, 1, {'nombre': 'Nuevo', 'gestion': 2027})
        assert result['nombre'] == 'Nuevo'
        assert result['gestion'] == 2027

    def test_actualizar_permission_error(self, periodo_service, docente_user):
        with patch.object(periodo_service.ac, 'puede_habilitar_periodo', return_value=False):
            with pytest.raises(PermissionError):
                periodo_service.actualizar(docente_user, 1, {})

    def test_eliminar_success(self, periodo_service, director_user):
        with patch.object(periodo_service.ac, 'puede_habilitar_periodo', return_value=True):
            with patch.object(periodo_service.audit, 'record', return_value=None):
                with patch('core.services.periodo_service.Periodos.objects') as mock_objects:
                    result = periodo_service.eliminar(director_user, 1)
        assert result['mensaje'] == 'Periodo eliminado'
        mock_objects.filter.assert_called_once_with(id=1)
        mock_objects.filter.return_value.update.assert_called_once_with(activo=False)

    def test_eliminar_permission_error(self, periodo_service, docente_user):
        with patch.object(periodo_service.ac, 'puede_habilitar_periodo', return_value=False):
            with pytest.raises(PermissionError):
                periodo_service.eliminar(docente_user, 1)


# ═══════════════════════════════════════════════════════════════════════════
# InscripcionesService new methods
# ═══════════════════════════════════════════════════════════════════════════

class TestInscripcionesServiceNewMethods:

    def test_obtener_success(self, inscripciones_service, admin_user):
        with patch.object(inscripciones_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.inscripciones_service.Inscripciones.objects') as mock_objects:
                mock_objects.select_related.return_value.get.return_value = SimpleNamespace(
                    id=1, estudiante_id=10,
                    estudiante=SimpleNamespace(nombres="Juan", primer_apellido="Perez"),
                    curso_id=5, curso=SimpleNamespace(__str__=lambda s: "1ro A"),
                    gestion=2026, fecha_inscripcion=date(2026, 2, 1), estado="activo",
                )
                result = inscripciones_service.obtener(admin_user, 1)
        assert result['id'] == 1
        assert result['estudiante_id'] == 10
        assert result['estado'] == "activo"

    def test_actualizar_estado_success(self, inscripciones_service, admin_user):
        with patch.object(inscripciones_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(inscripciones_service.audit, 'record_inscripcion_change', return_value=None):
                with patch('core.services.inscripciones_service.Inscripciones.objects') as mock_objects:
                    ins = SimpleNamespace(id=1, estado="activo", save=lambda **kw: None)
                    mock_objects.get.return_value = ins
                    result = inscripciones_service.actualizar_estado(admin_user, 1, "retirado")
        assert result['estado'] == "retirado"

    def test_actualizar_estado_value_error(self, inscripciones_service, admin_user):
        with patch.object(inscripciones_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with pytest.raises(ValueError):
                inscripciones_service.actualizar_estado(admin_user, 1, "invalido")


# ═══════════════════════════════════════════════════════════════════════════
# TutoresService all methods
# ═══════════════════════════════════════════════════════════════════════════

class TestTutoresService:

    def test_listar_success(self, tutores_service, admin_user):
        with patch.object(tutores_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.tutores_service.Tutores.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.count.return_value = 1
                mock_qs.__getitem__.return_value = [
                    SimpleNamespace(
                        id=1, ci="12345678", tipo_documento="CI",
                        primer_apellido="Perez", segundo_apellido="",
                        nombres="Juan", parentesco="Padre", celular="77700000",
                        idioma_frecuente="Español",
                        fecha_nacimiento=date(1980, 1, 1), activo=True,
                    ),
                ]
                mock_objects.all.return_value.order_by.return_value = mock_qs
                result = tutores_service.listar(admin_user)
        assert len(result['data']) == 1
        assert result['data'][0]['ci'] == "12345678"

    def test_crear_success(self, tutores_service, admin_user):
        with patch.object(tutores_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(tutores_service.audit, 'record', return_value=None):
                with patch('core.services.tutores_service.Tutores.objects') as mock_objects:
                    mock_objects.create.return_value = SimpleNamespace(id=1)
                    result = tutores_service.crear(admin_user, {
                        'ci': '12345678', 'nombres': 'Juan', 'primer_apellido': 'Perez',
                    })
        assert result['id'] == 1

    def test_obtener_success(self, tutores_service, admin_user):
        with patch.object(tutores_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.tutores_service.Tutores.objects') as mock_objects:
                mock_objects.get.return_value = SimpleNamespace(
                    id=1, ci="12345678", tipo_documento="CI",
                    primer_apellido="Perez", segundo_apellido="",
                    nombres="Juan", parentesco="Padre", celular="77700000",
                    idioma_frecuente="Español",
                    fecha_nacimiento=date(1980, 1, 1), activo=True,
                )
                result = tutores_service.obtener(admin_user, 1)
        assert result['id'] == 1
        assert result['ci'] == "12345678"

    def test_actualizar_success(self, tutores_service, admin_user):
        with patch.object(tutores_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(tutores_service.audit, 'record', return_value=None):
                with patch('core.services.tutores_service.Tutores.objects') as mock_objects:
                    tutor = SimpleNamespace(id=1, ci="12345678", nombres="Antes", save=lambda: None)
                    mock_objects.get.return_value = tutor
                    result = tutores_service.actualizar(admin_user, 1, {'nombres': 'Despues'})
        assert result['id'] == 1
        assert tutor.nombres == 'Despues'

    def test_eliminar_success(self, tutores_service, admin_user):
        with patch.object(tutores_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(tutores_service.audit, 'record', return_value=None):
                with patch('core.services.tutores_service.Tutores.objects') as mock_objects:
                    tutor = SimpleNamespace(id=1, activo=True, save=lambda **kw: None)
                    mock_objects.get.return_value = tutor
                    result = tutores_service.eliminar(admin_user, 1)
        assert result['mensaje'] == 'Tutor eliminado'
        assert tutor.activo is False


# ═══════════════════════════════════════════════════════════════════════════
# EstudianteTutorService all methods
# ═══════════════════════════════════════════════════════════════════════════

class TestEstudianteTutorService:

    def test_listar_success(self, estudiante_tutor_service, admin_user):
        with patch.object(estudiante_tutor_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.estudiante_tutor_service.EstudianteTutor.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.order_by.return_value = [
                    SimpleNamespace(
                        id=1, estudiante_id=10,
                        estudiante=SimpleNamespace(__str__=lambda s: "Juan Perez"),
                        tutor_id=20,
                        tutor=SimpleNamespace(__str__=lambda s: "Carlos Perez"),
                        es_principal=True,
                    ),
                ]
                mock_objects.select_related.return_value.filter.return_value = mock_qs
                result = estudiante_tutor_service.listar(admin_user)
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['es_principal'] is True

    def test_crear_success(self, estudiante_tutor_service, admin_user):
        with patch.object(estudiante_tutor_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(estudiante_tutor_service.audit, 'record', return_value=None):
                with patch('core.services.estudiante_tutor_service.EstudianteTutor.objects') as mock_objects:
                    mock_objects.get_or_create.return_value = (SimpleNamespace(id=1), True)
                    result = estudiante_tutor_service.crear(admin_user, {
                        'estudiante_id': 10, 'tutor_id': 20,
                    })
        assert result['id'] == 1

    def test_eliminar_success(self, estudiante_tutor_service, admin_user):
        with patch.object(estudiante_tutor_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(estudiante_tutor_service.audit, 'record', return_value=None):
                with patch('core.services.estudiante_tutor_service.EstudianteTutor.objects') as mock_objects:
                    et = MagicMock(id=1)
                    mock_objects.get.return_value = et
                    result = estudiante_tutor_service.eliminar(admin_user, 1)
        assert result['mensaje'] == 'Relacion eliminada'
        et.save.assert_called_once_with(update_fields=['activo'])


# ═══════════════════════════════════════════════════════════════════════════
# CatalogService listar_* methods
# ═══════════════════════════════════════════════════════════════════════════

class TestCatalogService:

    def _make_mock_qs(self, items):
        qs = MagicMock()
        qs.count.return_value = len(items)
        qs.__getitem__.return_value = items
        qs.filter.return_value = qs
        return qs

    def test_listar_niveles_success(self, catalog_service, admin_user):
        with patch.object(catalog_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Niveles.objects') as mock_objects:
                mock_objects.all.return_value.order_by.return_value = self._make_mock_qs([
                    SimpleNamespace(id=1, nombre="Inicial"),
                    SimpleNamespace(id=2, nombre="Primaria"),
                ])
                result = catalog_service.listar_niveles(admin_user)
        assert result['total'] == 2
        assert len(result['data']) == 2

    def test_listar_grados_success(self, catalog_service, admin_user):
        with patch.object(catalog_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Grados.objects') as mock_objects:
                mock_objects.select_related.return_value.all.return_value.order_by.return_value = self._make_mock_qs([
                    SimpleNamespace(id=1, nombre="Primero", numero=1, nivel_id=1,
                                    nivel=SimpleNamespace(nombre="Primaria")),
                ])
                result = catalog_service.listar_grados(admin_user)
        assert result['total'] == 1

    def test_listar_paralelos_success(self, catalog_service, admin_user):
        with patch.object(catalog_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Paralelos.objects') as mock_objects:
                mock_objects.all.return_value.order_by.return_value = self._make_mock_qs([
                    SimpleNamespace(id=1, nombre="A"),
                ])
                result = catalog_service.listar_paralelos(admin_user)
        assert result['total'] == 1

    def test_listar_cursos_success(self, catalog_service, admin_user):
        with patch.object(catalog_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Cursos.objects') as mock_objects:
                mock_objects.select_related.return_value.all.return_value.order_by.return_value = self._make_mock_qs([
                    SimpleNamespace(id=1, grado_id=1, paralelo_id=1,
                                    grado=SimpleNamespace(__str__=lambda s: "1ro"),
                                    paralelo=SimpleNamespace(nombre="A"),
                                    __str__=lambda s: "1ro A"),
                ])
                result = catalog_service.listar_cursos(admin_user)
        assert result['total'] == 1

    def test_listar_areas_success(self, catalog_service, admin_user):
        with patch.object(catalog_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.Areas.objects') as mock_objects:
                mock_objects.all.return_value.order_by.return_value = self._make_mock_qs([
                    SimpleNamespace(id=1, nombre="Matematica"),
                ])
                result = catalog_service.listar_areas(admin_user)
        assert result['total'] == 1

    def test_listar_dimensiones_success(self, catalog_service, admin_user):
        with patch.object(catalog_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.catalog_service.DimensionesEvaluacion.objects') as mock_objects:
                mock_objects.all.return_value.order_by.return_value = self._make_mock_qs([
                    SimpleNamespace(id=1, nombre="SABER", orden=1, gestion=2026),
                ])
                result = catalog_service.listar_dimensiones(admin_user)
        assert result['total'] == 1
        assert result['data'][0]['orden'] == 1


# ═══════════════════════════════════════════════════════════════════════════
# DimensionConfigService
# ═══════════════════════════════════════════════════════════════════════════

class TestDimensionConfigService:

    def _make_mock_qs(self, items):
        qs = MagicMock()
        qs.count.return_value = len(items)
        qs.__getitem__.return_value = items
        qs.filter.return_value = qs
        return qs

    def test_listar_success(self, dimension_config_service, admin_user):
        with patch.object(dimension_config_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.dimension_config_service.DimensionConfigPeriodo.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.order_by.return_value = [
                    SimpleNamespace(
                        id=1, periodo_id=1, dimension_id=1, puntaje_maximo=100,
                        periodo=SimpleNamespace(__str__=lambda s: "T1 2026"),
                        dimension=SimpleNamespace(nombre="SABER"),
                    ),
                ]
                mock_objects.select_related.return_value.all.return_value = mock_qs
                result = dimension_config_service.listar(admin_user)
        assert len(result) == 1
        assert result[0]['puntaje_maximo'] == 100.0

    def test_crear_success(self, dimension_config_service, admin_user):
        with patch.object(dimension_config_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(dimension_config_service.audit, 'record', return_value=None):
                with patch('core.services.dimension_config_service.DimensionConfigPeriodo.objects') as mock_objects:
                    mock_objects.create.return_value = SimpleNamespace(
                        id=1, periodo_id=1, dimension_id=1, puntaje_maximo=100,
                    )
                    result = dimension_config_service.crear(admin_user, {
                        'periodo_id': 1, 'dimension_id': 1, 'puntaje_maximo': 100,
                    })
        assert result['id'] == 1

    def test_actualizar_success(self, dimension_config_service, admin_user):
        with patch.object(dimension_config_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(dimension_config_service.audit, 'record', return_value=None):
                with patch('core.services.dimension_config_service.DimensionConfigPeriodo.objects') as mock_objects:
                    config = SimpleNamespace(
                        id=1, periodo_id=1, dimension_id=1, puntaje_maximo=50, save=lambda: None,
                    )
                    mock_objects.get.return_value = config
                    result = dimension_config_service.actualizar(admin_user, 1, {'puntaje_maximo': 80})
        assert result['puntaje_maximo'] == 80.0

    def test_eliminar_success(self, dimension_config_service, admin_user):
        with patch.object(dimension_config_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch.object(dimension_config_service.audit, 'record', return_value=None):
                with patch('core.services.dimension_config_service.DimensionConfigPeriodo.objects') as mock_objects:
                    mock_objects.filter.return_value.delete.return_value = None
                    result = dimension_config_service.eliminar(admin_user, 1)
        assert result['mensaje'] == 'Configuracion eliminada'


# ═══════════════════════════════════════════════════════════════════════════
# ScheduleService.eliminar_horario
# ═══════════════════════════════════════════════════════════════════════════

class TestScheduleServiceNewMethods:

    def test_eliminar_horario_success(self, schedule_service, admin_user):
        with patch.object(schedule_service.ac, 'puede_ver_todo', return_value=True):
            with patch.object(schedule_service.audit, 'record', return_value=None):
                with patch('core.services.schedule_service.Horarios.objects') as mock_objects:
                    schedule_service.eliminar_horario(admin_user, 1)
                mock_objects.filter.assert_called_once_with(id=1)
                mock_objects.filter.return_value.update.assert_called_once_with(activo=False)

    def test_eliminar_horario_permission_error(self, schedule_service, docente_user):
        with patch.object(schedule_service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                schedule_service.eliminar_horario(docente_user, 1)


# ═══════════════════════════════════════════════════════════════════════════
# AttendanceService.listar_asistencias_admin
# ═══════════════════════════════════════════════════════════════════════════

class TestAttendanceServiceNewMethods:

    def test_listar_asistencias_admin_success(self, attendance_service, admin_user):
        with patch.object(attendance_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.attendance_service.Asistencias.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.count.return_value = 0
                mock_qs.__getitem__.return_value = []
                mock_objects.filter.return_value.select_related.return_value = mock_qs
                result = attendance_service.listar_asistencias_admin(admin_user)
        assert result['total'] == 0
        assert result['data'] == []

    def test_listar_asistencias_admin_permission_error(self, attendance_service, docente_user):
        with patch.object(attendance_service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                attendance_service.listar_asistencias_admin(docente_user)


# ═══════════════════════════════════════════════════════════════════════════
# AuditService.listar
# ═══════════════════════════════════════════════════════════════════════════

class TestAuditServiceNewMethods:

    def test_listar_success(self):
        service = AuditService()
        with patch('core.services.audit_service.AccessControlService') as mock_ac_cls:
            mock_ac_cls.return_value.puede_ver_auditoria.return_value = True
            with patch('core.services.audit_service.AuditLog.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.count.return_value = 1
                mock_qs.__getitem__.return_value = [
                    SimpleNamespace(
                        id=1, tabla="actividades", registro_id=1, accion="CREATE",
                        datos_anterior=None, datos_nuevo={'nombre': 'Test'},
                        usuario=SimpleNamespace(nombre_completo="Admin"),
                        fecha_cambio=datetime(2026, 1, 1, 12, 0, 0),
                    ),
                ]
                mock_qs.filter.return_value = mock_qs
                mock_objects.select_related.return_value.all.return_value.order_by.return_value = (
                    mock_qs
                )
                admin = SimpleNamespace(id=1, nombre_completo="Admin")
                result = service.listar(admin)
        assert result['total'] == 1

    def test_listar_permission_error(self):
        service = AuditService()
        with patch('core.services.audit_service.AccessControlService') as mock_ac_cls:
            mock_ac_cls.return_value.puede_ver_auditoria.return_value = False
            admin = SimpleNamespace(id=1, nombre_completo="Admin")
            with pytest.raises(PermissionError):
                service.listar(admin)

    def test_historial_nota_success(self):
        service = AuditService()
        with patch('core.services.audit_service.AccessControlService') as mock_ac_cls:
            mock_ac_cls.return_value.puede_ver_auditoria.return_value = True
            with patch('core.services.audit_service.AuditLog.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.__iter__.return_value = iter([
                    SimpleNamespace(
                        id=7,
                        accion='UPDATE',
                        datos_anterior={'valor': 70},
                        datos_nuevo={'valor': 80},
                        usuario=SimpleNamespace(nombre_completo='Admin'),
                        fecha_cambio=datetime(2026, 1, 1, 12, 0, 0),
                    ),
                ])
                mock_objects.filter.return_value.select_related.return_value.order_by.return_value = mock_qs
                admin = SimpleNamespace(id=1, nombre_completo='Admin', rol=SimpleNamespace(nombre='director'))
                result = service.historial_nota(admin, 1)

        assert result == [{
            'id': 7,
            'accion': 'UPDATE',
            'valor_anterior': {'valor': 70},
            'valor_nuevo': {'valor': 80},
            'usuario': 'Admin',
            'fecha': '2026-01-01T12:00:00',
        }]

    def test_historial_nota_permission_error(self):
        service = AuditService()
        with patch('core.services.audit_service.AccessControlService') as mock_ac_cls:
            mock_ac_cls.return_value.puede_ver_auditoria.return_value = False
            admin = SimpleNamespace(id=1, nombre_completo='Admin', rol=SimpleNamespace(nombre='tutor'))
            with pytest.raises(PermissionError):
                service.historial_nota(admin, 1)


# ═══════════════════════════════════════════════════════════════════════════
# ReportsService.get_export_history and get_audit_load_summary
# ═══════════════════════════════════════════════════════════════════════════

class TestReportsServiceNewMethods:

    def test_get_export_history_success(self, reports_service, admin_user):
        with patch.object(reports_service.ac, 'puede_exportar', return_value=True):
            with patch('core.services.reports_service.ExportEvent.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.count.return_value = 1
                export_entry = SimpleNamespace(
                    id=1, formato="xlsx", periodo_id=1,
                    docente_asignacion_id=10,
                    periodo=SimpleNamespace(nombre="T1", gestion=2026),
                    usuario=SimpleNamespace(nombre_completo="Admin"),
                    creado_en=datetime(2026, 1, 1, 12, 0, 0),
                    filtros={},
                )
                mock_qs.__getitem__.return_value = [export_entry]
                mock_qs.filter.return_value = mock_qs
                mock_objects.select_related.return_value.order_by.return_value = mock_qs
                result = reports_service.get_export_history(admin_user)
        assert result['total'] == 1
        assert len(result['exports']) == 1

    def test_get_audit_load_summary_success(self, reports_service, admin_user):
        with patch.object(reports_service.ac, 'puede_ver_auditoria', return_value=True):
            with patch('core.services.reports_service.AuditLog.objects') as mock_objects:
                mock_qs = MagicMock()
                mock_qs.count.return_value = 5
                mock_qs.filter.return_value = mock_qs
                mock_qs.values.return_value.annotate.return_value.order_by.return_value = [
                    {'usuario__nombre_completo': 'Admin', 'changes': 3},
                ]
                mock_objects.all.return_value = mock_qs
                result = reports_service.get_audit_load_summary(admin_user)
        assert result['total_changes'] == 5
        assert len(result['by_user']) == 1
