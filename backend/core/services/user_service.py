from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from ..models import Docentes, Roles, Usuarios
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_email, validar_ci, ValidationError


@trace_service_class
class UserService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar(self, usuario, query=None, rol=None, page=1, page_size=8, incluir_inactivos=False):
        if not self.ac.puede_gestionar_usuarios(usuario):
            return {'usuarios': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

        qs = Usuarios.objects.select_related('rol', 'docente').all().order_by('nombre', 'primer_apellido', 'segundo_apellido')

        if not incluir_inactivos:
            qs = qs.filter(activo=True)

        if query:
            qs = qs.filter(
                Q(nombre__icontains=query)
                | Q(primer_apellido__icontains=query)
                | Q(segundo_apellido__icontains=query)
                | Q(email__icontains=query)
            )

        if rol:
            qs = qs.filter(rol__nombre=rol)

        # If page is None, return full list
        if page is None:
            usuarios = qs
            return [self._to_dict(u) for u in usuarios]

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        usuarios = qs[offset:offset + page_size]

        return {
            'usuarios': [self._to_dict(u) for u in usuarios],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    _ROLE_HIERARCHY = ['tutor', 'estudiante', 'docente', 'regente', 'secretaria', 'director']

    @classmethod
    def _role_rank(cls, rol_nombre):
        try:
            return cls._ROLE_HIERARCHY.index(rol_nombre)
        except ValueError:
            return -1

    def crear(self, usuario, data):
        if not self.ac.puede_gestionar_usuarios(usuario):
            raise PermissionError('No tienes permisos para crear usuarios')

        email = data.get('email')
        nombre = data.get('nombre') or ''
        apellido = data.get('apellido') or ''
        nombre_completo = data.get('nombre_completo', '').strip()
        ci = data.get('ci')
        rol_nombre = data.get('rol')
        password = data.get('password', '123456')

        validar_required(data, ['email', 'rol'])
        validar_email(data.get('email'))

        if not nombre and not apellido and nombre_completo:
            parts = nombre_completo.split(maxsplit=1)
            nombre = parts[0]
            apellido = parts[1] if len(parts) > 1 else ''

        if ci:
            validar_ci(ci)

        rol = Roles.objects.get(nombre=rol_nombre)

        if self._role_rank(rol_nombre) > self._role_rank(usuario.rol.nombre if usuario.rol else ''):
            raise PermissionError(f'No puedes crear un usuario con rol superior al tuyo')

        usuario_obj = Usuarios.objects.create(
            ci=ci or None,
            nombre=nombre or None,
            primer_apellido=apellido or None,
            email=email,
            password_hash=make_password(password),
            rol=rol,
            activo=True,
        )
        if rol_nombre == 'docente':
            docente_kwargs = {'usuario': usuario_obj}
            for f in ('titulo_academico', 'especialidad'):
                if f in data:
                    docente_kwargs[f] = data[f]
            if 'fecha_ingreso_institucion' in data:
                docente_kwargs['fecha_ingreso_institucion'] = data['fecha_ingreso_institucion']
            if 'anos_experiencia' in data:
                docente_kwargs['anos_experiencia'] = data['anos_experiencia']
            Docentes.objects.create(**docente_kwargs)
        self.audit.record_usuario_change(usuario, 'CREATE', usuario_obj.id, {'email': data.get('email')})
        return self._to_dict(usuario_obj)

    def actualizar(self, usuario, usuario_id, data):
        if not self.ac.puede_gestionar_usuarios(usuario):
            raise PermissionError('No tienes permisos para modificar usuarios')

        if usuario.id == usuario_id and 'activo' in data and data['activo'] is False:
            raise PermissionError('No puedes desactivarte a ti mismo')

        u = Usuarios.objects.select_related('docente').get(id=usuario_id)
        if 'nombre' in data:
            u.nombre = data['nombre']
        if 'primer_apellido' in data:
            u.primer_apellido = data['primer_apellido']
        if 'segundo_apellido' in data:
            u.segundo_apellido = data['segundo_apellido']
        if 'ci' in data:
            validar_ci(data['ci'])
            u.ci = data['ci']
        if 'email' in data:
            u.email = data['email']
        if 'activo' in data:
            u.activo = data['activo']
        if 'rol' in data:
            u.rol = Roles.objects.get(nombre=data['rol'])
        if 'password' in data:
            u.password_hash = make_password(data['password'])
        u.save()

        docente_fields = ['titulo_academico', 'especialidad', 'fecha_ingreso_institucion', 'anos_experiencia']
        if any(f in data for f in docente_fields):
            try:
                doc = u.docente
            except ObjectDoesNotExist:
                doc = Docentes.objects.create(usuario=u)
            if 'titulo_academico' in data:
                doc.titulo_academico = data['titulo_academico']
            if 'especialidad' in data:
                doc.especialidad = data['especialidad']
            if 'fecha_ingreso_institucion' in data:
                doc.fecha_ingreso_institucion = data['fecha_ingreso_institucion']
            if 'anos_experiencia' in data:
                doc.anos_experiencia = data['anos_experiencia']
            doc.save()

        self.audit.record_usuario_change(usuario, 'UPDATE', usuario_id, {k: data[k] for k in data if k in data})
        return self._to_dict(u)

    def eliminar(self, usuario, usuario_id):
        if not self.ac.puede_gestionar_usuarios(usuario):
            raise PermissionError('No tienes permisos para eliminar usuarios')

        if usuario.id == usuario_id:
            raise PermissionError('No puedes desactivarte a ti mismo')

        u = Usuarios.objects.get(id=usuario_id)
        if u.rol and u.rol.nombre == 'director':
            raise PermissionError('No puedes desactivar a un director')
        u.activo = False
        u.save(update_fields=['activo'])
        self.audit.record_usuario_change(usuario, 'DELETE', usuario_id, {'activo': False})

    def restaurar(self, usuario, usuario_id):
        if not self.ac.puede_gestionar_usuarios(usuario):
            raise PermissionError('No tienes permisos para restaurar usuarios')

        u = Usuarios.objects.get(id=usuario_id)
        u.activo = True
        u.save(update_fields=['activo'])
        self.audit.record_usuario_change(usuario, 'RESTORE', usuario_id, {'activo': True})
        return self._to_dict(u)

    def obtener(self, usuario, usuario_id):
        if not self.ac.puede_gestionar_usuarios(usuario):
            raise PermissionError('No tienes permisos')
        u = Usuarios.objects.select_related('rol', 'docente').get(id=usuario_id)
        return self._to_dict(u)

    @staticmethod
    def _docente_to_dict(docente):
        if docente is None:
            return None
        return {
            'titulo_academico': docente.titulo_academico,
            'especialidad': docente.especialidad,
            'fecha_ingreso_institucion': str(docente.fecha_ingreso_institucion) if docente.fecha_ingreso_institucion else None,
            'anos_experiencia': docente.anos_experiencia,
        }

    def _to_dict(self, u):
        d = {
            'id': u.id,
            'ci': u.ci,
            'nombre': u.nombre,
            'primer_apellido': u.primer_apellido,
            'segundo_apellido': u.segundo_apellido,
            'nombre_completo': u.nombre_completo,
            'email': u.email,
            'rol': u.rol.nombre if u.rol else None,
            'activo': u.activo,
        }
        try:
            d['docente'] = self._docente_to_dict(u.docente)
        except ObjectDoesNotExist:
            d['docente'] = None
        return d
