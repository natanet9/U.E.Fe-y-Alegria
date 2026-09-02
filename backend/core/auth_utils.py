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


def get_user_from_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]

    from .models import TokenBlacklist, Usuarios

    if TokenBlacklist.objects.filter(token=token, expira_en__gte=timezone.now()).exists():
        return None

    user_id, token_error = decode_token(token)
    if token_error:
        return None
    try:
        return Usuarios.objects.get(id=int(user_id))
    except (Usuarios.DoesNotExist, ValueError):
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
    from .models import Usuarios
    try:
        return Usuarios.objects.get(id=int(user_id), activo=True)
    except (Usuarios.DoesNotExist, ValueError):
        return None
