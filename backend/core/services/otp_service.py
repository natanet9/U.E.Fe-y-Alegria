"""Servicio de autenticacion en dos pasos (2FA/OTP).

Soporta dos metodos:
  * email -> codigo numerico enviado al correo del usuario
  * totp  -> codigo temporal de aplicacion autenticadora (RFC 6238)

Tambien genera contrasenas temporales para cuentas nuevas (tutores) y los
codigos de recuperacion de contrasena.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ..auth_utils import (
    build_otp_token,
    decode_otp_token,
    generar_codigo_otp,
    generar_password_temporal,
    generar_qr_totp,
    generar_secreto_totp,
    hash_codigo_otp,
    otpauth_uri,
    verificar_codigo_otp,
    verificar_totp,
)
from ..models import CodigoVerificacion
from ..tracing import trace_service_class
from .audit_service import AuditService
from .email_service import EmailService


class OTPError(ValueError):
    """Error controlado del flujo OTP (se traduce a HTTP 400/403)."""


@trace_service_class
class OTPService:

    PROPOSITOS_VALIDOS = {'login', 'recuperacion', 'activar_otp', 'desactivar_otp', 'credenciales'}

    def __init__(self):
        self.email = EmailService()
        self.audit = AuditService()

    # ── Utilidades ───────────────────────────────────────────────────────────
    def generar_password_temporal(self, longitud=10):
        return generar_password_temporal(longitud)

    def _ttl(self, proposito):
        if proposito == 'login':
            return int(getattr(settings, 'OTP_LOGIN_TTL_MINUTOS', 5))
        return int(getattr(settings, 'OTP_TTL_MINUTOS', 10))

    def _max_intentos(self):
        return int(getattr(settings, 'OTP_MAX_INTENTOS', 5))

    @staticmethod
    def enmascarar_email(email):
        email = (email or '').strip()
        if '@' not in email:
            return email or ''
        usuario, dominio = email.split('@', 1)
        visible = usuario[:2] if len(usuario) > 2 else usuario[:1]
        return f'{visible}{"*" * max(1, len(usuario) - len(visible))}@{dominio}'

    def email_destino(self, usuario):
        """Correo personal del usuario (respaldo: correo institucional)."""
        return self.email.correo_de(usuario)

    def cuenta_otp(self, usuario):
        """Nombre que identifica la cuenta en la app autenticadora."""
        return (
            (getattr(usuario, 'usuario', '') or '').strip()
            or self.email_destino(usuario)
            or str(getattr(usuario, 'id', ''))
        )

    def invalidar_codigos(self, usuario, proposito):
        return CodigoVerificacion.objects.filter(
            usuario=usuario, proposito=proposito, usado=False,
        ).update(usado=True, usado_en=timezone.now())

    def limpiar_expirados(self, dias=1):
        limite = timezone.now() - timedelta(days=dias)
        return CodigoVerificacion.objects.filter(expira_en__lt=limite).delete()

    # ── Codigos por correo ───────────────────────────────────────────────────
    def crear_codigo(self, usuario, proposito, metodo='email', ttl_minutos=None, enviado_a=None, ip=None):
        if proposito not in self.PROPOSITOS_VALIDOS:
            raise OTPError('Proposito de codigo no soportado')

        ttl = int(ttl_minutos or self._ttl(proposito))
        codigo = generar_codigo_otp()
        self.invalidar_codigos(usuario, proposito)

        CodigoVerificacion.objects.create(
            usuario=usuario,
            proposito=proposito,
            metodo=metodo,
            codigo_hash=hash_codigo_otp(codigo, usuario.id, proposito),
            enviado_a=enviado_a or self.email_destino(usuario),
            expira_en=timezone.now() + timedelta(minutes=ttl),
            ip_address=ip,
        )
        return codigo

    def enviar_codigo(self, usuario, proposito, ip=None, metodo='email', destinatario=None):
        """Crea el codigo y lo envia por correo. Devuelve el detalle del envio."""
        ttl = self._ttl(proposito)
        codigo = self.crear_codigo(
            usuario, proposito, metodo=metodo, ttl_minutos=ttl,
            enviado_a=destinatario or self.email_destino(usuario), ip=ip,
        )
        enviado = self.email.enviar_codigo(
            usuario, codigo, proposito=proposito, ttl_minutos=ttl, destinatario=destinatario,
        )
        return {
            'enviado': enviado,
            'expira_en_minutos': ttl,
            'destinatario': self.enmascarar_email(destinatario or self.email_destino(usuario)),
            'metodo': metodo,
        }

    def validar_codigo(self, usuario, codigo, proposito, consumir=True):
        """Valida un codigo por correo. Devuelve (ok, mensaje_error)."""
        codigo = str(codigo or '').strip()
        if not codigo:
            return False, 'Debe enviar el codigo de verificacion'

        registro = CodigoVerificacion.objects.filter(
            usuario=usuario, proposito=proposito, usado=False,
        ).order_by('-created_at').first()

        if not registro:
            return False, 'No hay un codigo vigente. Solicita uno nuevo'

        if registro.expira_en < timezone.now():
            registro.usado = True
            registro.usado_en = timezone.now()
            registro.save(update_fields=['usado', 'usado_en'])
            return False, 'El codigo expiro. Solicita uno nuevo'

        if registro.intentos >= self._max_intentos():
            registro.usado = True
            registro.usado_en = timezone.now()
            registro.save(update_fields=['usado', 'usado_en'])
            return False, 'Demasiados intentos fallidos. Solicita un nuevo codigo'

        if not verificar_codigo_otp(codigo, registro.codigo_hash, usuario.id, proposito):
            registro.intentos = registro.intentos + 1
            registro.save(update_fields=['intentos'])
            restantes = max(0, self._max_intentos() - registro.intentos)
            return False, f'Codigo incorrecto. Intentos restantes: {restantes}'

        if consumir:
            registro.usado = True
            registro.usado_en = timezone.now()
            registro.save(update_fields=['usado', 'usado_en'])
        return True, None

    # ── TOTP ─────────────────────────────────────────────────────────────────
    def validar_totp(self, usuario, codigo):
        secreto = getattr(usuario, 'otp_secret', None)
        if not secreto:
            return False, 'Este usuario no tiene configurada una aplicacion autenticadora'
        codigo = str(codigo or '').strip()
        if len(codigo) != int(getattr(settings, 'OTP_CODIGO_DIGITOS', 6)):
            return False, 'El codigo debe tener 6 digitos'
        if not verificar_totp(secreto, codigo):
            return False, 'Codigo de autenticacion incorrecto'
        return True, None

    def generar_secreto_totp(self):
        return generar_secreto_totp()

    def uri_totp(self, usuario, secreto=None):
        secreto = secreto or getattr(usuario, 'otp_secret', None)
        return otpauth_uri(secreto, self.cuenta_otp(usuario))

    # ── Flujo de login en dos pasos ──────────────────────────────────────────
    def iniciar_desafio_login(self, usuario, ip=None):
        """Genera el desafio 2FA posterior a la validacion de la contrasena."""
        metodo = getattr(usuario, 'otp_metodo', 'email') or 'email'
        payload = {
            'requires_otp': True,
            'metodo': metodo,
            'otp_token': build_otp_token(usuario.id, metodo),
            'expira_en_minutos': int(getattr(settings, 'OTP_PENDING_TOKEN_MAX_AGE', 600)) // 60,
        }
        if metodo == 'totp':
            payload['mensaje'] = 'Ingresa el codigo de tu aplicacion autenticadora'
            payload['destinatario'] = None
        else:
            envio = self.enviar_codigo(usuario, 'login', ip=ip)
            payload.update({
                'mensaje': 'Te enviamos un codigo de verificacion a tu correo',
                'destinatario': envio['destinatario'],
                'correo_enviado': envio['enviado'],
                'expira_en_minutos': envio['expira_en_minutos'],
            })
        return payload

    def verificar_desafio_login(self, otp_token, codigo):
        """Valida el token pendiente + codigo. Devuelve (usuario, error)."""
        if not otp_token or not codigo:
            return None, 'Debe enviar el token y el codigo de verificacion'

        from ..models import Usuarios

        usuario_id, metodo = decode_otp_token(otp_token)
        if not usuario_id:
            if metodo == 'OTP_EXPIRED':
                return None, 'La verificacion expiro. Vuelve a iniciar sesion'
            return None, 'Token de verificacion invalido'

        try:
            usuario = Usuarios.objects.select_related('rol').get(id=usuario_id)
        except Usuarios.DoesNotExist:
            return None, 'Usuario no encontrado'

        if not usuario.activo:
            return None, 'Usuario inactivo'

        if metodo == 'totp':
            ok, error = self.validar_totp(usuario, codigo)
        else:
            ok, error = self.validar_codigo(usuario, codigo, 'login')

        if not ok:
            usuario.intentos_otp_fallidos = (usuario.intentos_otp_fallidos or 0) + 1
            usuario.save(update_fields=['intentos_otp_fallidos'])
            return None, error

        usuario.intentos_otp_fallidos = 0
        usuario.save(update_fields=['intentos_otp_fallidos'])
        return usuario, None

    def reenviar_codigo_login(self, otp_token, ip=None):
        from ..models import Usuarios

        usuario_id, metodo = decode_otp_token(otp_token)
        if not usuario_id:
            if metodo == 'OTP_EXPIRED':
                raise OTPError('La verificacion expiro. Vuelve a iniciar sesion')
            raise OTPError('Token de verificacion invalido')

        usuario = Usuarios.objects.select_related('rol').filter(id=usuario_id, activo=True).first()
        if not usuario:
            raise OTPError('Usuario no encontrado')
        if (getattr(usuario, 'otp_metodo', 'email') or 'email') == 'totp':
            raise OTPError('Este usuario usa aplicacion autenticadora, no requiere reenvio')

        envio = self.enviar_codigo(usuario, 'login', ip=ip)
        return {
            'mensaje': 'Codigo reenviado a tu correo',
            'destinatario': envio['destinatario'],
            'correo_enviado': envio['enviado'],
            'expira_en_minutos': envio['expira_en_minutos'],
        }

    # ── Gestion del segundo factor ──────────────────────────────────────────
    def habilitar_inicial(self, usuario, metodo='email', actor=None, forzar=None):
        """Activa el segundo factor en cuentas nuevas (tutores, usuarios temporales).

        Se invoca al crear la cuenta con contrasena temporal para que el primer
        ingreso ya exija el codigo. Respeta el ajuste OTP_2FA_POR_DEFECTO del .env.
        """
        if forzar is None:
            forzar = bool(getattr(settings, 'OTP_2FA_POR_DEFECTO', True))
        if not forzar:
            return self.estado(usuario)

        metodo = (metodo or 'email').strip().lower()
        if metodo not in ('email', 'totp'):
            metodo = 'email'

        campos = ['otp_habilitado', 'otp_metodo', 'otp_configurado_en']
        usuario.otp_habilitado = True
        usuario.otp_metodo = metodo
        usuario.otp_configurado_en = timezone.now()
        if metodo == 'email':
            usuario.otp_secret = None
            campos.append('otp_secret')
        usuario.save(update_fields=campos)

        self.audit.record(
            actor or usuario, accion='OTP_ENABLE', tabla='usuarios',
            registro_id=usuario.id,
            datos_nuevo={'otp_metodo': metodo, 'origen': 'alta_cuenta'},
        )
        return self.estado(usuario)

    def estado(self, usuario):
        return {
            'otp_habilitado': bool(getattr(usuario, 'otp_habilitado', False)),
            'otp_metodo': getattr(usuario, 'otp_metodo', 'totp') or 'totp',
            'otp_configurado_en': (
                usuario.otp_configurado_en.isoformat()
                if getattr(usuario, 'otp_configurado_en', None) else None
            ),
            'configuracion_pendiente': bool(getattr(usuario, 'otp_secret', None)) and not bool(
                getattr(usuario, 'otp_habilitado', False)
            ),
            'email': usuario.email,
            'email_enmascarado': self.enmascarar_email(self.email_destino(usuario)),
            'usuario': (getattr(usuario, 'usuario', '') or '').strip() or None,
            'correo_personal': getattr(usuario, 'correo_personal', None),
            'correo_personal_enmascarado': self.enmascarar_email(getattr(usuario, 'correo_personal', None)),
            'opciones': ['totp'],
        }

    def iniciar_configuracion(self, usuario, metodo='totp', ip=None):
        """Prepara el segundo factor con Google Authenticator (TOTP con QR)."""
        metodo = (metodo or 'totp').strip().lower()
        if metodo not in ('email', 'totp'):
            raise OTPError('Metodo 2FA no soportado')

        usuario.otp_metodo = metodo
        usuario.otp_habilitado = False

        if metodo == 'totp':
            secreto = generar_secreto_totp()
            usuario.otp_secret = secreto
            usuario.save(update_fields=['otp_metodo', 'otp_habilitado', 'otp_secret'])
            uri = otpauth_uri(secreto, self.cuenta_otp(usuario))
            qr_data = generar_qr_totp(uri)
            return {
                'metodo': 'totp',
                'secreto': secreto,
                'otpauth_uri': uri,
                'qr_code': qr_data,
                'issuer': getattr(settings, 'OTP_ISSUER', 'U.E. Fe y Alegria'),
                'cuenta': self.cuenta_otp(usuario),
                'mensaje': 'Escanea el codigo QR con Google Authenticator o tu app autenticadora y confirma con el codigo',
            }

        usuario.otp_secret = None
        usuario.save(update_fields=['otp_metodo', 'otp_habilitado', 'otp_secret'])
        envio = self.enviar_codigo(usuario, 'activar_otp', ip=ip)
        return {
            'metodo': 'email',
            'mensaje': 'Te enviamos un codigo para confirmar la activacion',
            'destinatario': envio['destinatario'],
            'correo_enviado': envio['enviado'],
            'expira_en_minutos': envio['expira_en_minutos'],
        }

    def confirmar_configuracion(self, usuario, codigo):
        metodo = (getattr(usuario, 'otp_metodo', 'email') or 'email')
        if metodo == 'totp':
            ok, error = self.validar_totp(usuario, codigo)
        else:
            ok, error = self.validar_codigo(usuario, codigo, 'activar_otp')
        if not ok:
            return None, error

        usuario.otp_habilitado = True
        usuario.otp_configurado_en = timezone.now()
        usuario.save(update_fields=['otp_habilitado', 'otp_configurado_en'])
        self.audit.record(
            usuario, accion='OTP_ENABLE', tabla='usuarios',
            registro_id=usuario.id, datos_nuevo={'otp_metodo': metodo},
        )
        return self.estado(usuario), None

    def deshabilitar(self, usuario, codigo=None, password=None):
        """Desactiva el segundo factor. Sin codigo requiere la contrasena."""
        from django.contrib.auth.hashers import check_password

        if (getattr(usuario, 'otp_metodo', 'email') or 'email') == 'totp' and codigo:
            ok, error = self.validar_totp(usuario, codigo)
        elif codigo:
            ok, error = self.validar_codigo(usuario, codigo, 'desactivar_otp')
        elif password is not None:
            if check_password(password, usuario.password_hash):
                ok, error = True, None
            else:
                ok, error = False, 'Contrasena incorrecta'
        else:
            ok, error = False, 'Debe confirmar con su contrasena o un codigo de verificacion'

        if not ok:
            return None, error

        usuario.otp_habilitado = False
        usuario.otp_secret = None
        usuario.otp_configurado_en = None
        usuario.intentos_otp_fallidos = 0
        usuario.save(update_fields=['otp_habilitado', 'otp_secret', 'otp_configurado_en', 'intentos_otp_fallidos'])
        self.audit.record(
            usuario, accion='OTP_DISABLE', tabla='usuarios',
            registro_id=usuario.id, datos_nuevo={'otp_habilitado': False},
        )
        return self.estado(usuario), None

    # ── Recuperacion de contrasena por codigo ────────────────────────────────
    def iniciar_recuperacion(self, usuario, ip=None):
        return self.enviar_codigo(usuario, 'recuperacion', ip=ip)

    def validar_codigo_recuperacion(self, usuario, codigo, consumir=True):
        return self.validar_codigo(usuario, codigo, 'recuperacion', consumir=consumir)