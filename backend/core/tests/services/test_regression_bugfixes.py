import pytest
from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from core.models import (
    Actividades, ActividadNotas, Areas, Asistencias, Cursos, DimensionesEvaluacion,
    DocenteAsignacion, Docentes, Estudiantes, Grados, Inscripciones, Niveles,
    Paralelos, Periodos, PeriodoCierreDocente, Roles, Usuarios,
)
from core.services.activity_service import ActivityService
from core.services.attendance_service import AttendanceService
from core.services.cierre_service import CierreService
from core.services.dashboard_service import DashboardService
from core.services.report_card_service import ReportCardService
from core.services.user_service import UserService


TODAY_ISO = date.today().isoformat()
TODAY_LOCAL = timezone.localdate()


def make_usuario(nombre, email, rol_obj):
    return Usuarios.objects.create(
        nombre=nombre, primer_apellido='Test', email=email,
        password_hash=make_password('123456'), rol=rol_obj,
    )


# ═══════════════════════════════════════════════════════════════════
# 1. ATTENDANCE — timezone.localdate() + toggle + audit mock
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAttendanceTimezoneFix:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        docente = make_usuario('Docente', 'doc@test.com', roles['docente'])
        director = make_usuario('Director', 'dir@test.com', roles['director'])
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematica')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {'docente': docente, 'director': director, 'da': da, 'estudiante': estudiante}

    @patch('core.services.attendance_service.AuditService')
    def test_docente_solo_puede_marcar_hoy(self, mock_audit_cls, setup):
        ayer = (TODAY_LOCAL - timedelta(days=1)).isoformat()
        with pytest.raises(ValueError, match='solo pueden registrar asistencia del dia de hoy'):
            AttendanceService().marcar_asistencias(
                setup['docente'], setup['da'].id, ayer,
                {str(setup['estudiante'].id): 'presente'},
            )

    @patch('core.services.attendance_service.AuditService')
    def test_docente_no_puede_marcar_futuro(self, mock_audit_cls, setup):
        manana = (TODAY_LOCAL + timedelta(days=1)).isoformat()
        with pytest.raises(ValueError, match='solo pueden registrar asistencia del dia de hoy'):
            AttendanceService().marcar_asistencias(
                setup['docente'], setup['da'].id, manana,
                {str(setup['estudiante'].id): 'presente'},
            )

    @patch('core.services.attendance_service.AuditService')
    def test_docente_marca_hoy_ok(self, mock_audit_cls, setup):
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, TODAY_ISO,
            {str(setup['estudiante'].id): 'presente'},
        )
        a = Asistencias.objects.get(estudiante=setup['estudiante'], docente_asignacion=setup['da'])
        assert a.estado == 'presente'

    def test_admin_con_motivo_pasado_ok(self, setup):
        ayer = (TODAY_LOCAL - timedelta(days=1)).isoformat()
        with patch('core.services.attendance_service.AuditService'):
            AttendanceService().marcar_asistencias(
                setup['director'], setup['da'].id, ayer,
                {str(setup['estudiante'].id): 'ausente'},
                motivo='Correccion retroactiva',
            )
        assert Asistencias.objects.filter(estudiante=setup['estudiante']).exists()

    def test_admin_con_motivo_futuro_rejected(self, setup):
        manana = (TODAY_LOCAL + timedelta(days=1)).isoformat()
        with patch('core.services.attendance_service.AuditService'):
            with pytest.raises(ValueError, match='No se puede registrar asistencia en fechas futuras'):
                AttendanceService().marcar_asistencias(
                    setup['director'], setup['da'].id, manana,
                    {str(setup['estudiante'].id): 'presente'},
                    motivo='Prueba',
                )


@pytest.mark.django_db
class TestAttendanceToggle:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='docente'),
        ])}
        docente = make_usuario('Doc2', 'doc2@test.com', roles['docente'])
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='B')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Ciencias')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD002', ci='87654321', nombres='Maria',
            primer_apellido='Lopez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {'docente': docente, 'da': da, 'estudiante': estudiante}

    @patch('core.services.attendance_service.AuditService')
    def test_toggle_from_none_to_present(self, mock_audit_cls, setup):
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, TODAY_ISO,
            {str(setup['estudiante'].id): 'presente'},
        )
        a = Asistencias.objects.get(estudiante=setup['estudiante'])
        assert a.estado == 'presente'

    @patch('core.services.attendance_service.AuditService')
    def test_toggle_present_to_absent(self, mock_audit_cls, setup):
        srv = AttendanceService()
        eid = str(setup['estudiante'].id)
        srv.marcar_asistencias(setup['docente'], setup['da'].id, TODAY_ISO, {eid: 'presente'})
        srv.marcar_asistencias(setup['docente'], setup['da'].id, TODAY_ISO, {eid: 'ausente'})
        a = Asistencias.objects.get(estudiante=setup['estudiante'])
        assert a.estado == 'ausente'
        assert Asistencias.objects.filter(estudiante=setup['estudiante']).count() == 1

    @patch('core.services.attendance_service.AuditService')
    def test_toggle_absent_to_licencia(self, mock_audit_cls, setup):
        srv = AttendanceService()
        eid = str(setup['estudiante'].id)
        srv.marcar_asistencias(setup['docente'], setup['da'].id, TODAY_ISO, {eid: 'ausente'})
        srv.marcar_asistencias(setup['docente'], setup['da'].id, TODAY_ISO, {eid: 'con_licencia'})
        a = Asistencias.objects.get(estudiante=setup['estudiante'])
        assert a.estado == 'con_licencia'

    @patch('core.services.attendance_service.AuditService')
    def test_estado_invalido_rechazado(self, mock_audit_cls, setup):
        with pytest.raises(ValueError, match='Estado invalido'):
            AttendanceService().marcar_asistencias(
                setup['docente'], setup['da'].id, TODAY_ISO,
                {str(setup['estudiante'].id): 'invalido'},
            )


# ═══════════════════════════════════════════════════════════════════
# 2. REPORT CARD — string estudiante_id conversion
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestReportCardStringIntConversion:

    @pytest.fixture
    def setup(self):
        Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='docente'), Roles(nombre='tutor'),
        ])
        estudiante = Estudiantes.objects.create(
            rude='RUD010', ci='11111111', nombres='Test',
            primer_apellido='Estudiante',
        )
        return {'estudiante': estudiante}

    def test_generar_boletin_acepta_string(self, setup):
        service = ReportCardService()
        with patch.object(service.ac, 'get_estudiantes_autorizados', return_value=None):
            with pytest.raises(ValueError, match='sin inscripciones'):
                service.generar_boletin(SimpleNamespace(id=1), str(setup['estudiante'].id))

    def test_generar_boletin_acepta_int(self, setup):
        service = ReportCardService()
        with patch.object(service.ac, 'get_estudiantes_autorizados', return_value=None):
            with pytest.raises(ValueError, match='sin inscripciones'):
                service.generar_boletin(SimpleNamespace(id=1), setup['estudiante'].id)

    def test_generar_boletin_autorizados_lista_string(self, setup):
        service = ReportCardService()
        string_id = str(setup['estudiante'].id)
        with patch.object(service.ac, 'get_estudiantes_autorizados',
                          return_value={setup['estudiante'].id}):
            with pytest.raises(ValueError, match='sin inscripciones'):
                service.generar_boletin(SimpleNamespace(id=1), string_id)


# ═══════════════════════════════════════════════════════════════════
# 3. USER — role hierarchy
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestUserRoleHierarchy:

    @pytest.fixture
    def roles(self):
        return {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='tutor'), Roles(nombre='estudiante'), Roles(nombre='docente'),
            Roles(nombre='regente'), Roles(nombre='secretaria'), Roles(nombre='director'),
        ])}

    def test_role_rank_values(self):
        assert UserService._role_rank('tutor') == 0
        assert UserService._role_rank('estudiante') == 1
        assert UserService._role_rank('docente') == 2
        assert UserService._role_rank('regente') == 3
        assert UserService._role_rank('secretaria') == 4
        assert UserService._role_rank('director') == 5
        assert UserService._role_rank('unknown') == -1

    def test_secretaria_no_puede_crear_director(self, roles):
        usuario = SimpleNamespace(id=1, nombre='Sec', rol=SimpleNamespace(nombre='secretaria'))
        with patch.object(UserService, '_role_rank', side_effect=lambda r: {'secretaria': 4, 'director': 5}.get(r, -1)):
            with patch('core.services.user_service.AccessControlService') as mock_ac_cls:
                mock_ac = mock_ac_cls.return_value
                mock_ac.puede_gestionar_usuarios.return_value = True
                with pytest.raises(PermissionError, match='No puedes crear un usuario con rol superior'):
                    UserService().crear(usuario, {
                        'email': 'nuevodir@test.com', 'nombre_completo': 'Nuevo Director', 'rol': 'director',
                    })

    def test_director_puede_crear_cualquier_rol(self, roles):
        usuario = SimpleNamespace(id=1, nombre='Dir', rol=SimpleNamespace(nombre='director'))
        with patch('core.services.user_service.AccessControlService') as mock_ac_cls:
            with patch('core.services.user_service.AuditService'):
                mock_ac = mock_ac_cls.return_value
                mock_ac.puede_gestionar_usuarios.return_value = True
                for rol_name in ('docente', 'secretaria', 'regente'):
                    with patch.object(Usuarios.objects, 'create', return_value=MagicMock(
                        id=999, nombre=rol_name, primer_apellido='T', email=f'{rol_name}@test.com',
                        rol=MagicMock(nombre=rol_name), activo=True,
                    )):
                        with patch('core.services.user_service.Docentes.objects.create', return_value=MagicMock()):
                            u = UserService().crear(usuario, {
                                'email': f'{rol_name}@test.com', 'nombre_completo': f'Rol {rol_name}', 'rol': rol_name,
                            })
                    assert u['rol'] == rol_name


# ═══════════════════════════════════════════════════════════════════
# 4. CIERRE — completitud + permission
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCierreCompletitud:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        director = make_usuario('Dir', 'dir_c@test.com', roles['director'])
        secretaria = make_usuario('Sec', 'sec_c@test.com', roles['secretaria'])
        docente = make_usuario('Doc', 'doc_c@test.com', roles['docente'])
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Segundo', numero=2)
        paralelo = Paralelos.objects.create(nombre='C')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Historia')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31', estado='activo',
        )
        return {'director': director, 'secretaria': secretaria, 'docente': docente, 'da': da, 'periodo': periodo}

    @patch('core.services.cierre_service.AuditService')
    def test_cierre_director_exitoso(self, mock_audit_cls, setup):
        result = CierreService().cerrar_docente(
            setup['director'], setup['da'].id, setup['periodo'].id,
        )
        assert 'exitosamente' in result['mensaje']

    @patch('core.services.cierre_service.AuditService')
    def test_cierre_secretaria_exitoso(self, mock_audit_cls, setup):
        result = CierreService().cerrar_docente(
            setup['secretaria'], setup['da'].id, setup['periodo'].id,
        )
        assert 'exitosamente' in result['mensaje']

    @patch('core.services.cierre_service.AuditService')
    def test_cierre_docente_propio(self, mock_audit_cls, setup):
        result = CierreService().cerrar_docente(
            setup['docente'], setup['da'].id, setup['periodo'].id,
        )
        assert 'exitosamente' in result['mensaje']

    @patch('core.services.cierre_service.AuditService')
    def test_cierre_duplicado_mensaje(self, mock_audit_cls, setup):
        CierreService().cerrar_docente(setup['director'], setup['da'].id, setup['periodo'].id)
        result = CierreService().cerrar_docente(setup['director'], setup['da'].id, setup['periodo'].id)
        assert 'ya estaba cerrado' in result['mensaje']

    def test_cierre_otro_docente_sin_permiso(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = make_usuario('Otro', 'otro@test.com', otro_rol)
        Docentes.objects.create(usuario=otro)
        with pytest.raises(PermissionError):
            CierreService().cerrar_docente(otro, setup['da'].id, setup['periodo'].id)


# ═══════════════════════════════════════════════════════════════════
# 5. DASHBOARD — docente dashboard with asignaciones
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestDashboardDocenteAsignaciones:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='docente'),
        ])}
        director = make_usuario('Dir', 'dir_dash@test.com', roles['director'])
        docente = make_usuario('Doc', 'doc_dash@test.com', roles['docente'])
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Tercero', numero=3)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area1 = Areas.objects.create(nombre='Lenguaje')
        area2 = Areas.objects.create(nombre='Geografia')
        dm = Docentes.objects.create(usuario=docente)
        da1 = DocenteAsignacion.objects.create(docente=dm, curso=curso, area=area1, gestion=2026)
        da2 = DocenteAsignacion.objects.create(docente=dm, curso=curso, area=area2, gestion=2026)
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31', estado='activo',
        )
        from django.db import connection
        with connection.cursor() as c:
            c.execute(
                "CREATE VIEW IF NOT EXISTS v_notas_totales AS "
                "SELECT 1 AS estudiante_id, 1 AS docente_asignacion_id, "
                "1 AS periodo_id, 1.0 AS nota_total, 0 AS dimensiones_evaluadas WHERE 0"
            )
        return {'director': director, 'docente': docente, 'das': [da1, da2], 'periodo': periodo}

    def test_dashboard_docente_muestra_asignaciones(self, setup):
        data = DashboardService().build_dashboard(setup['docente'])
        assert 'asignaciones' in data
        assert len(data['asignaciones']) == 2

    def test_dashboard_docente_asignacion_detail(self, setup):
        data = DashboardService().build_dashboard(setup['docente'])
        for a in data['asignaciones']:
            assert 'curso' in a
            assert 'area' in a
            assert 'actividades_count' in a
            assert 'completitud' in a
            assert 'cerrado' in a

    def test_dashboard_docente_sin_asignaciones(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = make_usuario('SinAsig', 'sinasig@test.com', otro_rol)
        Docentes.objects.create(usuario=otro)
        data = DashboardService().build_dashboard(otro)
        assert data['asignaciones'] == []

    @patch.object(DashboardService, '_dashboard_docente')
    def test_dashboard_estructura(self, mock_dd, setup):
        mock_dd.return_value = {'asignaciones': [], 'total_estudiantes': 0, 'estudiantes_con_notas': 0, 'periodo_activo': None}
        data = DashboardService().build_dashboard(setup['docente'])
        assert 'asignaciones' in data


# ═══════════════════════════════════════════════════════════════════
# 6. ACTIVITY SERVICE — guardar_notas_batch bulk operations
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestActivityServiceBulkOperations:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='docente'),
        ])}
        director = make_usuario('Dir', 'dir_bulk@test.com', roles['director'])
        docente = make_usuario('Doc', 'doc_bulk@test.com', roles['docente'])
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Cuarto', numero=4)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematica')
        dm = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(docente=dm, curso=curso, area=area, gestion=2026)
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31', estado='activo',
        )
        dim = DimensionesEvaluacion.objects.create(nombre='SABER', orden=2, gestion=2026)
        act1 = Actividades.objects.create(
            docente_asignacion=da, periodo=periodo, dimension=dim,
            nombre='Act1', puntaje_maximo=100, fecha_actividad=TODAY_ISO,
        )
        act2 = Actividades.objects.create(
            docente_asignacion=da, periodo=periodo, dimension=dim,
            nombre='Act2', puntaje_maximo=50, fecha_actividad=TODAY_ISO,
        )
        e1 = Estudiantes.objects.create(rude='RUD040', ci='66666666', nombres='Pedro', primer_apellido='Sol')
        e2 = Estudiantes.objects.create(rude='RUD041', ci='77777777', nombres='Sofia', primer_apellido='Luna')
        Inscripciones.objects.create(estudiante=e1, curso=curso, gestion=2026, estado='activo')
        Inscripciones.objects.create(estudiante=e2, curso=curso, gestion=2026, estado='activo')
        return {
            'director': director, 'docente': docente, 'da': da, 'periodo': periodo,
            'act1': act1, 'act2': act2, 'e1': e1, 'e2': e2,
        }

    def test_batch_crea_notas_en_lote(self, setup):
        actividades = [
            {'actividad_id': setup['act1'].id, 'notas': {str(setup['e1'].id): 80, str(setup['e2'].id): 75}},
            {'actividad_id': setup['act2'].id, 'notas': {str(setup['e1'].id): 40, str(setup['e2'].id): 35}},
        ]
        ActivityService().guardar_notas_batch(setup['docente'], actividades)
        assert ActividadNotas.objects.count() == 4
        an1 = ActividadNotas.objects.get(actividad=setup['act1'], estudiante=setup['e1'])
        assert float(an1.valor) == 80

    def test_batch_actualiza_notas_existente(self, setup):
        ActividadNotas.objects.create(actividad=setup['act1'], estudiante=setup['e1'], valor=50)
        actividades = [
            {'actividad_id': setup['act1'].id, 'notas': {str(setup['e1'].id): 95}},
        ]
        ActivityService().guardar_notas_batch(setup['docente'], actividades)
        an1 = ActividadNotas.objects.get(actividad=setup['act1'], estudiante=setup['e1'])
        assert float(an1.valor) == 95
        assert ActividadNotas.objects.count() == 1

    def test_batch_mixto_crea_y_actualiza(self, setup):
        ActividadNotas.objects.create(actividad=setup['act1'], estudiante=setup['e1'], valor=50)
        actividades = [
            {'actividad_id': setup['act1'].id, 'notas': {str(setup['e1'].id): 99}},
            {'actividad_id': setup['act2'].id, 'notas': {str(setup['e2'].id): 44}},
        ]
        ActivityService().guardar_notas_batch(setup['docente'], actividades)
        assert ActividadNotas.objects.count() == 2
        assert float(ActividadNotas.objects.get(actividad=setup['act1'], estudiante=setup['e1']).valor) == 99
        assert float(ActividadNotas.objects.get(actividad=setup['act2'], estudiante=setup['e2']).valor) == 44
