from unittest.mock import patch, MagicMock

import pytest

from core.services.auth_service import AuthService


class TestPasswordReset:

    def test_solicitar_reset_email_exists(self):
        service = AuthService()
        mock_usuario = MagicMock(id=1, email="test@test.com", activo=True)
        with patch.object(service, 'buscar_usuario', return_value=mock_usuario):
            with patch('core.services.auth_service.build_token', return_value='reset_token_123'):
                token = service.solicitar_reset("test@test.com")
                assert token == 'reset_token_123'

    def test_solicitar_reset_email_not_found(self):
        service = AuthService()
        with patch.object(service, 'buscar_usuario', return_value=None):
            result = service.solicitar_reset("noexiste@test.com")
            assert result is None

    def test_reset_password_success(self):
        service = AuthService()
        mock_usuario = MagicMock()
        mock_usuario.id = 1
        mock_usuario.password_hash = "old_hash"
        with patch('core.services.auth_service.get_user_from_reset_token', return_value=mock_usuario):
            with patch('core.services.auth_service.make_password', return_value='new_hash'):
                with patch('core.services.auth_service.OTPService.invalidar_codigos'):
                    result = service.reset_password('valid_token', 'new_pass_123')
                    assert result['mensaje'] == 'Contrasena actualizada exitosamente'
                    # Se actualiza el hash y se limpian las banderas de contrasena temporal
                    mock_usuario.save.assert_called_once()
                    update_fields = mock_usuario.save.call_args.kwargs.get('update_fields')
                    assert 'password_hash' in update_fields
                    assert 'debe_cambiar_password' in update_fields
                    assert mock_usuario.password_hash == 'new_hash'

    def test_reset_password_invalid_token(self):
        service = AuthService()
        with patch('core.services.auth_service.get_user_from_reset_token', return_value=None):
            with pytest.raises(ValueError, match='Token invalido'):
                service.reset_password('bad_token', 'new_pass')

    def test_reset_password_con_codigo_success(self):
        service = AuthService()
        mock_usuario = MagicMock(id=1, email="test@test.com", activo=True)
        with patch.object(service, 'buscar_usuario', return_value=mock_usuario):
            with patch('core.services.auth_service.OTPService.validar_codigo_recuperacion', return_value=(True, None)) as mock_val:
                with patch.object(service, '_aplicar_password'):
                    with patch('core.services.auth_service.OTPService.invalidar_codigos') as mock_inv:
                        result = service.reset_password_con_codigo("test@test.com", "123456", "NewSecret123!")
                        assert result['mensaje'] == 'Contrasena actualizada exitosamente'
                        mock_val.assert_called_once_with(mock_usuario, "123456", consumir=True)
                        mock_inv.assert_called_once_with(mock_usuario, 'recuperacion')
