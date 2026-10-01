from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import Actividades, DocenteAsignacion, Estudiantes, Licencias, Periodos, Usuarios
from core.views import (
    actividades_notas_estudiante_view,
    actividades_notas_view,
    actividad_delete_view,
    actividad_restore_view,
    attendance_view,
    change_password_view,
    cierre_view,
    course_detail_view,
    course_delete_view,
    course_restore_view,
    courses_view,
    docentes_view,
    docente_delete_view,
    docente_restore_view,
    enrollment_catalogs_view,
    enrollment_new_view,
    enrollment_re_enroll_view,
    enrollment_search_view,
    grades_update_view,
    grades_view,
    licencias_view,
    periodos_view,
    reports_download_view,
    reports_view,
    schedules_view,
    search_tutor_by_ci_view,
    student_delete_view,
    student_restore_view,
    students_view,
    dashboard_view,
)


USUARIO_SECRETARIA = SimpleNamespace(
    id=1,
    activo=True,
    nombre_completo='Sec',
    email='sec@test.com',
    rol=SimpleNamespace(nombre='secretaria'),
)

USUARIO_DOCENTE = SimpleNamespace(
    id=2,
    activo=True,
    nombre_completo='Doc',
    email='doc@test.com',
    rol=SimpleNamespace(nombre='docente'),
)

USUARIO_REGENTE = SimpleNamespace(
    id=3,
    activo=True,
    nombre_completo='Reg',
    email='reg@test.com',
    rol=SimpleNamespace(nombre='regente'),
)


def _request(factory, method, path, data=None, query=None, usuario=None):
    if method == 'get':
        request = factory.get(path, query or {})
    elif method == 'post':
        request = factory.post(path, data or {}, format='json')
    elif method == 'patch':
        request = factory.patch(path, data or {}, format='json')
    elif method == 'delete':
        request = factory.delete(path)
    else:
        raise ValueError(method)
    if usuario is not None:
        request.usuario = usuario
    return request


@pytest.mark.django_db
class TestViewBranches:
    def test_change_password_requires_auth_and_validation(self):
        factory = APIRequestFactory()
        assert change_password_view(factory.post('/api/auth/change-password/', {}, format='json')).status_code == status.HTTP_401_UNAUTHORIZED

        request = _request(factory, 'post', '/api/auth/change-password/', {'current_password': 'old'}, usuario=USUARIO_SECRETARIA)
        response = change_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'post', '/api/auth/change-password/', {'current_password': 'old', 'new_password': 'new'}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.AuthService.change_password', return_value=({}, 'Credenciales invalidas')):
            response = change_password_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_password_success(self):
        factory = APIRequestFactory()
        request = _request(factory, 'post', '/api/auth/change-password/', {'current_password': 'old', 'new_password': 'new'}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.AuthService.change_password', return_value=({'mensaje': 'ok'}, None)):
            response = change_password_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_dashboard_view_auth_and_success(self):
        factory = APIRequestFactory()
        assert dashboard_view(factory.get('/api/dashboard/')).status_code == status.HTTP_401_UNAUTHORIZED
        request = _request(factory, 'get', '/api/dashboard/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.DashboardService.build_dashboard', return_value={'ok': True}):
            response = dashboard_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'ok': True}

    def test_students_view_get_and_post_paths(self):
        factory = APIRequestFactory()
        request = _request(factory, 'get', '/api/students/', usuario=USUARIO_SECRETARIA, query={'query': 'Ana', 'grado_id': '1', 'page': '2', 'page_size': '10', 'incluir_inactivos': 'true'})
        with patch('core.views.StudentsService.listar', return_value={'estudiantes': [], 'total': 0, 'page': 2, 'page_size': 10, 'total_pages': 1}):
            response = students_view(request)
        assert response.status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/students/', {'rude': 'R1'}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.StudentsService.crear', return_value={'id': 1}):
            response = students_view(request)
        assert response.status_code == status.HTTP_201_CREATED

    def test_student_restore_delete_paths(self):
        factory = APIRequestFactory()
        request = _request(factory, 'post', '/api/students/1/restore/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.StudentsService.restaurar', return_value={'id': 1}):
            assert student_restore_view(request, 1).status_code == status.HTTP_200_OK

        request = _request(factory, 'delete', '/api/students/1/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.StudentsService.eliminar'):
            assert student_delete_view(request, 1).status_code == status.HTTP_200_OK

    def test_docentes_view_and_restore_delete(self):
        factory = APIRequestFactory()
        request = _request(factory, 'get', '/api/docentes/', usuario=USUARIO_SECRETARIA, query={'search': 'Sec', 'rol': 'secretaria', 'incluir_inactivos': 'true'})
        with patch('core.views.UserService.listar', return_value={'usuarios': [], 'total': 0, 'page': 1, 'page_size': 8, 'total_pages': 1}):
            assert docentes_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/docentes/', {'email': 'a@b.com', 'nombre_completo': 'X', 'rol': 'docente'}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.UserService.crear', return_value={'id': 1}):
            assert docentes_view(request).status_code == status.HTTP_201_CREATED

        request = _request(factory, 'post', '/api/docentes/1/restore/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.UserService.restaurar', return_value={'id': 1}):
            assert docente_restore_view(request, 1).status_code == status.HTTP_200_OK

        request = _request(factory, 'delete', '/api/docentes/1/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.UserService.eliminar'):
            assert docente_delete_view(request, 1).status_code == status.HTTP_200_OK

    def test_enrollment_views_branching(self):
        factory = APIRequestFactory()
        request = _request(factory, 'get', '/api/enrollment/search/', usuario=USUARIO_SECRETARIA)
        assert enrollment_search_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/enrollment/search/', usuario=USUARIO_SECRETARIA, query={'rude': 'R1'})
        with patch('core.views.EnrollmentService.search_existing_student', return_value=None):
            assert enrollment_search_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/enrollment/new/', {'rude': 'R1'}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.EnrollmentService.enroll_new_student', return_value={'id': 1}):
            assert enrollment_new_view(request).status_code == status.HTTP_201_CREATED

        request = _request(factory, 'post', '/api/enrollment/re-enroll/', {'rude': 'R1'}, usuario=USUARIO_SECRETARIA)
        assert enrollment_re_enroll_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/enrollment/catalogs/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.EnrollmentService.get_enrollment_catalogs', return_value={'gestiones': []}):
            assert enrollment_catalogs_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'get', '/api/enrollment/search-tutor/', usuario=USUARIO_SECRETARIA)
        assert search_tutor_by_ci_view(request).status_code == status.HTTP_400_BAD_REQUEST

    def test_course_views_branching(self):
        factory = APIRequestFactory()
        request = _request(factory, 'get', '/api/courses/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.CourseService.listar_asignaciones', return_value=[]):
            assert courses_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/courses/', {'usuario_id': 1}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.CourseService.crear_asignacion', return_value={'id': 1}):
            assert courses_view(request).status_code == status.HTTP_201_CREATED

        request = _request(factory, 'get', '/api/courses/detail/', usuario=USUARIO_SECRETARIA)
        assert course_detail_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'post', '/api/courses/1/restore/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.CourseService.restaurar', return_value={'id': 1}):
            assert course_restore_view(request, 1).status_code == status.HTTP_200_OK

        request = _request(factory, 'delete', '/api/courses/1/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.CourseService.eliminar'):
            assert course_delete_view(request, 1).status_code == status.HTTP_200_OK

    def test_periodos_grades_reports_and_schedule(self):
        factory = APIRequestFactory()
        request = _request(factory, 'get', '/api/periodos/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.PeriodoService.listar', return_value=[]):
            assert periodos_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/periodos/', {'accion': 'desconocida'}, usuario=USUARIO_SECRETARIA)
        assert periodos_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/grades/', usuario=USUARIO_SECRETARIA)
        assert grades_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/grades/', usuario=USUARIO_SECRETARIA, query={'docente_asignacion_id': '1', 'periodo_id': '1'})
        with patch('core.views.GradesService.get_notas_totales', return_value=[]), patch('core.views.GradesService.get_notas_por_dimension', return_value=[]):
            assert grades_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'get', '/api/reports/', usuario=USUARIO_SECRETARIA)
        assert reports_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/reports/', usuario=USUARIO_SECRETARIA, query={'docente_asignacion_id': '1', 'periodo_id': '1'})
        with patch('core.views.GradesService.get_notas_por_dimension', return_value=[]), patch('core.views.GradesService.get_notas_totales', return_value=[]):
            with patch('core.views.DocenteAsignacion.objects.get') as mock_da_get:
                mock_da_get.return_value = MagicMock(curso=MagicMock(), gestion=2026)
                with patch('core.views.Inscripciones.objects.filter') as mock_ins:
                    mock_ins.return_value.select_related.return_value = []
                    assert reports_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'get', '/api/reports/download/', usuario=USUARIO_SECRETARIA)
        assert reports_download_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/reports/download/', usuario=USUARIO_SECRETARIA, query={'docente_asignacion_id': '1', 'periodo_id': '1'})
        with patch('core.views.ReportsService.export_notas_excel', return_value=BytesIO(b'xls')):
            assert reports_download_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'get', '/api/schedules/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.ScheduleService.listar_horarios', return_value=[]):
            assert schedules_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/schedules/', {'docente_asignacion_id': 1}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.ScheduleService.guardar_horario', return_value={'id': 1}):
            assert schedules_view(request).status_code == status.HTTP_201_CREATED

        request = _request(factory, 'post', '/api/schedules/', {}, usuario=USUARIO_DOCENTE)
        assert schedules_view(request).status_code == status.HTTP_403_FORBIDDEN

    def test_attendance_licenses_cierre_and_restores(self):
        factory = APIRequestFactory()
        request = _request(factory, 'get', '/api/attendance/', usuario=USUARIO_SECRETARIA, query={'docente_asignacion_id': '1'})
        with patch('core.views.AttendanceService.listar_asistencias', return_value=[]):
            assert attendance_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/attendance/', {'docente_asignacion_id': 1, 'fecha': '2025-01-01', 'estados': {'1': 'A'}}, usuario=USUARIO_SECRETARIA)
        with patch('core.views.AttendanceService.marcar_asistencias', return_value=None):
            assert attendance_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/licencias/', {'estudiante_id': 1, 'motivo': 'x', 'fecha_inicio': '2025-01-01', 'fecha_fin': '2025-01-02'}, usuario=USUARIO_REGENTE)
        with patch('core.views.LicenseService.crear', return_value={'id': 1}):
            assert licencias_view(request).status_code == status.HTTP_201_CREATED

        request = _request(factory, 'patch', '/api/licencias/', {'aceptar': True}, usuario=USUARIO_SECRETARIA)
        assert licencias_view(request).status_code == status.HTTP_400_BAD_REQUEST

        request = _request(factory, 'get', '/api/cierre/', usuario=USUARIO_SECRETARIA)
        with patch('core.views.CierreService.listar_cierres', return_value=[]):
            assert cierre_view(request).status_code == status.HTTP_200_OK

        request = _request(factory, 'post', '/api/cierre/', {'accion': 'desconocida', 'docente_asignacion_id': 1, 'periodo_id': 1}, usuario=USUARIO_SECRETARIA)
        assert cierre_view(request).status_code == status.HTTP_400_BAD_REQUEST

