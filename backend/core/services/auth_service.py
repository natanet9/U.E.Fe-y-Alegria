from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from ..auth_utils import build_token, get_user_from_reset_token, refresh_token
from ..models import AuditLog, Usuarios
from ..tracing import trace_service_class


@trace_service_class
class AuthService:

    def login(self, email, password):
        email = (email or '').strip().lower()
        password = (password or '').strip()
        try:
            usuario = Usuarios.objects.select_related('rol').get(email=email)
        except Usuarios.DoesNotExist:
            return None, "Credenciales invalidas"

        if not usuario.activo:
            return None, "Usuario inactivo"

        if not check_password(password, usuario.password_hash):
            return None, "Credenciales invalidas"

        usuario.last_login = timezone.now()
        usuario.save(update_fields=['last_login'])

        token = build_token(usuario.id)
        return self._build_response(usuario, token), None

    def change_password(self, usuario, old_password, new_password):
        if not check_password(old_password, usuario.password_hash):
            return None, "Contrasena actual incorrecta"

        if len(new_password) < 6:
            return None, "Nueva contrasena debe tener al menos 6 caracteres"

        usuario.password_hash = make_password(new_password)
        usuario.save(update_fields=['password_hash'])

        AuditLog.objects.create(
            tabla='usuarios',
            registro_id=usuario.id,
            accion='UPDATE',
            usuario=usuario,
            datos_nuevo={'password_changed': True},
        )

        return {'mensaje': 'Contrasena cambiada exitosamente'}, None

    def get_me(self, usuario):
        return self._user_payload(usuario)

    def actualizar_perfil(self, usuario, data):
        for field in ('nombre', 'primer_apellido', 'segundo_apellido', 'ci'):
            if field in data:
                setattr(usuario, field, data[field])
        if 'email' in data:
            from .validation import validar_email
            validar_email(data['email'])
            usuario.email = data['email']
        usuario.save()
        AuditLog.objects.create(
            tabla='usuarios',
            registro_id=usuario.id,
            accion='UPDATE',
            usuario=usuario,
            datos_nuevo={k: data[k] for k in data if k in data},
        )
        return {'mensaje': 'Perfil actualizado', 'usuario': self._user_payload(usuario)}

    def _user_payload(self, usuario):
        return {
            'id': usuario.id,
            'ci': usuario.ci,
            'nombre': usuario.nombre,
            'primer_apellido': usuario.primer_apellido,
            'segundo_apellido': usuario.segundo_apellido,
            'nombre_completo': usuario.nombre_completo,
            'email': usuario.email,
            'rol': usuario.rol.nombre if usuario.rol else None,
            'rol_id': usuario.rol_id,
            'activo': usuario.activo,
            'last_login': usuario.last_login.isoformat() if usuario.last_login else None,
        }

    def solicitar_reset(self, email):
        email = (email or '').strip().lower()
        try:
            usuario = Usuarios.objects.get(email=email, activo=True)
        except Exception:
            return None
        reset_token = build_token(usuario.id, salt='password-reset')
        return reset_token

    def reset_password(self, reset_token, new_password):
        usuario = get_user_from_reset_token(reset_token)
        if not usuario:
            raise ValueError('Token invalido o expirado')
        usuario.password_hash = make_password(new_password)
        usuario.save(update_fields=['password_hash'])
        return {'mensaje': 'Contrasena actualizada exitosamente'}

    def refresh(self, usuario):
        new_token = refresh_token(usuario)
        return {'token': new_token, 'usuario': self.get_me(usuario)}

    def _build_response(self, usuario, token):
        return {
            'token': token,
            'usuario': self._user_payload(usuario),
        }
