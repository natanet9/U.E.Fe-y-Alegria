"""Envio de correos transaccionales (credenciales, codigos OTP, recuperacion).

Configuracion SMTP tomada de `config.settings` (variables del `.env`):
EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
DEFAULT_FROM_EMAIL.

Todos los metodos devuelven True/False y nunca lanzan excepciones: un fallo de
correo no debe romper el flujo de login o de gestion de tutores.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger('core.tracing')

PROPOSITO_TITULOS = {
    'login': 'Codigo de verificacion para iniciar sesion',
    'recuperacion': 'Codigo para restablecer tu contrasena',
    'activar_otp': 'Codigo para activar la verificacion en dos pasos',
    'desactivar_otp': 'Codigo para desactivar la verificacion en dos pasos',
    'credenciales': 'Tus credenciales de acceso',
}


class EmailService:
    """Envia correos usando el backend configurado en settings."""

    def __init__(self):
        self.from_email = (
            getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            or getattr(settings, 'EMAIL_HOST_USER', '')
            or 'no-reply@localhost'
        )

    # ── Configuracion ────────────────────────────────────────────────────────
    def esta_configurado(self):
        backend = str(getattr(settings, 'EMAIL_BACKEND', ''))
        if 'console' in backend or 'locmem' in backend or 'filebased' in backend:
            return True
        return bool(getattr(settings, 'EMAIL_HOST', '')) and bool(getattr(settings, 'EMAIL_HOST_USER', ''))

    @property
    def nombre_institucion(self):
        return getattr(settings, 'OTP_ISSUER', 'U.E. Fe y Alegria')

    def _base_url(self):
        return str(getattr(settings, 'FRONTEND_BASE_URL', '') or '').rstrip('/')

    def asunto(self, texto):
        prefijo = getattr(settings, 'EMAIL_SUBJECT_PREFIX', '[U.E. Fe y Alegria] ')
        return f'{prefijo}{texto}'

    @staticmethod
    def correo_de(usuario):
        """Correo del usuario para notificaciones: personal con respaldo institucional."""
        if usuario is None:
            return None
        return (
            getattr(usuario, 'correo_notificaciones', None)
            or getattr(usuario, 'correo_personal', None)
            or getattr(usuario, 'email', None)
        )

    @staticmethod
    def nombre_usuario_de(usuario, respaldo=None):
        """Nombre de usuario (usuario) o, si no existe, el respaldo indicado."""
        return (getattr(usuario, 'usuario', '') or '').strip() or respaldo or ''

    # ── Envio base ───────────────────────────────────────────────────────────
    def enviar(self, destinatario, asunto, texto, html=None):
        if not destinatario:
            logger.warning('correo.omitido sin destinatario')
            return False
        try:
            mensaje = EmailMultiAlternatives(
                subject=asunto,
                body=texto,
                from_email=self.from_email,
                to=[destinatario],
            )
            if html:
                mensaje.attach_alternative(html, 'text/html')
            enviados = mensaje.send(fail_silently=False)
            logger.info('correo.enviado destino=%s asunto=%s enviados=%s', destinatario, asunto, enviados)
            return bool(enviados)
        except Exception as exc:  # pragma: no cover - depende de la red/SMTP
            logger.warning('correo.error destino=%s asunto=%s error=%s', destinatario, asunto, exc)
            return False

    # ── Plantillas ───────────────────────────────────────────────────────────
    def _html(self, titulo, parrafos, codigo=None):
        cuerpo = ''.join(f'<p style="margin:0 0 12px 0;line-height:1.55">{p}</p>' for p in parrafos)
        bloque_codigo = ''
        if codigo:
            bloque_codigo = (
                '<p style="margin:24px 0;text-align:center">'
                '<span style="display:inline-block;padding:14px 26px;border-radius:12px;'
                'background:#0f172a;color:#ffffff;font-size:26px;letter-spacing:6px;'
                f'font-family:monospace">{codigo}</span></p>'
            )
        return (
            '<div style="font-family:Segoe UI,Arial,sans-serif;color:#0f172a;max-width:560px">'
            f'<h2 style="margin:0 0 16px 0">{titulo}</h2>{cuerpo}{bloque_codigo}'
            f'<p style="margin:24px 0 0 0;font-size:12px;color:#64748b">{self.nombre_institucion}</p>'
            '</div>'
        )

    # ── Correos de negocio ───────────────────────────────────────────────────
    def enviar_codigo(self, usuario, codigo, proposito='login', ttl_minutos=10, destinatario=None):
        destinatario = destinatario or self.correo_de(usuario)
        titulo = PROPOSITO_TITULOS.get(proposito, 'Codigo de verificacion')
        nombre = getattr(usuario, 'nombre_completo', None) or getattr(usuario, 'nombre', '') or 'usuario'
        parrafos = [
            f'Hola {nombre},',
            f'Tu codigo es valido por {ttl_minutos} minutos. No lo compartas con nadie.',
        ]
        if proposito == 'recuperacion':
            parrafos.append('Si no solicitaste el cambio de contrasena, ignora este mensaje.')
        texto = (
            f'{titulo}\n\nHola {nombre},\n\nTu codigo de verificacion es: {codigo}\n'
            f'Valido por {ttl_minutos} minutos.\n\n{self.nombre_institucion}\n'
        )
        return self.enviar(destinatario, self.asunto(titulo), texto, self._html(titulo, parrafos, codigo=codigo))

    def enviar_credenciales(self, usuario, password_temporal, nombre=None):
        destinatario = self.correo_de(usuario)
        nombre_usuario = self.nombre_usuario_de(usuario, respaldo=destinatario)
        nombre = nombre or getattr(usuario, 'nombre_completo', None) or getattr(usuario, 'nombre', '') or 'usuario'
        titulo = 'Credenciales de acceso al panel academico'
        base = self._base_url()
        parrafos = [
            f'Hola {nombre},',
            'Se creo tu cuenta de acceso al panel academico.',
            f'<b>Usuario:</b> {nombre_usuario}',
            f'<b>Correo personal:</b> {destinatario}',
            f'<b>Contrasena temporal:</b> {password_temporal}',
            'Por seguridad deberas cambiar la contrasena la primera vez que ingreses. '
            'Los codigos de verificacion y la recuperacion de contrasena se enviaran a este correo personal.',
        ]
        if base:
            parrafos.append(f'Ingresa en: <a href="{base}/login">{base}/login</a>')
        texto = (
            f'{titulo}\n\nHola {nombre},\n\nSe creo tu cuenta de acceso al panel academico.\n'
            f'Usuario: {nombre_usuario}\nCorreo personal: {destinatario}\n'
            f'Contrasena temporal: {password_temporal}\n\n'
            'Deberas cambiar la contrasena en tu primer ingreso.\n'
            'Los codigos de verificacion y la recuperacion de contrasena se envian a este correo personal.\n'
            + (f'Ingresa en: {base}/login\n' if base else '')
            + f'\n{self.nombre_institucion}\n'
        )
        return self.enviar(
            destinatario, self.asunto(titulo), texto,
            self._html(titulo, parrafos, codigo=password_temporal),
        )

    def enviar_aviso_password_actualizada(self, usuario):
        titulo = 'Tu contrasena fue actualizada'
        nombre = getattr(usuario, 'nombre_completo', None) or getattr(usuario, 'nombre', '') or 'usuario'
        parrafos = [
            f'Hola {nombre},',
            'La contrasena de tu cuenta fue actualizada correctamente.',
            'Si no realizaste este cambio, contacta a la direccion de la unidad educativa.',
        ]
        texto = f'{titulo}\n\n' + '\n'.join(parrafos) + f'\n\n{self.nombre_institucion}\n'
        return self.enviar(
            self.correo_de(usuario), self.asunto(titulo), texto, self._html(titulo, parrafos),
        )
