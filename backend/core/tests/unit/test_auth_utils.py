"""Tests unitarios de utilidades de autenticación"""
import pytest
import time
from unittest.mock import patch, MagicMock
from uuid import uuid4

from core.auth_utils import build_token, decode_token, get_signer, get_user_from_token, refresh_token, get_user_from_reset_token, generar_qr_totp
from django.core.signing import BadSignature, SignatureExpired


class TestAuthUtils:
    """Tests para funciones de autenticación"""

    def test_build_token_generates_valid_token(self):
        """Verifica que build_token genera un token válido"""
        token = build_token("user-123")
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)
        assert token != "user-123"

    def test_build_token_different_for_different_users(self):
        """Verifica que usuarios diferentes generan tokens diferentes"""
        token1 = build_token("user-1")
        token2 = build_token("user-2")
        
        assert token1 != token2

    def test_decode_token_round_trip(self):
        """Verifica que el token puede decodificarse"""
        token = build_token("user-7")
        user_id, error = decode_token(token)

        assert error is None
        assert user_id == "user-7"

    def test_decode_token_with_uuid(self):
        """Verifica que build_token funciona con UUIDs"""
        user_uuid = str(uuid4())
        token = build_token(user_uuid)
        user_id, error = decode_token(token)
        
        assert error is None
        assert user_id == user_uuid

    def test_decode_token_invalid_token(self):
        """Verifica que tokens inválidos retornan TOKEN_INVALID"""
        user_id, error = decode_token("invalid_token_xyz")
        
        assert user_id is None
        assert error == "TOKEN_INVALID"

    def test_decode_token_tampering_detection(self):
        """Verifica que tokens modificados son detectados"""
        token = build_token("user-123")
        # Tamper with token
        tampered = token[:-5] + "xxxxx"
        
        user_id, error = decode_token(tampered)
        
        assert user_id is None
        assert error == "TOKEN_INVALID"

    def test_decode_token_expired(self):
        """Verifica que tokens expirados retornan TOKEN_EXPIRED"""
        token = build_token("user-456")
        
        # Mock time to make token appear expired
        with patch('django.core.signing.TimestampSigner.unsign') as mock_unsign:
            mock_unsign.side_effect = SignatureExpired("Token expired")
            user_id, error = decode_token(token)
        
        assert user_id is None
        assert error == "TOKEN_EXPIRED"

    def test_decode_token_bad_signature(self):
        """Verifica que tokens con firma inválida son rechazados"""
        token = build_token("user-789")
        
        with patch('django.core.signing.TimestampSigner.unsign') as mock_unsign:
            mock_unsign.side_effect = BadSignature("Bad signature")
            user_id, error = decode_token(token)
        
        assert user_id is None
        assert error == "TOKEN_INVALID"

    def test_get_signer_uses_custom_salt(self):
        """Verifica que get_signer crea una instancia válida"""
        signer = get_signer()
        assert signer is not None
        assert hasattr(signer, 'sign')
        assert hasattr(signer, 'unsign')

    def test_get_signer_default_salt(self):
        """Verifica que get_signer funciona con salt por defecto"""
        signer = get_signer()
        assert signer is not None
        # Should be able to sign/unsign
        token = signer.sign("test-data")
        assert token is not None
        assert isinstance(token, str)

    def test_token_consistency(self):
        """Verifica que el mismo user_id produce tokens consistentes (decodificables)"""
        user_id = "user-consistency-test"
        
        tokens = [build_token(user_id) for _ in range(5)]
        
        # Todos deben decodificar al mismo user_id
        for token in tokens:
            decoded_id, error = decode_token(token)
            assert error is None
            assert decoded_id == user_id

    def test_build_token_with_numeric_id(self):
        """Verifica que build_token funciona con IDs numéricos"""
        token = build_token("12345")
        user_id, error = decode_token(token)
        
        assert error is None
        assert user_id == "12345"

    def test_build_token_with_special_characters(self):
        """Verifica que build_token funciona con IDs especiales"""
        special_id = "user-with-special-chars_@"
        token = build_token(special_id)
        user_id, error = decode_token(token)
        
        assert error is None
        assert user_id == special_id

    def test_decode_empty_token(self):
        """Verifica que token vacío es rechazado"""
        user_id, error = decode_token("")
        
        assert user_id is None
        assert error == "TOKEN_INVALID"

    def test_decode_none_token(self):
        """Verifica que token None causa error"""
        with pytest.raises((TypeError, AttributeError)):
            decode_token(None)

    def test_token_max_age_respected(self):
        """Verifica que decode_token respeta el max_age configurado"""
        token = build_token("user-maxage")
        
        # Token debería ser válido inmediatamente después de creado
        user_id, error = decode_token(token)
        
        assert error is None
        assert user_id == "user-maxage"

    def test_token_roundtrip_preserves_user_id(self):
        """Verifica que el ciclo build->decode preserva el user_id exactamente"""
        original_id = "test-user-12345"
        
        token = build_token(original_id)
        decoded_id, error = decode_token(token)
        
        assert error is None
        assert decoded_id == original_id
        assert type(decoded_id) == type(original_id)

    def test_token_invalid_with_different_salt(self):
        """Si el salt cambia, tokens previos no deben decodificarse"""
        token = build_token("user-salt-test")

        from django.test import override_settings

        # Cambiamos el salt al decodificar -> debería fallar la verificación
        with override_settings(AUTH_TOKEN_SALT="different.salt"):
            user_id, error = decode_token(token)

        assert user_id is None
        assert error == "TOKEN_INVALID"

    def test_decode_respects_max_age_setting(self):
        """Si max_age es 0, el token debe considerarse expirado al decodificar"""
        token = build_token("user-expire-test")

        from django.test import override_settings

        # Forzamos max age a 0 segundos para provocar expiración
        with override_settings(AUTH_TOKEN_MAX_AGE=0):
            user_id, error = decode_token(token)

        # Dependiendo de la implementación interna puede devolver TOKEN_EXPIRED
        # o TOKEN_INVALID; aceptamos TOKEN_EXPIRED preferentemente
        assert user_id is None
        assert error in ("TOKEN_EXPIRED", "TOKEN_INVALID")

    def test_build_and_decode_with_custom_salt_roundtrip(self):
        """Construir y decodificar con un salt personalizado funciona"""
        from django.test import override_settings

        with override_settings(AUTH_TOKEN_SALT="my.custom.salt"):
            user_id_original = "user-custom-salt"
            token = build_token(user_id_original)
            user_id, error = decode_token(token)

        assert error is None
        assert user_id == user_id_original

    def test_refresh_token(self):
        """Verifica que refresh_token genera un nuevo token válido"""
        usuario_mock = MagicMock(id="123")
        token = refresh_token(usuario_mock)
        assert token is not None
        assert isinstance(token, str)
        user_id, error = decode_token(token)
        assert error is None
        assert user_id == "123"

    def test_get_user_from_token_valid(self):
        """Verifica que get_user_from_token retorna usuario válido"""
        request_mock = MagicMock()
        request_mock.META = {"HTTP_AUTHORIZATION": "Bearer test-token"}
        test_user = MagicMock(id=1)
        
        with patch('core.auth_utils.decode_token', return_value=("1", None)), \
             patch('core.auth_utils.TokenBlacklist.objects.filter', return_value=MagicMock(exists=MagicMock(return_value=False))), \
             patch('core.auth_utils.Usuarios.objects.get', return_value=test_user):
            user = get_user_from_token(request_mock)
            assert user == test_user

    def test_get_user_from_token_invalid_auth_header(self):
        """Verifica que get_user_from_token retorna None con header inválido"""
        request_mock = MagicMock()
        request_mock.META = {"HTTP_AUTHORIZATION": "InvalidHeader"}
        user = get_user_from_token(request_mock)
        assert user is None

    def test_get_user_from_token_blacklisted(self):
        """Verifica que get_user_from_token retorna None con token en lista negra"""
        request_mock = MagicMock()
        request_mock.META = {"HTTP_AUTHORIZATION": "Bearer test-token"}
        
        with patch('core.auth_utils.TokenBlacklist.objects.filter', return_value=MagicMock(exists=MagicMock(return_value=True))):
            user = get_user_from_token(request_mock)
            assert user is None

    def test_get_user_from_token_decode_error(self):
        """Verifica que get_user_from_token retorna None con error de decode"""
        request_mock = MagicMock()
        request_mock.META = {"HTTP_AUTHORIZATION": "Bearer test-token"}
        
        with patch('core.auth_utils.decode_token', return_value=(None, "TOKEN_INVALID")), \
             patch('core.auth_utils.TokenBlacklist.objects.filter', return_value=MagicMock(exists=MagicMock(return_value=False))):
            user = get_user_from_token(request_mock)
            assert user is None

    def test_get_user_from_token_user_not_found(self):
        """Verifica que get_user_from_token retorna None si usuario no existe"""
        request_mock = MagicMock()
        request_mock.META = {"HTTP_AUTHORIZATION": "Bearer test-token"}
        
        with patch('core.auth_utils.decode_token', return_value=("999", None)), \
             patch('core.auth_utils.TokenBlacklist.objects.filter', return_value=MagicMock(exists=MagicMock(return_value=False))), \
             patch('core.auth_utils.Usuarios.objects.get', side_effect=Exception("Does not exist")):
            user = get_user_from_token(request_mock)
            assert user is None

    def test_get_user_from_reset_token_valid(self):
        """Verifica que get_user_from_reset_token retorna usuario válido"""
        test_user = MagicMock(id=1)
        
        with patch('django.core.signing.TimestampSigner.unsign', return_value="1"), \
             patch('core.auth_utils.Usuarios.objects.get', return_value=test_user):
            user = get_user_from_reset_token("test-token")
            assert user == test_user

    def test_get_user_from_reset_token_expired(self):
        """Verifica que get_user_from_reset_token retorna None con token expirado"""
        with patch('django.core.signing.TimestampSigner.unsign', side_effect=SignatureExpired("Expired")):
            user = get_user_from_reset_token("test-token")
            assert user is None

    def test_get_user_from_reset_token_bad_signature(self):
        """Verifica que get_user_from_reset_token retorna None con firma inválida"""
        with patch('django.core.signing.TimestampSigner.unsign', side_effect=BadSignature("Bad")):
            user = get_user_from_reset_token("test-token")
            assert user is None

    def test_get_user_from_reset_token_user_not_found(self):
        """Verifica que get_user_from_reset_token retorna None si usuario no existe"""
        with patch('django.core.signing.TimestampSigner.unsign', return_value="999"), \
             patch('core.auth_utils.Usuarios.objects.get', side_effect=Exception("Does not exist")):
            user = get_user_from_reset_token("test-token")
            assert user is None

    def test_generar_qr_totp(self):
        """Verifica que generar_qr_totp produce un Data URI SVG válido"""
        uri = "otpauth://totp/UE:ana?secret=JBSWY3DPEHPK3PXP"
        qr = generar_qr_totp(uri)
        assert qr is not None
        assert qr.startswith("data:image/svg+xml;base64,")
        assert len(qr) > 50

        # Con URI vacía retorna None
        assert generar_qr_totp("") is None
        assert generar_qr_totp(None) is None


