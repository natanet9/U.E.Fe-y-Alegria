from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import forgot_password_view, reset_password_view, verify_reset_code_view


class TestForgotPasswordView:

    def test_missing_email(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/forgot-password/", {}, format="json")
        response = forgot_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/forgot-password/", {"email": "admin@test.com"}, format="json")
        with patch("core.views.AuthService.solicitar_reset", return_value="reset_token"):
            with patch("core.views.AuthService.solicitar_codigo_recuperacion", return_value={"enviado": True, "destinatario": "a***@test.com", "expira_en_minutos": 10}):
                response = forgot_password_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["codigo_enviado"] is True

    def test_email_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/forgot-password/", {"email": "no@test.com"}, format="json")
        with patch("core.views.AuthService.solicitar_reset", return_value=None):
            with patch("core.views.AuthService.solicitar_codigo_recuperacion", return_value=None):
                response = forgot_password_view(request)
        assert response.status_code == status.HTTP_200_OK


class TestVerifyResetCodeView:

    def test_missing_fields(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/verify-reset-code/", {}, format="json")
        response = verify_reset_code_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/verify-reset-code/", {"email": "test@test.com", "codigo": "123456"}, format="json")
        with patch("core.views.AuthService.verificar_codigo_recuperacion", return_value={"reset_token": "valid_tok", "mensaje": "ok"}):
            response = verify_reset_code_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["reset_token"] == "valid_tok"

    def test_verify_invalid_code(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/verify-reset-code/", {"email": "test@test.com", "codigo": "000000"}, format="json")
        with patch("core.views.AuthService.verificar_codigo_recuperacion", side_effect=ValueError("Codigo incorrecto")):
            response = verify_reset_code_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Codigo incorrecto" in response.data["error"]


class TestResetPasswordView:

    def test_missing_fields(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/reset-password/", {}, format="json")
        response = reset_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success_with_token(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/reset-password/", {"token": "valid", "new_password": "new_pass_123"}, format="json")
        with patch("core.views.AuthService.reset_password", return_value={"mensaje": "Contrasena actualizada"}):
            response = reset_password_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_success_with_email_and_codigo(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/auth/reset-password/",
            {"email": "test@test.com", "codigo": "123456", "new_password": "new_pass_123"},
            format="json",
        )
        with patch("core.views.AuthService.reset_password_con_codigo", return_value={"mensaje": "Contrasena actualizada"}):
            response = reset_password_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_fallback_to_credentials_when_token_fails(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/auth/reset-password/",
            {"token": "expired_tok", "email": "test@test.com", "codigo": "123456", "new_password": "new_pass_123"},
            format="json",
        )
        with patch("core.views.AuthService.reset_password", side_effect=ValueError("Token expirado")):
            with patch("core.views.AuthService.reset_password_con_codigo", return_value={"mensaje": "Contrasena actualizada"}) as mock_reset_con_codigo:
                response = reset_password_view(request)
        assert response.status_code == status.HTTP_200_OK
        mock_reset_con_codigo.assert_called_once_with("test@test.com", "123456", "new_pass_123")

    def test_invalid_token_without_credentials(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/reset-password/", {"token": "bad", "new_password": "new_pass_123"}, format="json")
        with patch("core.views.AuthService.reset_password", side_effect=ValueError("Token invalido")):
            response = reset_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
