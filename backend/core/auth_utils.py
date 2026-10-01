import base64
import hashlib
import hmac
import os
import secrets
import struct
from datetime import timedelta

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone


def get_signer(salt=None):
    salt = salt or getattr(settings, "AUTH_TOKEN_SALT", "ue.panama.auth")
    return TimestampSigner(salt=salt)


def build_token(user_id, salt=None):
    signer = get_signer(salt=salt)
    return signer.sign(str(user_id))


def decode_token(token):
    signer = get_signer()
    max_age = getattr(settings, "AUTH_TOKEN_MAX_AGE", 60 * 60 * 24)

    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_id, None
    except SignatureExpired:
        return None, "TOKEN_EXPIRED"
    except BadSignature:
        return None, "TOKEN_INVALID"


from .models import TokenBlacklist, Usuarios


def get_user_from_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]

    if TokenBlacklist.objects.filter(token=token, expira_en__gte=timezone.now()).exists():
        return None

    user_id, token_error = decode_token(token)
    if token_error:
        return None
    try:
        return Usuarios.objects.get(id=int(user_id))
    except Exception:
        return None


def refresh_token(usuario):
    """Generate a new token for an already-authenticated user."""
    return build_token(usuario.id)


def get_user_from_reset_token(token):
    signer = TimestampSigner(salt='password-reset')
    try:
        user_id = signer.unsign(token, max_age=3600)
    except (SignatureExpired, BadSignature):
        return None
    try:
        return Usuarios.objects.get(id=int(user_id), activo=True)
    except Exception:
        return None


# ── Autenticacion en dos pasos (2FA / OTP) ───────────────────────────────────
# Implementado solo con libreria estandar (sin dependencias extra).

OTP_TOKEN_SALT = 'ue.panama.otp.pending'


def build_otp_token(usuario_id, metodo='email'):
    """Token temporal que certifica que el usuario ya supero el paso 1 (contrasena)."""
    signer = TimestampSigner(salt=OTP_TOKEN_SALT)
    return signer.sign(f'{usuario_id}:{metodo}')


def decode_otp_token(token):
    """Devuelve (usuario_id, metodo) o (None, error)."""
    signer = TimestampSigner(salt=OTP_TOKEN_SALT)
    max_age = getattr(settings, 'OTP_PENDING_TOKEN_MAX_AGE', 60 * 10)
    try:
        payload = signer.unsign(token, max_age=max_age)
    except SignatureExpired:
        return None, 'OTP_EXPIRED'
    except (BadSignature, AttributeError):
        return None, 'OTP_INVALID'

    partes = str(payload).split(':')
    if len(partes) != 2:
        return None, 'OTP_INVALID'
    try:
        return int(partes[0]), partes[1]
    except ValueError:
        return None, 'OTP_INVALID'


def generar_codigo_otp(digitos=None):
    """Codigo numerico aleatorio criptograficamente seguro (por defecto 6 digitos)."""
    digitos = digitos or getattr(settings, 'OTP_CODIGO_DIGITOS', 6)
    maximo = 10 ** digitos
    return str(secrets.randbelow(maximo)).zfill(digitos)


def hash_codigo_otp(codigo, usuario_id=None, proposito='login'):
    """Hash del codigo ligado al usuario y proposito (nunca se guarda en claro)."""
    salt = f'{usuario_id}:{proposito}'
    material = f'{settings.SECRET_KEY}:{salt}:{codigo}'.encode('utf-8')
    return hashlib.sha256(material).hexdigest()


def verificar_codigo_otp(codigo, codigo_hash, usuario_id=None, proposito='login'):
    if not codigo or not codigo_hash:
        return False
    esperado = hash_codigo_otp(str(codigo).strip(), usuario_id=usuario_id, proposito=proposito)
    return hmac.compare_digest(esperado, codigo_hash)


def generar_password_temporal(longitud=10):
    """Contrasena temporal que cumple la politica del frontend."""
    mayusculas = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    minusculas = 'abcdefghijkmnopqrstuvwxyz'
    numeros = '23456789'
    simbolos = '!@#$%*'
    obligatorios = [
        secrets.choice(mayusculas),
        secrets.choice(minusculas),
        secrets.choice(numeros),
        secrets.choice(simbolos),
    ]
    alfabeto = mayusculas + minusculas + numeros + simbolos
    faltan = max(4, int(longitud) - len(obligatorios))
    resto = [secrets.choice(alfabeto) for _ in range(faltan)]
    password = obligatorios + resto
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def generar_codigo_recuperacion(longitud=6):
    return generar_codigo_otp(longitud)


# ── TOTP (RFC 6238) compatible con Google Authenticator / Authy ──────────────

def generar_secreto_totp(bytes_aleatorios=20):
    """Secreto base32 sin padding, listo para apps autenticadoras."""
    return base64.b32encode(os.urandom(bytes_aleatorios)).decode('ascii').rstrip('=')


def _decodificar_secreto(secreto):
    secreto = (secreto or '').strip().replace(' ', '').upper()
    if not secreto:
        raise ValueError('Secreto TOTP vacio')
    padding = '=' * ((8 - len(secreto) % 8) % 8)
    return base64.b32decode(secreto + padding, casefold=True)


def totp_codigo(secreto, momento=None, intervalo=None, digitos=None):
    """Calcula el codigo TOTP vigente para el secreto entregado."""
    intervalo = intervalo or getattr(settings, 'OTP_TOTP_INTERVALO', 30)
    digitos = digitos or getattr(settings, 'OTP_CODIGO_DIGITOS', 6)
    momento = momento or timezone.now()
    timestamp = int(momento.timestamp()) if hasattr(momento, 'timestamp') else int(momento)
    contador = timestamp // int(intervalo)
    clave = _decodificar_secreto(secreto)
    mensaje = struct.pack('>Q', contador)
    digest = hmac.new(clave, mensaje, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    trozo = digest[offset:offset + 4]
    valor = struct.unpack('>I', trozo)[0] & 0x7FFFFFFF
    return str(valor % (10 ** int(digitos))).zfill(int(digitos))


def verificar_totp(secreto, codigo, ventana=None, intervalo=None, digitos=None):
    """Valida el codigo aceptando +/- ventana intervalos por desfase de reloj."""
    if not secreto or not codigo:
        return False
    codigo = str(codigo).strip().replace(' ', '')
    intervalo = intervalo or getattr(settings, 'OTP_TOTP_INTERVALO', 30)
    ventana = getattr(settings, 'OTP_TOTP_VENTANA', 1) if ventana is None else ventana
    ahora = timezone.now()
    for desplazamiento in range(-int(ventana), int(ventana) + 1):
        momento = ahora + timedelta(seconds=desplazamiento * int(intervalo))
        try:
            esperado = totp_codigo(secreto, momento=momento, intervalo=intervalo, digitos=digitos)
        except ValueError:
            return False
        if hmac.compare_digest(esperado, codigo):
            return True
    return False


def otpauth_uri(secreto, cuenta, issuer=None):
    """URI otpauth:// que se entrega al usuario para escanear el QR."""
    issuer = issuer or getattr(settings, 'OTP_ISSUER', 'U.E. Fe y Alegria')
    from urllib.parse import quote
    etiqueta = quote(f'{issuer}:{cuenta}', safe='')
    parametros = f'secret={secreto}&issuer={quote(issuer, safe="")}'
    intervalo = getattr(settings, 'OTP_TOTP_INTERVALO', 30)
    digitos = getattr(settings, 'OTP_CODIGO_DIGITOS', 6)
    return f'otpauth://totp/{etiqueta}?{parametros}&algorithm=SHA1&digits={digitos}&period={intervalo}'


def generar_qr_totp(uri):
    """Genera una imagen de codigo QR en formato data:image/svg+xml;base64 para la URI otpauth."""
    if not uri:
        return None
    try:
        import io
        import qrcode
        import qrcode.image.svg
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(uri, image_factory=factory)
        stream = io.BytesIO()
        img.save(stream)
        svg_bytes = stream.getvalue()
        b64 = base64.b64encode(svg_bytes).decode('ascii')
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return None

