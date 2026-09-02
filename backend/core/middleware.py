import logging
import time

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone

from .auth_utils import decode_token
from .models import TokenBlacklist, Usuarios


logger = logging.getLogger("core.tracing")


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_header = request.headers.get("X-Timezone")
        if tz_header:
            try:
                import zoneinfo
                zoneinfo.ZoneInfo(tz_header)
                from django.utils import timezone
                timezone.activate(tz_header)
            except Exception:
                pass
        response = self.get_response(request)
        return response


class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        print(f"-> {request.method} {request.path}")
        logger.info("request.start %s %s", request.method, request.path)

        response = self.get_response(request)

        duration = time.time() - start
        print(f"<- {response.status_code} in {duration:.2f}s")
        logger.info(
            "request.end %s %s %s",
            request.method,
            request.path,
            round(duration * 1000, 2),
            extra={"trace_kind": "request", "trace_name": request.path, "elapsed_ms": round(duration * 1000, 2)},
        )
            
        return response


class ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            logger.exception("Internal server error")
            return JsonResponse(
                {"error": "Error interno"},
                status=500,
            )


class AuthMiddleware:
    PUBLIC_PATHS = {
        "/api/health/",
        "/api/auth/login/",
        "/api/login/",
        "/api/auth/forgot-password/",
        "/api/auth/reset-password/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        if settings.API_DOCS_PUBLIC and request.path in {"/api/schema/", "/api/docs/"}:
            return self.get_response(request)

        if request.path in self.PUBLIC_PATHS:
            return self.get_response(request)

        # Try Authorization header first, then fall back to cookie
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        else:
            cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "auth_token")
            token = request.COOKIES.get(cookie_name)

        if not token:
            return JsonResponse({"error": "No autorizado"}, status=401)
        user_id, token_error = decode_token(token)
        if token_error == "TOKEN_EXPIRED":
            return JsonResponse({"error": "Token expirado"}, status=401)
        if token_error == "TOKEN_INVALID":
            return JsonResponse({"error": "Token invalido"}, status=401)

        if TokenBlacklist.objects.filter(token=token, expira_en__gte=timezone.now()).exists():
            return JsonResponse({"error": "Token invalido"}, status=401)

        try:
            usuario = Usuarios.objects.get(id=user_id)
        except Usuarios.DoesNotExist:
            return JsonResponse({"error": "Usuario no encontrado"}, status=401)

        if usuario.activo is False:
            return JsonResponse({"error": "Usuario inactivo"}, status=403)

        request.usuario = usuario

        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("SET app.current_user_id = %s", [str(usuario.id)])

        return self.get_response(request)

