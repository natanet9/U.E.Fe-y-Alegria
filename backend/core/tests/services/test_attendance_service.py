import pytest
from datetime import date
from django.contrib.auth.hashers import make_password

from core.models import (
    Areas, Asistencias, Cursos, DocenteAsignacion, Docentes, Estudiantes, Grados,
    Inscripciones, Licencias, Niveles, Paralelos, Periodos, Roles, Tutores, Usuarios,
)
from core.services.attendance_service import AttendanceService
from core.services.license_service import LicenseService


@pytest.mark.django_db
class TestAttendanceService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'),
            Roles(nombre='docente'), Roles(nombre='regente'),
        ])}
        docente = Usuarios.objects.create(
            nombre='Docente', email='doc@test.com',
            password_hash=make_password('123456'), rol=roles['docente'],
        )
        regente = Usuarios.objects.create(
            nombre='Regente', email='reg@test.com',
            password_hash=make_password('123456'), rol=roles['regente'],
        )
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'],
        )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Lenguaje')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {
            'docente': docente, 'regente': regente, 'secretaria': secretaria,
            'da': da, 'estudiante': estudiante,
        }

    def test_listar_asistencias(self, setup):
        hoy = date.today().isoformat()
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, hoy,
            {str(setup['estudiante'].id): 'presente'},
        )
        registros = AttendanceService().listar_asistencias(
            setup['docente'], setup['da'].id, hoy,
        )
        assert len(registros) == 1
        assert registros[0]['estado'] == 'presente'

    def test_marcar_asistencias(self, setup):
        hoy = date.today().isoformat()
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, hoy,
            {str(setup['estudiante'].id): 'ausente'},
        )
        a = Asistencias.objects.get(
            estudiante=setup['estudiante'],
            docente_asignacion=setup['da'],
            fecha=date.fromisoformat(hoy),
        )
        assert a.estado == 'ausente'

    def test_marcar_asistencias_actualiza_sin_duplicar(self, setup):
        hoy = date.today().isoformat()
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, hoy,
            {str(setup['estudiante'].id): 'presente'},
        )
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, hoy,
            {str(setup['estudiante'].id): 'ausente'},
        )

        asistencias = Asistencias.objects.filter(
            estudiante=setup['estudiante'],
            docente_asignacion=setup['da'],
            fecha=date.fromisoformat(hoy),
            tipo='por_asignacion',
        )
        assert asistencias.count() == 1
        assert asistencias.first().estado == 'ausente'

    def test_marcar_asistencias_invalid_state(self, setup):
        with pytest.raises(ValueError):
            AttendanceService().marcar_asistencias(
                setup['docente'], setup['da'].id, date(2026, 5, 21),
                {str(setup['estudiante'].id): 'invalido'},
            )

    def test_marcar_asistencias_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro', email='otro@test.com',
            password_hash=make_password('123456'),
            rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            AttendanceService().marcar_asistencias(
                otro, setup['da'].id, date(2026, 5, 21), {},
            )

    def test_listar_asistencias_admin(self, setup):
        hoy = date.today().isoformat()
        AttendanceService().marcar_asistencias(
            setup['secretaria'], setup['da'].id, hoy,
            {str(setup['estudiante'].id): 'presente'},
            motivo='Carga inicial',
        )
        result = AttendanceService().listar_asistencias_admin(
            setup['secretaria'], hoy,
        )
        assert len(result) >= 1

    def test_crear_licencia(self, setup):
        tutor = Tutores.objects.create(
            ci='11111111', nombres='Tutor', primer_apellido='Test',
            celular='77700000',
        )
        lic = LicenseService().crear(setup['regente'], {
            'estudiante_id': setup['estudiante'].id,
            'motivo': 'Enfermedad',
            'fecha_inicio': '2026-05-01',
            'fecha_fin': '2026-05-03',
            'tutor_id': tutor.id,
        })
        assert lic['mensaje'] == 'Licencia creada exitosamente'

    def test_crear_licencia_permision(self, setup):
        with pytest.raises(PermissionError):
            LicenseService().crear(setup['docente'], {
                'estudiante_id': 1, 'motivo': 'Test',
                'fecha_inicio': '2026-05-01', 'fecha_fin': '2026-05-03',
            })

    def test_aprobar_licencia(self, setup):
        tut = Tutores.objects.create(
            ci='22222222', nombres='T2', primer_apellido='T',
            celular='77700001',
        )
        lic = Licencias.objects.create(
            estudiante=setup['estudiante'],
            tutor_solicitante=tut,
            motivo='Falta', fecha_inicio='2026-05-01',
            fecha_fin='2026-05-01',
        )
        result = LicenseService().aprobar(
            setup['secretaria'], lic.id, aceptar=True,
        )
        assert result['estado'] == 'aprobada'

    def test_aprobar_licencia_mas_3_dias(self, setup):
        tut = Tutores.objects.create(
            ci='33333333', nombres='T3', primer_apellido='T',
            celular='77700002',
        )
        lic = Licencias.objects.create(
            estudiante=setup['estudiante'],
            tutor_solicitante=tut,
            motivo='Viaje', fecha_inicio='2026-05-01',
            fecha_fin='2026-05-10',
        )
        with pytest.raises(PermissionError, match='mas de 3 dias'):
            LicenseService().aprobar(
                setup['regente'], lic.id, aceptar=True,
            )

    def test_listar_licencias(self, setup):
        LicenseService().listar(setup['secretaria'])
