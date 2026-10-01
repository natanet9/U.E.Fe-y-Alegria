from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from core.services.students_service import StudentsService
from core.services.enrollment_service import EnrollmentService
from core.services.periodo_service import PeriodoService
from core.services.config_service import ConfigService


@pytest.fixture
def admin_user():
    return SimpleNamespace(id=1, activo=True, nombre_completo="Admin", email="admin@test.com",
                           rol=SimpleNamespace(nombre="secretaria"))


@pytest.fixture
def students_service():
    return StudentsService()


@pytest.fixture
def enrollment_service():
    return EnrollmentService()


@pytest.fixture
def periodo_service():
    return PeriodoService()


class TestStudentsServiceHistory:

    def test_historial_academico_success(self, students_service, admin_user):
        with patch.object(students_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.students_service.Estudiantes.objects.get') as mock_get:
                mock_get.return_value = SimpleNamespace(
                    id=1, rude="R001", ci="123", nombres="Test", primer_apellido="Student",
                    segundo_apellido="", fecha_nacimiento=None, genero="M",
                    pais_nacimiento="Bolivia", tiene_discapacidad=False, tipo_discapacidad="",
                    tiene_tea=False, dificultad_aprendizaje="", estado="activo",
                )
                with patch('core.services.students_service.Inscripciones.objects.filter') as mock_ins:
                    mock_ins.return_value.select_related.return_value.order_by.return_value = []
                    with patch('core.services.students_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.select_related.return_value.order_by.return_value = []
                        with patch('core.services.students_service.NotaObservaciones.objects.filter') as mock_obs:
                            mock_obs.return_value.select_related.return_value.order_by.return_value = []
                            with patch('core.services.students_service.Asistencias.objects.filter') as mock_asist:
                                mock_asist.return_value.select_related.return_value.order_by.return_value = []
                                result = students_service.historial_academico(admin_user, 1)
                                assert result['id'] == 1
                                assert 'inscripciones' in result
                                assert 'actividades' in result

    def test_historial_academico_permission_error(self, students_service, admin_user):
        with patch.object(students_service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                students_service.historial_academico(admin_user, 1)

    def test_historial_academico_not_found(self, students_service, admin_user):
        with patch.object(students_service.ac, 'puede_ver_todo', return_value=True):
            from core.models import Estudiantes
            with patch('core.services.students_service.Estudiantes.objects.get', side_effect=Estudiantes.DoesNotExist):
                with pytest.raises(Estudiantes.DoesNotExist):
                    students_service.historial_academico(admin_user, 999)


class TestEnrollmentServicePromote:

    def test_promocionar_success(self, enrollment_service, admin_user):
        with patch.object(enrollment_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch('core.services.enrollment_service.Inscripciones.objects.filter') as mock_filter:
                mock_exists = MagicMock()
                mock_exists.exists.return_value = True
                mock_filter.return_value = mock_exists

                mock_insc = MagicMock()
                mock_insc.estudiante = SimpleNamespace(id=1)
                mock_insc.id = 10
                mock_filter.return_value.select_related.return_value = [mock_insc]

                with patch('core.services.enrollment_service.Cursos.objects.get') as mock_curso:
                    mock_curso.return_value = SimpleNamespace(id=1, __str__=lambda s: "Curso Test")
                    with patch('core.services.enrollment_service.Inscripciones.objects.create'):
                        with patch.object(enrollment_service.audit, 'record_inscripcion_change'):
                            result = enrollment_service.promocionar_estudiantes(admin_user, 1, 2, 2025, 2026)
                            assert result['promocionados'] == 1

    def test_promocionar_permission_error(self, enrollment_service, admin_user):
        with patch.object(enrollment_service.ac, 'puede_gestionar_inscripciones', return_value=False):
            with pytest.raises(PermissionError):
                enrollment_service.promocionar_estudiantes(admin_user, 1, 2, 2025, 2026)

    def test_promocionar_gestion_invalida(self, enrollment_service, admin_user):
        with patch.object(enrollment_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with pytest.raises(ValueError):
                enrollment_service.promocionar_estudiantes(admin_user, 1, 2, 2026, 2025)

    def test_promocionar_sin_estudiantes(self, enrollment_service, admin_user):
        with patch.object(enrollment_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch('core.services.enrollment_service.Inscripciones.objects.filter') as mock_filter:
                mock_filter.return_value.select_related.return_value.exists.return_value = False
                with pytest.raises(ValueError, match='No hay estudiantes'):
                    enrollment_service.promocionar_estudiantes(admin_user, 1, 2, 2025, 2026)


class TestPeriodoServiceClose:

    def test_cerrar_sin_actividades_sin_notas_falla(self, periodo_service, admin_user):
        with patch.object(periodo_service.ac, 'puede_cerrar_periodo', return_value=True):
            mock_periodo = MagicMock()
            mock_periodo.estado = 'activo'
            mock_periodo.id = 1
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_act = MagicMock()
                    mock_act.id = 1
                    mock_act.nombre = "Act1"
                    mock_act.docente_asignacion_id = 1
                    mock_acts.return_value.only.return_value = [mock_act]
                    with patch('core.services.periodo_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.exists.return_value = False
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da:
                            mock_da.return_value.select_related.return_value.first.return_value = SimpleNamespace(
                                curso=SimpleNamespace(__str__=lambda s: "Curso A"),
                                area=SimpleNamespace(nombre="Matematicas"),
                            )
                            with pytest.raises(ValueError, match='No se puede cerrar'):
                                periodo_service.cerrar(admin_user, 1)

    def test_cerrar_con_todas_notas_exito(self, periodo_service, admin_user):
        with patch.object(periodo_service.ac, 'puede_cerrar_periodo', return_value=True):
            mock_periodo = MagicMock()
            mock_periodo.estado = 'activo'
            mock_periodo.id = 1
            mock_periodo.pk = 1
            mock_periodo.gestion = 2026
            with patch('core.services.periodo_service.Periodos.objects.get', return_value=mock_periodo):
                with patch('core.services.periodo_service.Actividades.objects.filter') as mock_acts:
                    mock_act = MagicMock()
                    mock_act.id = 1
                    mock_act.nombre = "Act1"
                    mock_act.docente_asignacion_id = 1
                    mock_acts.return_value.only.return_value = [mock_act]
                    with patch('core.services.periodo_service.ActividadNotas.objects.filter') as mock_notas:
                        mock_notas.return_value.exists.return_value = True
                        with patch('core.services.periodo_service.DocenteAsignacion.objects.filter') as mock_da:
                            mock_da.return_value.exclude.return_value.select_related.return_value.exists.return_value = False
                            with patch('core.services.periodo_service.PeriodoCierreDocente.objects.filter') as mock_pcd:
                                mock_pcd.return_value.values.return_value = []
                                with patch.object(periodo_service.audit, 'record', return_value=None):
                                    with patch.object(mock_periodo, 'save'):
                                        result = periodo_service.cerrar(admin_user, 1)
                                    assert mock_periodo.estado == 'cerrado'


class TestConfigService:

    def test_obtener_success(self, admin_user):
        config_service = ConfigService()
        with patch.object(config_service.ac, 'puede_ver_todo', return_value=True):
            with patch('core.services.config_service.ConfiguracionEscuela.objects.get_or_create') as mock_get:
                mock_config = MagicMock()
                mock_config.id = 1
                mock_config.nombre = "U.E. Test"
                mock_config.direccion = ""
                mock_config.telefono = ""
                mock_config.email = ""
                mock_config.ciudad = ""
                mock_config.gestion_actual = 2026
                mock_config.escala_aprobacion = 51.0
                mock_get.return_value = (mock_config, True)
                result = config_service.obtener(admin_user)
                assert result['nombre'] == "U.E. Test"
                assert result['gestion_actual'] == 2026

    def test_obtener_permission_error(self, admin_user):
        config_service = ConfigService()
        with patch.object(config_service.ac, 'puede_ver_todo', return_value=False):
            with pytest.raises(PermissionError):
                config_service.obtener(admin_user)

    def test_actualizar_success(self, admin_user):
        config_service = ConfigService()
        with patch.object(config_service.ac, 'puede_gestionar_inscripciones', return_value=True):
            with patch('core.services.config_service.ConfiguracionEscuela.objects.get_or_create') as mock_get:
                mock_config = MagicMock()
                mock_get.return_value = (mock_config, True)
                with patch.object(config_service.audit, 'record', return_value=None):
                    with patch.object(config_service, 'obtener', return_value={"nombre": "Nuevo"}):
                        result = config_service.actualizar(admin_user, {"nombre": "Nuevo"})
                    assert result['nombre'] == "Nuevo"

    def test_actualizar_permission_error(self, admin_user):
        config_service = ConfigService()
        with patch.object(config_service.ac, 'puede_gestionar_inscripciones', return_value=False):
            with pytest.raises(PermissionError):
                config_service.actualizar(admin_user, {})
