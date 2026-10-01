"""Flujo de cuentas de tutores, autenticacion en dos pasos (2FA) y recuperacion.

Cubre el alta del tutor con usuario + contrasena temporal, el envio de las
credenciales y los codigos por correo, el login en dos pasos y la recuperacion
de la contrasena mediante codigo.
"""
import re

import pytest
from django.contrib.auth.hashers import check_password, make_password
from django.core import mail
from django.test import override_settings

from core.models import CodigoVerificacion, EstudianteTutor, Estudiantes, Roles, Tutores, Usuarios
from core.services.access_service import AccessControlService
from core.services.auth_service import AuthService
from core.services.estudiante_tutor_service import EstudianteTutorService
from core.services.tutores_service import TutoresService

PASSWORD_REGEX = re.compile(r'Contrasena temporal: (\S+)')
CODIGO_REGEX = re.compile(r'Tu codigo de verificacion es: (\d{6})')


def _password_de_correo(indice=-1):
    return PASSWORD_REGEX.search(mail.outbox[indice].body).group(1)


def _codigo_de_correo(indice=-1):
    return CODIGO_REGEX.search(mail.outbox[indice].body).group(1)


@pytest.mark.django_db
class TestAltaTutorConCuentaY2FA:

    @pytest.fixture
    def secretaria(self):
        rol = Roles.objects.create(nombre='secretaria', descripcion='Secretaria')
        return Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('Secre123!'), rol=rol, activo=True,
        )

    def _crear_tutor(self, secretaria, email='carlos.perez@test.com'):
        return TutoresService().crear(secretaria, {
            'ci': '8765432',
            'nombres': 'Carlos',
            'primer_apellido': 'Perez',
            'email': email,
        })

    def test_alta_tutor_crea_cuenta_con_password_temporal(self, secretaria):
        mail.outbox = []
        with override_settings(OTP_2FA_POR_DEFECTO=True):
            resultado = self._crear_tutor(secretaria)

        cuenta = resultado['cuenta']
        assert cuenta['usuario_id']
        assert cuenta['debe_cambiar_password'] is True
        assert cuenta['otp_habilitado'] is True
        assert cuenta['otp_metodo'] == 'email'
        assert cuenta['correo_enviado'] is True

        usuario = Usuarios.objects.get(id=cuenta['usuario_id'])
        assert usuario.rol.nombre == 'tutor'
        assert usuario.activo is True
        assert usuario.password_temporal is True
        assert usuario.debe_cambiar_password is True
        assert usuario.otp_habilitado is True

        # La cuenta queda vinculada al tutor y el correo con credenciales se envio
        tutor = Tutores.objects.get(ci='8765432')
        assert tutor.usuario_id == usuario.id
        assert tutor.tiene_usuario is True
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['carlos.perez@test.com']
        assert check_password(_password_de_correo(), usuario.password_hash)

    def test_alta_tutor_sin_2fa_cuando_el_ajuste_esta_apagado(self, secretaria):
        with override_settings(OTP_2FA_POR_DEFECTO=False):
            resultado = self._crear_tutor(secretaria, email='sin2fa@test.com')

        usuario = Usuarios.objects.get(id=resultado['cuenta']['usuario_id'])
        assert usuario.otp_habilitado is False

    def test_no_se_crea_cuenta_sin_correo(self, secretaria):
        resultado = TutoresService().crear(secretaria, {
            'ci': '1111111', 'nombres': 'Sin', 'primer_apellido': 'Correo',
        })
        assert resultado['cuenta'] is None
        assert Tutores.objects.get(ci='1111111').usuario_id is None

    def test_rechaza_correo_duplicado(self, secretaria):
        self._crear_tutor(secretaria, email='duplicado@test.com')
        resultado = TutoresService().crear(secretaria, {
            'ci': '2222222', 'nombres': 'Otro', 'primer_apellido': 'Tutor',
            'email': 'duplicado@test.com',
        })
        assert 'error' in resultado['cuenta']


@pytest.mark.django_db
class TestLoginEnDosPasos:

    @pytest.fixture
    def tutor_con_cuenta(self):
        rol = Roles.objects.create(nombre='secretaria')
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('Secre123!'), rol=rol, activo=True,
        )
        TutoresService().crear(secretaria, {
            'ci': '5555555', 'nombres': 'Marta', 'primer_apellido': 'Quispe',
            'email': 'marta.quispe@test.com',
        })
        usuario = Usuarios.objects.get(email='marta.quispe@test.com')
        return usuario, _password_de_correo()

    def test_login_pide_codigo_y_luego_permite_el_cambio(self, tutor_con_cuenta):
        usuario, password_temporal = tutor_con_cuenta
        mail.outbox = []

        desafio, error = AuthService().login(usuario.email, password_temporal)
        assert error is None
        assert desafio['requires_otp'] is True
        assert desafio['otp_token']
        assert desafio['usuario']['debe_cambiar_password'] is True
        assert CODIGO_REGEX.search(mail.outbox[-1].body)

        sesion, error = AuthService().verify_otp(desafio['otp_token'], _codigo_de_correo())
        assert error is None
        assert sesion['token']
        assert sesion['usuario']['debe_cambiar_password'] is True

        # El cambio de contrasena limpia las banderas de contrasena temporal
        resultado, error = AuthService().change_password(usuario, password_temporal, 'NuevaClave123!')
        assert error is None
        assert resultado['mensaje'] == 'Contrasena cambiada exitosamente'

        usuario.refresh_from_db()
        assert usuario.debe_cambiar_password is False
        assert usuario.password_temporal is False
        assert check_password('NuevaClave123!', usuario.password_hash)

    def test_codigo_incorrecto_no_entrega_token(self, tutor_con_cuenta):
        usuario, password_temporal = tutor_con_cuenta
        mail.outbox = []

        desafio, _ = AuthService().login(usuario.email, password_temporal)
        sesion, error = AuthService().verify_otp(desafio['otp_token'], '000000')
        assert sesion is None
        assert error

    def test_reenvio_de_codigo_deja_uno_vigente(self, tutor_con_cuenta):
        usuario, password_temporal = tutor_con_cuenta
        mail.outbox = []

        desafio, _ = AuthService().login(usuario.email, password_temporal)
        datos, error = AuthService().reenviar_codigo_otp(desafio['otp_token'])
        assert error is None
        assert datos['correo_enviado'] is True
        assert len(mail.outbox) == 2
        assert CodigoVerificacion.objects.filter(
            usuario=usuario, proposito='login', usado=False,
        ).count() == 1


@pytest.mark.django_db
class TestRecuperacionYAccesoTutor:

    @pytest.fixture
    def escenario(self):
        rol_secretaria = Roles.objects.create(nombre='secretaria')
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('Secre123!'), rol=rol_secretaria, activo=True,
        )
        resultado = TutoresService().crear(secretaria, {
            'ci': '4444444', 'nombres': 'Luis', 'primer_apellido': 'Rojas',
            'email': 'luis.rojas@test.com',
        })
        tutor = Tutores.objects.get(ci='4444444')
        cuenta = Usuarios.objects.get(id=resultado['cuenta']['usuario_id'])
        estudiante = Estudiantes.objects.create(
            rude='R-001', ci='9999999', nombres='Ana', primer_apellido='Rojas',
        )
        EstudianteTutorService().crear(secretaria, {
            'estudiante_id': estudiante.id, 'tutor_id': tutor.id,
        })
        return {'secretaria': secretaria, 'tutor': tutor, 'cuenta': cuenta, 'estudiante': estudiante}

    def test_recuperacion_de_contrasena_con_codigo_por_correo(self, escenario):
        mail.outbox = []
        email = 'luis.rojas@test.com'

        envio = AuthService().solicitar_codigo_recuperacion(email)
        assert envio and envio['enviado'] is True
        assert envio['destinatario'].endswith('@test.com')

        codigo = _codigo_de_correo()
        resultado = AuthService().reset_password_con_codigo(email, codigo, 'OtraClave123!')
        assert resultado['mensaje'] == 'Contrasena actualizada exitosamente'

        escenario['cuenta'].refresh_from_db()
        assert check_password('OtraClave123!', escenario['cuenta'].password_hash)

    def test_recuperacion_de_contrasena_flujo_completo_3_pasos(self, escenario):
        mail.outbox = []
        email = 'luis.rojas@test.com'

        # Paso 1: Solicitar codigo
        envio = AuthService().solicitar_codigo_recuperacion(email)
        assert envio and envio['enviado'] is True
        codigo = _codigo_de_correo()

        # Paso 2: Verificar codigo (sin consumirlo prematuramente, emite token de restablecimiento)
        verificacion = AuthService().verificar_codigo_recuperacion(email, codigo)
        assert verificacion['reset_token']
        reset_token = verificacion['reset_token']

        # Paso 3: Restablecer contrasena usando el token
        resultado = AuthService().reset_password(reset_token, 'NuevaClavePaso3!')
        assert resultado['mensaje'] == 'Contrasena actualizada exitosamente'

        escenario['cuenta'].refresh_from_db()
        assert check_password('NuevaClavePaso3!', escenario['cuenta'].password_hash)

        # Verificar que el codigo queda invalidado y no puede reutilizarse
        with pytest.raises(ValueError, match='No hay un codigo vigente'):
            AuthService().reset_password_con_codigo(email, codigo, 'OtraClaveMas123!')

    def test_codigo_de_recuperacion_invalido(self, escenario):
        mail.outbox = []
        AuthService().solicitar_codigo_recuperacion('luis.rojas@test.com')

        with pytest.raises(ValueError):
            AuthService().reset_password_con_codigo('luis.rojas@test.com', '000000', 'OtraClave123!')

    def test_el_tutor_solo_ve_a_sus_estudiantes(self, escenario):
        ac = AccessControlService()

        assert ac.get_tutor(escenario['cuenta']).id == escenario['tutor'].id
        assert ac.get_estudiantes_ids_tutor(escenario['cuenta']) == [escenario['estudiante'].id]
        assert ac.get_estudiantes_autorizados(escenario['cuenta']) == [escenario['estudiante'].id]
        # Un usuario que no es tutor no accede a estudiantes de tutores
        assert ac.get_estudiantes_ids_tutor(escenario['secretaria']) == []

    def test_el_estudiante_siempre_queda_con_tutor_principal(self, escenario):
        segundo_tutor = Tutores.objects.create(
            ci='7777777', nombres='Pedro', primer_apellido='Rojas',
        )
        servicio = EstudianteTutorService()
        estudiante = escenario['estudiante']

        # El primer tutor asignado es el principal
        estudiante.refresh_from_db()
        assert estudiante.tiene_tutor is True
        assert estudiante.tutor_principal.id == escenario['tutor'].id
        assert escenario['tutor'].estudiantes_ids == [estudiante.id]

        # El segundo tutor no desplaza al principal salvo que se indique
        servicio.crear(escenario['secretaria'], {
            'estudiante_id': estudiante.id, 'tutor_id': segundo_tutor.id,
        })
        assert EstudianteTutor.objects.filter(estudiante=estudiante, es_principal=True).count() == 1

        # Marcarlo como principal deja un unico principal
        servicio.crear(escenario['secretaria'], {
            'estudiante_id': estudiante.id, 'tutor_id': segundo_tutor.id, 'es_principal': True,
        })
        assert EstudianteTutor.objects.filter(estudiante=estudiante, es_principal=True).count() == 1
        estudiante.refresh_from_db()
        assert estudiante.tutor_principal.id == segundo_tutor.id