import pytest
from django.contrib.auth.hashers import make_password

from core.models import Estudiantes, Licencias, Roles, Tutores, Usuarios
from core.services.license_service import LicenseService


@pytest.mark.django_db
class TestLicenseService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'),
            Roles(nombre='docente'), Roles(nombre='regente'), Roles(nombre='tutor'),
        ])}
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'],
        )
        regente = Usuarios.objects.create(
            nombre='Regente', email='reg@test.com',
            password_hash=make_password('123456'), rol=roles['regente'],
        )
        docente = Usuarios.objects.create(
            nombre='Docente', email='doc@test.com',
            password_hash=make_password('123456'), rol=roles['docente'],
        )
        director = Usuarios.objects.create(
            nombre='Dir', email='dir@test.com',
            password_hash=make_password('123456'), rol=roles['director'],
        )
        tutor_user = Usuarios.objects.create(
            nombre='Tutor', email='tut@test.com',
            password_hash=make_password('123456'), rol=roles['tutor'],
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Juan',
            primer_apellido='Perez',
        )
        tutor = Tutores.objects.create(
            ci='11111111', nombres='Tutor', primer_apellido='Test',
            celular='77700000',
        )
        lic = Licencias.objects.create(
            estudiante=estudiante, tutor_solicitante=tutor,
            motivo='Enfermedad', fecha_inicio='2026-05-01',
            fecha_fin='2026-05-03', regente=regente,
        )
        return {
            'secretaria': secretaria, 'regente': regente, 'docente': docente,
            'director': director, 'tutor_user': tutor_user,
            'estudiante': estudiante, 'tutor': tutor, 'lic': lic,
        }

    def test_listar_secretaria(self, setup):
        result = LicenseService().listar(setup['secretaria'])
        assert len(result) >= 1

    def test_listar_regente(self, setup):
        result = LicenseService().listar(setup['regente'])
        assert len(result) >= 1

    def test_listar_regente_other(self, setup):
        otro_rol = Roles.objects.get(nombre='regente')
        otro = Usuarios.objects.create(
            nombre='OtroReg', email='oreg@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        result = LicenseService().listar(otro)
        assert len(result) >= 1

    def test_listar_docente_permision(self, setup):
        with pytest.raises(PermissionError):
            LicenseService().listar(setup['docente'])

    def test_listar_tutor_permision(self, setup):
        with pytest.raises(PermissionError):
            LicenseService().listar(setup['tutor_user'])

    def test_listar_por_estado(self, setup):
        result = LicenseService().listar(setup['secretaria'], estado='pendiente')
        assert len(result) >= 1

    def test_crear_licencia_regente(self, setup):
        result = LicenseService().crear(setup['regente'], {
            'estudiante_id': setup['estudiante'].id,
            'motivo': 'Enfermedad', 'fecha_inicio': '2026-06-01',
            'fecha_fin': '2026-06-03', 'tutor_id': setup['tutor'].id,
        })
        assert result['mensaje'] == 'Licencia creada exitosamente'

    def test_crear_licencia_secretaria(self, setup):
        result = LicenseService().crear(setup['secretaria'], {
            'estudiante_id': setup['estudiante'].id,
            'motivo': 'Enfermedad', 'fecha_inicio': '2026-06-01',
            'fecha_fin': '2026-06-03', 'tutor_id': setup['tutor'].id,
        })
        assert result['mensaje'] == 'Licencia creada exitosamente'

    def test_crear_licencia_permision(self, setup):
        with pytest.raises(PermissionError):
            LicenseService().crear(setup['docente'], {
                'estudiante_id': 1, 'motivo': 'Test',
                'fecha_inicio': '2026-05-01', 'fecha_fin': '2026-05-03',
            })

    def test_crear_licencia_validation(self, setup):
        with pytest.raises(ValueError, match='Campos requeridos faltantes'):
            LicenseService().crear(setup['regente'], {
                'estudiante_id': setup['estudiante'].id,
            })

    def test_aprobar_licencia_secretaria(self, setup):
        result = LicenseService().aprobar(setup['secretaria'], setup['lic'].id, aceptar=True)
        assert result['estado'] == 'aprobada'

    def test_aprobar_licencia_regente_3_dias(self, setup):
        tut = Tutores.objects.create(
            ci='22222222', nombres='T2', primer_apellido='T', celular='77700001',
        )
        lic = Licencias.objects.create(
            estudiante=setup['estudiante'], tutor_solicitante=tut,
            motivo='Falta', fecha_inicio='2026-05-01', fecha_fin='2026-05-03',
        )
        result = LicenseService().aprobar(setup['regente'], lic.id, aceptar=True)
        assert result['estado'] == 'aprobada'

    def test_aprobar_licencia_regente_mas_3_dias(self, setup):
        tut = Tutores.objects.create(
            ci='33333333', nombres='T3', primer_apellido='T', celular='77700002',
        )
        lic = Licencias.objects.create(
            estudiante=setup['estudiante'], tutor_solicitante=tut,
            motivo='Viaje', fecha_inicio='2026-05-01', fecha_fin='2026-05-10',
        )
        with pytest.raises(PermissionError, match='mas de 3 dias'):
            LicenseService().aprobar(setup['regente'], lic.id, aceptar=True)

    def test_aprobar_licencia_permision(self, setup):
        with pytest.raises(PermissionError):
            LicenseService().aprobar(setup['docente'], setup['lic'].id, aceptar=True)

    def test_rechazar_licencia(self, setup):
        result = LicenseService().aprobar(setup['secretaria'], setup['lic'].id, aceptar=False, observaciones='No procede')
        assert result['estado'] == 'rechazada'

    def test_obtener_actualizar_y_eliminar(self, setup):
        data = LicenseService().obtener(setup['secretaria'], setup['lic'].id)
        assert data['id'] == setup['lic'].id

        actualizado = LicenseService().actualizar(setup['secretaria'], setup['lic'].id, {
            'motivo': 'Actualizado',
            'observaciones': 'Cambio manual',
        })
        assert actualizado['mensaje'] == 'Licencia actualizada exitosamente'

        eliminado = LicenseService().eliminar(setup['secretaria'], setup['lic'].id)
        assert eliminado['mensaje'] == 'Licencia eliminada'
