"""Tests unitarios de middlewares"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory, override_settings
from django.http import HttpResponse, JsonResponse
from uuid import uuid4

from core.middleware import LogMiddleware, ErrorMiddleware, AuthMiddleware
from core.models import Usuarios
from core.tests.factories.user_factory import UsuarioFactory


@pytest.mark.django_db
class TestLogMiddleware:
    """Tests para LogMiddleware"""

    def test_log_middleware_processes_request(self, capsys):
        """Verifica que LogMiddleware registra request/response"""
        factory = RequestFactory()
        request = factory.get("/api/test/")

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = LogMiddleware(get_response)

        with patch('builtins.print') as mock_print:
            response = middleware(request)

        assert response.status_code == 200
        # Verify print was called (logging output)
        assert mock_print.call_count >= 2

    def test_log_middleware_timing(self):
        """Verifica que LogMiddleware mide tiempo de respuesta"""
        factory = RequestFactory()
        request = factory.get("/api/test/")

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = LogMiddleware(get_response)

        with patch('time.time', side_effect=[0.0, 0.5, 0.5, 0.5]):  # 500ms response
            with patch('builtins.print'):
                response = middleware(request)

        assert response.status_code == 200

    def test_log_middleware_post_request(self, capsys):
        """Verifica que LogMiddleware registra POST requests"""
        factory = RequestFactory()
        request = factory.post("/api/data/", data={"key": "value"})

        def get_response(req):
            return HttpResponse("Created", status=201)

        middleware = LogMiddleware(get_response)

        with patch('builtins.print') as mock_print:
            response = middleware(request)

        assert response.status_code == 201
        assert mock_print.call_count >= 2


@pytest.mark.django_db
class TestErrorMiddleware:
    """Tests para ErrorMiddleware"""

    def test_error_middleware_normal_response(self):
        """Verifica que ErrorMiddleware retorna response normal sin errores"""
        factory = RequestFactory()
        request = factory.get("/api/test/")

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = ErrorMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200
        assert response.content == b"OK"

    def test_error_middleware_catches_exception(self):
        """Verifica que ErrorMiddleware captura excepciones"""
        factory = RequestFactory()
        request = factory.get("/api/error/")

        def get_response(req):
            raise ValueError("Test error message")

        middleware = ErrorMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 500
        data = json.loads(response.content)
        assert data["error"] == "Error interno"

    def test_error_middleware_handles_runtime_error(self):
        """Verifica que ErrorMiddleware maneja RuntimeError"""
        factory = RequestFactory()
        request = factory.get("/api/test/")

        def get_response(req):
            raise RuntimeError("Runtime problem")

        middleware = ErrorMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 500
        data = json.loads(response.content)
        assert data["error"] == "Error interno"

    def test_error_middleware_handles_database_error(self):
        """Verifica que ErrorMiddleware maneja errores de BD"""
        from django.db import DatabaseError

        factory = RequestFactory()
        request = factory.get("/api/test/")

        def get_response(req):
            raise DatabaseError("Connection failed")

        middleware = ErrorMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 500
        data = json.loads(response.content)
        assert "error" in data


@pytest.mark.django_db
class TestAuthMiddleware:
    """Tests para AuthMiddleware"""

    def test_auth_middleware_allows_non_api_paths(self):
        """Verifica que AuthMiddleware permite paths no-API"""
        factory = RequestFactory()
        request = factory.get("/static/style.css")

        def get_response(req):
            return HttpResponse("CSS content")

        middleware = AuthMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_auth_middleware_allows_public_paths(self):
        """Verifica que AuthMiddleware permite rutas públicas"""
        factory = RequestFactory()

        # Health check
        request = factory.get("/api/health/")
        def get_response(req):
            return JsonResponse({"status": "ok"})

        middleware = AuthMiddleware(get_response)
        response = middleware(request)
        assert response.status_code == 200

    def test_auth_middleware_allows_login_path(self):
        """Verifica que AuthMiddleware permite ruta de login"""
        factory = RequestFactory()
        request = factory.post("/api/auth/login/", data={"email": "test@test.com", "password": "pass"})

        def get_response(req):
            return JsonResponse({"token": "abc123"})

        middleware = AuthMiddleware(get_response)
        response = middleware(request)
        assert response.status_code == 200

    @override_settings(API_DOCS_PUBLIC=True)
    def test_auth_middleware_allows_schema_path_in_local(self):
        """Verifica que AuthMiddleware permite el schema en local"""
        factory = RequestFactory()
        request = factory.get("/api/schema/")

        def get_response(req):
            return JsonResponse({"openapi": "3.0.0"})

        middleware = AuthMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    @override_settings(API_DOCS_PUBLIC=False)
    def test_auth_middleware_blocks_schema_path_in_production(self):
        """Verifica que AuthMiddleware bloquea el schema en producción"""
        factory = RequestFactory()
        request = factory.get("/api/schema/")

        def get_response(req):
            return JsonResponse({"openapi": "3.0.0"})

        middleware = AuthMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["error"] == "No autorizado"

    def test_auth_middleware_rejects_missing_auth_header(self):
        """Verifica que AuthMiddleware rechaza requests sin Authorization"""
        factory = RequestFactory()
        request = factory.get("/api/protected/")

        def get_response(req):
            return HttpResponse("Protected resource")

        middleware = AuthMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["error"] == "No autorizado"

    def test_auth_middleware_rejects_invalid_bearer_format(self):
        """Verifica que AuthMiddleware rechaza formato Bearer inválido"""
        factory = RequestFactory()
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="InvalidToken")

        def get_response(req):
            return HttpResponse("Protected resource")

        middleware = AuthMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["error"] == "No autorizado"

    def test_auth_middleware_rejects_expired_token(self):
        """Verifica que AuthMiddleware rechaza tokens expirados"""
        factory = RequestFactory()
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer expired_token")

        def get_response(req):
            return HttpResponse("Protected resource")

        middleware = AuthMiddleware(get_response)

        with patch('core.middleware.decode_token', return_value=(None, "TOKEN_EXPIRED")):
            response = middleware(request)

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["error"] == "Token expirado"

    def test_auth_middleware_rejects_invalid_token(self):
        """Verifica que AuthMiddleware rechaza tokens inválidos"""
        factory = RequestFactory()
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer invalid_token")

        def get_response(req):
            return HttpResponse("Protected resource")

        middleware = AuthMiddleware(get_response)

        with patch('core.middleware.decode_token', return_value=(None, "TOKEN_INVALID")):
            response = middleware(request)

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["error"] == "Token invalido"

    def test_auth_middleware_rejects_nonexistent_user(self):
        """Verifica que AuthMiddleware rechaza usuario no existente"""
        factory = RequestFactory()
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer valid_token")

        def get_response(req):
            return HttpResponse("Protected resource")

        middleware = AuthMiddleware(get_response)
        fake_user_id = 999999

        with patch('core.middleware.decode_token', return_value=(str(fake_user_id), None)):
            response = middleware(request)

        assert response.status_code == 401
        data = json.loads(response.content)
        assert data["error"] == "Usuario no encontrado"

    def test_auth_middleware_rejects_inactive_user(self):
        """Verifica que AuthMiddleware rechaza usuarios inactivos"""
        factory = RequestFactory()
        
        # Create inactive user
        usuario = UsuarioFactory(activo=False)
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer valid_token")

        def get_response(req):
            return HttpResponse("Protected resource")

        middleware = AuthMiddleware(get_response)

        with patch('core.middleware.decode_token', return_value=(str(usuario.id), None)):
            response = middleware(request)

        assert response.status_code == 403
        data = json.loads(response.content)
        assert data["error"] == "Usuario inactivo"

    def test_auth_middleware_allows_valid_active_user(self):
        """Verifica que AuthMiddleware permite usuarios activos válidos"""
        factory = RequestFactory()
        
        # Create active user
        usuario = UsuarioFactory(activo=True)
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer valid_token")

        def get_response(req):
            assert hasattr(req, 'usuario')
            assert req.usuario.id == usuario.id
            return JsonResponse({"message": "Protected resource accessed"})

        middleware = AuthMiddleware(get_response)

        with patch('core.middleware.decode_token', return_value=(str(usuario.id), None)):
            response = middleware(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert "Protected resource accessed" in data["message"]

    def test_auth_middleware_adds_usuario_to_request(self):
        """Verifica que AuthMiddleware agrega usuario al request"""
        factory = RequestFactory()
        usuario = UsuarioFactory(activo=True)
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer valid_token")

        request_usuario = None

        def get_response(req):
            nonlocal request_usuario
            request_usuario = getattr(req, 'usuario', None)
            return HttpResponse("OK")

        middleware = AuthMiddleware(get_response)

        with patch('core.middleware.decode_token', return_value=(str(usuario.id), None)):
            response = middleware(request)

        assert request_usuario is not None
        assert request_usuario.id == usuario.id
        assert response.status_code == 200

    def test_auth_middleware_handles_bearer_with_extra_spaces(self):
        """Verifica que AuthMiddleware maneja Bearer tokens con espacios extras"""
        factory = RequestFactory()
        usuario = UsuarioFactory(activo=True)
        request = factory.get("/api/protected/", HTTP_AUTHORIZATION="Bearer   valid_token  ")

        def get_response(req):
            return HttpResponse("OK")

        middleware = AuthMiddleware(get_response)

        with patch('core.middleware.decode_token', return_value=(str(usuario.id), None)):
            response = middleware(request)

        assert response.status_code == 200

