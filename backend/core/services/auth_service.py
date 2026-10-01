from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.utils import timezone

from ..auth_utils import build_token, get_user_from_reset_token, refresh_token
from ..models import AuditLog, Usuarios
from ..tracing import trace_service_class
from .email_service import EmailService
from .otp_service import OTPError, OTPService


@trace_service_class
class AuthService:

    @staticmethod
    def buscar_usuario(identificador):
        """Busca un usuario por nombre de usuario, correo institucional o correo personal."""
        valor = (identificador or '').strip()
        if not valor:
            return None
        return Usuarios.objects.select_related('rol').filter(
            Q(usuario__iexact=valor) | Q(email__iexact=valor) | Q(correo_personal__iexact=valor),
        ).first()

    def login(self, email, password, ip=None):
        """Valida las credenciales.

        `email` acepta el nombre de usuario, el correo institucional o el correo personal.
        """
        password = (password or '').strip()
        usuario = self.buscar_usuario(email)
        if usuario is None:
            return None, "Credenciales invalidas"

        if not usuario.activo:
            return None, "Usuario inactivo"

        if not check_password(password, usuario.password_hash):
            return None, "Credenciales invalidas"

        # Segundo factor: no se emite el token definitivo hasta verificar el codigo
        if getattr(usuario, 'otp_habilitado', False) is True:
            return self._iniciar_desafio_2fa(usuario, ip=ip), None

        usuario.last_login = timezone.now()
        usuario.save(update_fields=['last_login'])

        token = build_token(usuario.id)
        return self._build_response(usuario, token), None

    def _iniciar_desafio_2fa(self, usuario, ip=None):
        desafio = OTPService().iniciar_desafio_login(usuario, ip=ip)
        desafio['usuario'] = self._user_payload(usuario)
        return desafio

    def verify_otp(self, otp_token, codigo):
        """Completa el login validando el segundo factor. Devuelve (data, error)."""
        usuario, error = OTPService().verificar_desafio_login(otp_token, codigo)
        if error:
            return None, error

        usuario.last_login = timezone.now()
        usuario.save(update_fields=['last_login'])

        token = build_token(usuario.id)
        return self._build_response(usuario, token), None

    def reenviar_codigo_otp(self, otp_token, ip=None):
        try:
            return OTPService().reenviar_codigo_login(otp_token, ip=ip), None
        except OTPError as exc:
            return None, str(exc)

    def change_password(self, usuario, old_password, new_password):
        if not check_password(old_password, usuario.password_hash):
            return None, "Contrasena actual incorrecta"

        if len(new_password) < 6:
            return None, "Nueva contrasena debe tener al menos 6 caracteres"

        if check_password(new_password, usuario.password_hash):
            return None, "La nueva contrasena debe ser distinta a la actual"

        self._aplicar_password(usuario, new_password, registrar_auditoria=True)

        return {'mensaje': 'Contrasena cambiada exitosamente'}, None

    def _aplicar_password(self, usuario, new_password, registrar_auditoria=True, notificar=True):
        """Guarda la contrasena y limpia las banderas de contrasena temporal."""
        usuario.password_hash = make_password(new_password)
        usuario.password_temporal = False
        usuario.debe_cambiar_password = False
        usuario.password_cambiada_en = timezone.now()
        usuario.save(update_fields=[
            'password_hash', 'password_temporal', 'debe_cambiar_password', 'password_cambiada_en',
        ])

        if registrar_auditoria:
            try:
                AuditLog.objects.create(
                    tabla='usuarios',
                    registro_id=usuario.id,
                    accion='UPDATE',
                    usuario=usuario,
                    datos_nuevo={'password_changed': True},
                )
            except Exception:
                # La auditoria nunca debe impedir el cambio de contrasena
                pass

        if notificar:
            try:
                EmailService().enviar_aviso_password_actualizada(usuario)
            except Exception:
                pass
        return usuario

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
        if 'correo_personal' in data:
            from .validation import validar_email
            correo = (data['correo_personal'] or '').strip().lower()
            validar_email(correo)
            if Usuarios.objects.filter(correo_personal__iexact=correo).exclude(id=usuario.id).exists():
                raise ValueError('Ese correo personal ya esta registrado por otro usuario')
            usuario.correo_personal = correo
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
        payload = {
            'id': usuario.id,
            'ci': usuario.ci,
            'nombre': usuario.nombre,
            'primer_apellido': usuario.primer_apellido,
            'segundo_apellido': usuario.segundo_apellido,
            'nombre_completo': usuario.nombre_completo,
            'usuario': (getattr(usuario, 'usuario', '') or '').strip() or None,
            'email': usuario.email,
            'correo_personal': getattr(usuario, 'correo_personal', None),
            'rol': usuario.rol.nombre if usuario.rol else None,
            'rol_id': usuario.rol_id,
            'activo': usuario.activo,
            'last_login': usuario.last_login.isoformat() if usuario.last_login else None,
            'password_temporal': bool(getattr(usuario, 'password_temporal', False)),
            'debe_cambiar_password': bool(getattr(usuario, 'debe_cambiar_password', False)),
            'otp_habilitado': bool(getattr(usuario, 'otp_habilitado', False)),
            'otp_metodo': getattr(usuario, 'otp_metodo', 'email') or 'email',
            'tutor_id': self._tutor_id(usuario),
        }
        return payload

    @staticmethod
    def _tutor_id(usuario):
        try:
            tutor = getattr(usuario, 'tutor', None)
            tutor_id = getattr(tutor, 'id', None)
        except Exception:
            return None
        return tutor_id if isinstance(tutor_id, int) else None

    # ─ Recuperacion de contrasena ───────────────────────────────────────────
    def solicitar_reset(self, email):
        """Genera el token de cambio de contrasena. Acepta usuario o cualquier correo."""
        usuario = self.buscar_usuario(email)
        if usuario is None or not usuario.activo:
            return None
        reset_token = build_token(usuario.id, salt='password-reset')
        return reset_token

    def solicitar_codigo_recuperacion(self, email, ip=None):
        """Genera y envia un codigo de recuperacion al correo personal."""
        usuario = self.buscar_usuario(email)
        if usuario is None or not usuario.activo:
            return None
        try:
            envio = OTPService().iniciar_recuperacion(usuario, ip=ip)
        except Exception:
            return None
        return {'usuario_id': usuario.id, **envio}

    def verificar_codigo_recuperacion(self, email, codigo):
        """Valida el codigo del correo y entrega un token temporal de cambio."""
        if not (email or '').strip() or not codigo:
            raise ValueError('Debe enviar email y codigo')

        usuario = self.buscar_usuario(email)
        if usuario is None or not usuario.activo:
            raise ValueError('Codigo invalido o expirado')

        ok, error = OTPService().validar_codigo_recuperacion(usuario, codigo, consumir=False)
        if not ok:
            raise ValueError(error)

        return {
            'reset_token': build_token(usuario.id, salt='password-reset'),
            'mensaje': 'Codigo verificado correctamente',
        }

    def reset_password(self, reset_token, new_password):
        usuario = get_user_from_reset_token(reset_token)
        if not usuario:
            raise ValueError('Token invalido o expirado')
        self._aplicar_password(usuario, new_password)
        OTPService().invalidar_codigos(usuario, 'recuperacion')
        return {'mensaje': 'Contrasena actualizada exitosamente'}

    def reset_password_con_codigo(self, email, codigo, new_password):
        if not (email or '').strip() or not codigo or not new_password:
            raise ValueError('Debe enviar email, codigo y nueva contrasena')

        usuario = self.buscar_usuario(email)
        if usuario is None or not usuario.activo:
            raise ValueError('Codigo invalido o expirado')

        ok, error = OTPService().validar_codigo_recuperacion(usuario, codigo, consumir=True)
        if not ok:
            raise ValueError(error)

        self._aplicar_password(usuario, new_password)
        OTPService().invalidar_codigos(usuario, 'recuperacion')
        return {'mensaje': 'Contrasena actualizada exitosamente'}

    def refresh(self, usuario):
        new_token = refresh_token(usuario)
        return {'token': new_token, 'usuario': self.get_me(usuario)}

    def _build_response(self, usuario, token):
        return {
            'token': token,
            'usuario': self._user_payload(usuario),
        }
