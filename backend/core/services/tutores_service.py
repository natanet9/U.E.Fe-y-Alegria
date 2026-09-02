from ..models import Tutores, EstudianteTutor
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_ci, validar_nombre, validar_telefono, ValidationError
from django.db.models.query import QuerySet


@trace_service_class
class TutoresService:
    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

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
                    'data': [
                        {
                            'id': t.id,
                            'ci': t.ci,
                            'tipo_documento': t.tipo_documento,
                            'primer_apellido': t.primer_apellido,
                            'segundo_apellido': t.segundo_apellido or '',
                            'nombres': t.nombres,
                            'parentesco': t.parentesco or '',
                            'celular': t.celular or '',
                            'idioma_frecuente': t.idioma_frecuente or '',
                            'fecha_nacimiento': str(t.fecha_nacimiento) if t.fecha_nacimiento else None,
                            'activo': t.activo,
                        }
                        for t in items
                    ],
                    'total': total,
                    'page': 1,
                    'page_size': total,
                    'total_pages': 1,
                }
            return [
                {
                    'id': t.id,
                    'ci': t.ci,
                    'tipo_documento': t.tipo_documento,
                    'primer_apellido': t.primer_apellido,
                    'segundo_apellido': t.segundo_apellido or '',
                    'nombres': t.nombres,
                    'parentesco': t.parentesco or '',
                    'celular': t.celular or '',
                    'idioma_frecuente': t.idioma_frecuente or '',
                    'fecha_nacimiento': str(t.fecha_nacimiento) if t.fecha_nacimiento else None,
                    'activo': t.activo,
                }
                for t in qs
            ]

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]
        return {
            'data': [
                {
                    'id': t.id,
                    'ci': t.ci,
                    'tipo_documento': t.tipo_documento,
                    'primer_apellido': t.primer_apellido,
                    'segundo_apellido': t.segundo_apellido or '',
                    'nombres': t.nombres,
                    'parentesco': t.parentesco or '',
                    'celular': t.celular or '',
                    'idioma_frecuente': t.idioma_frecuente or '',
                    'fecha_nacimiento': str(t.fecha_nacimiento) if t.fecha_nacimiento else None,
                    'activo': t.activo,
                }
                for t in items
            ],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def obtener(self, usuario, tutor_id):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        t = Tutores.objects.get(id=tutor_id)
        return {
            'id': t.id,
            'ci': t.ci,
            'tipo_documento': t.tipo_documento,
            'primer_apellido': t.primer_apellido,
            'segundo_apellido': t.segundo_apellido or '',
            'nombres': t.nombres,
            'parentesco': t.parentesco or '',
            'celular': t.celular or '',
            'idioma_frecuente': t.idioma_frecuente or '',
            'fecha_nacimiento': str(t.fecha_nacimiento) if t.fecha_nacimiento else None,
            'activo': t.activo,
        }

    def crear(self, usuario, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede gestionar tutores')

        validar_required(data, ['ci', 'nombres', 'primer_apellido'])
        validar_ci(data.get('ci'))
        validar_nombre(data.get('nombres'))
        validar_nombre(data.get('primer_apellido'))

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
        return {'id': tutor.id, 'mensaje': 'Tutor creado exitosamente'}

    def actualizar(self, usuario, tutor_id, data):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede modificar tutores')

        tutor = Tutores.objects.get(id=tutor_id)
        for campo in ('ci', 'tipo_documento', 'primer_apellido', 'segundo_apellido',
                       'nombres', 'parentesco', 'celular', 'idioma_frecuente', 'fecha_nacimiento'):
            if campo in data:
                setattr(tutor, campo, data[campo])
        tutor.save()
        self.audit.record(usuario, accion='UPDATE', tabla='tutores', registro_id=tutor.id, datos_nuevo={k: data[k] for k in data if k in data})
        return {'mensaje': 'Tutor actualizado', 'id': tutor.id}

    def eliminar(self, usuario, tutor_id):
        if not self.ac.puede_gestionar_inscripciones(usuario):
            raise PermissionError('Solo la secretaria puede eliminar tutores')

        tutor = Tutores.objects.get(id=tutor_id)
        tutor.activo = False
        tutor.save(update_fields=['activo'])
        self.audit.record(usuario, accion='DELETE', tabla='tutores', registro_id=tutor.id)
        return {'mensaje': 'Tutor eliminado'}
