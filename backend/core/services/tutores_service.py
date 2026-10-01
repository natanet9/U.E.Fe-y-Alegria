from django.contrib.auth.hashers import make_password

from ..models import Tutores, EstudianteTutor, Roles, Usuarios
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .email_service import EmailService
from .otp_service import OTPService
from .validation import (
    validar_required, validar_ci, validar_nombre, validar_telefono, validar_email, ValidationError,
)
from django.db.models.query import QuerySet


@trace_service_class
class TutoresService:
    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()
        self.otp = OTPService()
        self.email = EmailService()

    def listar(self, usuario, query=None, page=None, page_size=None):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        qs = Tutores.objects.all().order_by('primer_apellido', 'nombres')
        if query:
            from django.db.models import Q
            try:
                qs = qs.filter(
                    Q(ci__icontains=query)
                    | Q(nombres__icontains=query)
                    | Q(primer_apellido__icontains=query)
                    | Q(celular__icontains=query)
                )
            except TypeError:
                qs = qs.filter(
                    ci__icontains=query,
                    nombres__icontains=query,
                    primer_apellido__icontains=query,
                    celular__icontains=query,
                )

        if page is None:
            if not isinstance(qs, QuerySet):
                items = qs.__getitem__(slice(None)) if hasattr(qs, '__getitem__') else list(qs)
                total = qs.count() if hasattr(qs, 'count') else len(items)
                return {
                    'data': [self._to_dict(t) for t in items],
                    'total': total,
                    'page': 1,
                    'page_size': total,
                    'total_pages': 1,
                }
            return [self._to_dict(t) for t in qs]

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]
        return {
            'data': [self._to_dict(t) for t in items],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    @staticmethod
    def _to_dict(t):
        usuario = getattr(t, 'usuario', None)
        usuario_id = getattr(t, 'usuario_id', None)
        return {
            'id': getattr(t, 'id', None),
            'ci': getattr(t, 'ci', None),
            'tipo_documento': getattr(t, 'tipo_documento', '') or '',
            'primer_apellido': getattr(t, 'primer_apellido', '') or '',
            'segundo_apellido': getattr(t, 'segundo_apellido', '') or '',
            'nombres': getattr(t, 'nombres', '') or '',
            'parentesco': getattr(t, 'parentesco', '') or '',
            'celular': getattr(t, 'celular', '') or '',
            'email': getattr(usuario, 'email', '') or '' if usuario else '',
            'idioma_frecuente': getattr(t, 'idioma_frecuente', '') or '',
            'fecha_nacimiento': str(t.fecha_nacimiento) if getattr(t, 'fecha_nacimiento', None) else None,
            'activo': bool(getattr(t, 'activo', True)),
            'usuario_id': usuario_id,
            'tiene_usuario': usuario_id is not None,
            'usuario_activo': bool(getattr(usuario, 'activo', False)) if usuario else False,
            'debe_cambiar_password': bool(getattr(usuario, 'debe_cambiar_password', False)) if usuario else False,
            'otp_habilitado': bool(getattr(usuario, 'otp_habilitado', False)) if usuario else False,
            'otp_metodo': getattr(usuario, 'otp_metodo', 'email') or 'email' if usuario else 'email',
        }

    def obtener(self, usuario, tutor_id):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        t = Tutores.objects.get(id=tutor_id)
        return self._to_dict(t)

    # ── Cuentas de acceso de tutores ─────────────────────────────────────────
    def _rol_tutor(self):
        rol, _ = Roles.objects.get_or_create(
            nombre='tutor',
            defaults={'descripcion': 'Tutor / padre o madre de familia'},
        )
        return rol

    def _puede_gestionar(self, usuario):
        return self.ac.puede_gestionar_inscripciones(usuario) or self.ac.es_director(usuario)

    def _crear_usuario_tutor(self, usuario, tutor, email):
        """Crea la cuenta del tutor con contrasena temporal y la envia por correo."""
        email = (email or '').strip().lower()
        if not email:
            raise ValueError('Debe registrar un correo electronico para crear la cuenta del tutor')

        if Usuarios.objects.filter(email__iexact=email).exists():
            raise ValueError('Ya existe un usuario registrado con ese correo electronico')

        if Usuarios.objects.filter(correo_personal__iexact=email).exists():
            raise ValueError('Ese correo ya esta registrado como correo personal de otro usuario')

        if tutor.usuario_id:
            raise ValueError('Este tutor ya tiene una cuenta de acceso')

        password_temporal = self.otp.generar_password_temporal()

        cuenta = Usuarios.objects.create(
            ci=tutor.ci,
            nombre=tutor.nombres,
            primer_apellido=tutor.primer_apellido,
            segundo_apellido=tutor.segundo_apellido,
            email=email,
            correo_personal=email,
            password_hash=make_password(password_temporal),
            rol=self._rol_tutor(),
            activo=True,
            password_temporal=True,
            debe_cambiar_password=True,
        )
        tutor.usuario = cuenta
        tutor.save(update_fields=['usuario'])

        # El segundo factor queda activo desde el primer ingreso (OTP_2FA_POR_DEFECTO)
        try:
            self.otp.habilitar_inicial(cuenta, actor=usuario)
        except Exception:  # noqa: BLE001 - la 2FA no debe impedir crear la cuenta
            pass
        otp_habilitado = bool(getattr(cuenta, 'otp_habilitado', False))
        otp_metodo = getattr(cuenta, 'otp_metodo', 'email') or 'email'

        enviado = False
        try:
            enviado = self.email.enviar_credenciales(cuenta, password_temporal, nombre=tutor.nombre_completo)
        except Exception:
            enviado = False

        self.audit.record(
            usuario, accion='CREATE', tabla='usuarios', registro_id=cuenta.id,
            datos_nuevo={
                'email': email, 'rol': 'tutor', 'tutor_id': tutor.id,
                'password_temporal': True, 'otp_habilitado': otp_habilitado,
            },
        )

        resultado = {
            'usuario_id': cuenta.id,
            'usuario': cuenta.usuario,
            'email': email,
            'correo_personal': cuenta.correo_personal,
            'rol': 'tutor',
            'correo_enviado': enviado,
            'debe_cambiar_password': True,
            'otp_habilitado': otp_habilitado,
            'otp_metodo': otp_metodo,
            'mensaje': 'Cuenta creada. Se envio la contrasena temporal al correo del tutor.'
            if enviado else 'Cuenta creada. No se pudo enviar el correo: comparte la contrasena temporal.',
        }
        if not enviado:
            resultado['password_temporal'] = password_temporal
        return resultado

    def generar_credenciales(self, usuario, tutor_id, email=None, regenerar=True):
        """Crea o restablece la cuenta del tutor con una nueva contrasena temporal."""
        if not self._puede_gestionar(usuario):
            raise PermissionError('Solo la secretaria o el director pueden gestionar cuentas de tutores')

        tutor = Tutores.objects.select_related('usuario').get(id=tutor_id)
        email = (email or (tutor.usuario.email if tutor.usuario_id else '') or '').strip().lower()

        if tutor.usuario_id and regenerar:
            cuenta = tutor.usuario
            password_temporal = self.otp.generar_password_temporal()
            cuenta.password_hash = make_password(password_temporal)
            cuenta.password_temporal = True
            cuenta.debe_cambiar_password = True
            cuenta.activo = True
            campos = ['password_hash', 'password_temporal', 'debe_cambiar_password', 'activo']
            if email:
                cuenta.email = email
                cuenta.correo_personal = email
                campos.extend(['email', 'correo_personal'])
            cuenta.save(update_fields=campos)

            enviado = False
            try:
                enviado = self.email.enviar_credenciales(cuenta, password_temporal, nombre=tutor.nombre_completo)
            except Exception:
                enviado = False

            self.audit.record(
                usuario, accion='UPDATE', tabla='usuarios', registro_id=cuenta.id,
                datos_nuevo={'email': cuenta.email, 'password_temporal': True, 'motivo': 'reenvio_credenciales'},
            )
            resultado = {
                'usuario_id': cuenta.id,
                'usuario': cuenta.usuario,
                'email': cuenta.email,
                'correo_personal': cuenta.correo_personal,
                'rol': 'tutor',
                'correo_enviado': enviado,
                'debe_cambiar_password': True,
                'otp_habilitado': bool(getattr(cuenta, 'otp_habilitado', False)),
                'otp_metodo': getattr(cuenta, 'otp_metodo', 'email') or 'email',
                'mensaje': 'Credenciales regeneradas y enviadas al correo del tutor.'
                if enviado else 'Credenciales regeneradas. No se pudo enviar el correo: comparte la contrasena temporal.',
            }
            if not enviado:
                resultado['password_temporal'] = password_temporal
            return resultado

        return self._crear_usuario_tutor(usuario, tutor, email)

    def desvincular_usuario(self, usuario, tutor_id, desactivar=True):
        """Quita la cuenta de acceso del tutor (opcionalmente la desactiva)."""
        if not self._puede_gestionar(usuario):
            raise PermissionError('Solo la secretaria o el director pueden gestionar cuentas de tutores')

        tutor = Tutores.objects.select_related('usuario').get(id=tutor_id)
        cuenta = tutor.usuario
        if not cuenta:
            raise ValueError('Este tutor no tiene una cuenta de acceso')

        tutor.usuario = None
        tutor.save(update_fields=['usuario'])
        if desactivar:
            cuenta.activo = False
            cuenta.save(update_fields=['activo'])

        self.audit.record(
            usuario, accion='DELETE', tabla='usuarios', registro_id=cuenta.id,
            datos_nuevo={'tutor_id': tutor.id, 'activo': False},
        )
        return {'mensaje': 'Cuenta del tutor desvinculada', 'usuario_id': cuenta.id}

    def crear(self, usuario, data, enviar_credenciales=True):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede gestionar tutores')

        validar_required(data, ['ci', 'nombres', 'primer_apellido'])
        validar_ci(data.get('ci'))
        validar_nombre(data.get('nombres'))
        validar_nombre(data.get('primer_apellido'))

        email = (data.get('email') or '').strip().lower() or None
        if email:
            validar_email(email)
        if data.get('celular'):
            validar_telefono(data.get('celular'))

        tutor = Tutores.objects.create(
            ci=data['ci'],
            tipo_documento=data.get('tipo_documento', 'CI'),
            primer_apellido=data['primer_apellido'],
            segundo_apellido=data.get('segundo_apellido', ''),
            nombres=data['nombres'],
            parentesco=data.get('parentesco', ''),
            celular=data.get('celular', ''),
            idioma_frecuente=data.get('idioma_frecuente', ''),
            fecha_nacimiento=data.get('fecha_nacimiento') or None,
        )
        self.audit.record(usuario, accion='CREATE', tabla='tutores', registro_id=tutor.id, datos_nuevo={'ci': data['ci'], 'nombres': data['nombres'], 'primer_apellido': data['primer_apellido']})

        resultado = {
            'id': tutor.id,
            'mensaje': 'Tutor creado exitosamente',
            'email': email or '',
            'cuenta': None,
        }

        # Crear la cuenta de acceso con contrasena temporal (si hay correo)
        crear_cuenta = bool(data.get('crear_usuario', True)) and enviar_credenciales
        if email and crear_cuenta:
            try:
                resultado['cuenta'] = self._crear_usuario_tutor(usuario, tutor, email)
            except ValueError as exc:
                resultado['cuenta'] = {'error': str(exc), 'correo_enviado': False}
            except Exception as exc:  # noqa: BLE001 - no romper la creacion del tutor
                resultado['cuenta'] = {'error': f'No se pudo crear la cuenta: {exc}', 'correo_enviado': False}

        return resultado

    def actualizar(self, usuario, tutor_id, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede modificar tutores')

        tutor = Tutores.objects.select_related('usuario').get(id=tutor_id)
        for campo in ('ci', 'tipo_documento', 'primer_apellido', 'segundo_apellido',
                       'nombres', 'parentesco', 'celular', 'idioma_frecuente', 'fecha_nacimiento'):
            if campo in data:
                setattr(tutor, campo, data[campo])
        if 'email' in data and tutor.usuario_id:
            email = (data.get('email') or '').strip().lower() or None
            if email:
                validar_email(email)
                tutor.usuario.email = email
                tutor.usuario.save(update_fields=['email'])
        tutor.save()
        self.audit.record(usuario, accion='UPDATE', tabla='tutores', registro_id=tutor.id, datos_nuevo={k: data[k] for k in data if k in data})
        return {'mensaje': 'Tutor actualizado', 'id': tutor.id, **self._to_dict(tutor)}

    def eliminar(self, usuario, tutor_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar tutores')

        tutor = Tutores.objects.get(id=tutor_id)
        tutor.activo = False
        tutor.save(update_fields=['activo'])
        self.audit.record(usuario, accion='DELETE', tabla='tutores', registro_id=tutor.id)
        return {'mensaje': 'Tutor eliminado'}
