from django.utils import timezone

from ..models import Periodos, Actividades, ActividadNotas, DocenteAsignacion, PeriodoCierreDocente
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService


@trace_service_class
class PeriodoService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar(self, usuario, gestion=None, page=None, page_size=None):
        qs = Periodos.objects.all().order_by('-gestion', 'fecha_inicio')
        if gestion:
            qs = qs.filter(gestion=gestion)
        if page is None or page_size is None:
            return [self._to_dict(p) for p in qs]

        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]
        return {
            'data': [self._to_dict(p) for p in items],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def crear(self, usuario, data):
        if not self.ac.puede_habilitar_periodo(usuario):
            raise PermissionError('Solo el director puede crear periodos')

        nombre = data.get('nombre')
        gestion = data.get('gestion')
        numero = data.get('numero')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        if not all([nombre, gestion, fecha_inicio, fecha_fin]):
            raise ValueError('Debe enviar nombre, gestion, fecha_inicio y fecha_fin')

        if not numero:
            ultimo = Periodos.objects.filter(gestion=gestion).order_by('-numero').first()
            numero = (ultimo.numero + 1) if ultimo else 1

        from datetime import date
        if isinstance(fecha_inicio, str):
            fecha_inicio = date.fromisoformat(fecha_inicio)
        if isinstance(fecha_fin, str):
            fecha_fin = date.fromisoformat(fecha_fin)

        if fecha_inicio > fecha_fin:
            raise ValueError('La fecha de inicio no puede ser posterior a la fecha de fin')

        # Validar que no se superponga con otros periodos de la misma gestion
        periodos_existentes = Periodos.objects.filter(gestion=gestion, activo=True)
        for p in periodos_existentes:
            if (fecha_inicio <= p.fecha_fin and fecha_fin >= p.fecha_inicio):
                raise ValueError(
                    f'El periodo se superpone con "{p.nombre}" ({p.fecha_inicio} a {p.fecha_fin})'
                )

        periodo = Periodos.objects.create(
            nombre=nombre,
            gestion=gestion,
            numero=numero,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado='pendiente',
        )
        self.audit.record(usuario, accion='CREATE', tabla='periodos', registro_id=periodo.id, datos_nuevo={'nombre': nombre, 'gestion': gestion, 'numero': numero})
        return self._to_dict(periodo)

    def obtener(self, usuario, periodo_id):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver periodos')

        periodo = Periodos.objects.get(id=periodo_id)
        return self._to_dict(periodo)

    def actualizar(self, usuario, periodo_id, data):
        if not self.ac.puede_habilitar_periodo(usuario):
            raise PermissionError('Solo el director puede modificar periodos')

        periodo = Periodos.objects.get(id=periodo_id)
        if 'nombre' in data:
            periodo.nombre = data['nombre']
        if 'gestion' in data:
            periodo.gestion = data['gestion']
        if 'fecha_inicio' in data:
            periodo.fecha_inicio = data['fecha_inicio']
        if 'fecha_fin' in data:
            periodo.fecha_fin = data['fecha_fin']
        periodo.save()
        self.audit.record(usuario, accion='UPDATE', tabla='periodos', registro_id=periodo.id, datos_nuevo={k: data[k] for k in data if k in data})
        return self._to_dict(periodo)

    def eliminar(self, usuario, periodo_id):
        if not self.ac.puede_habilitar_periodo(usuario):
            raise PermissionError('Solo el director puede eliminar periodos')

        from django.db.models import Q
        Periodos.objects.filter(id=periodo_id).update(activo=False)
        self.audit.record(usuario, accion='DELETE', tabla='periodos', registro_id=periodo_id, datos_nuevo={'activo': False})
        return {'mensaje': 'Periodo eliminado'}

    def habilitar(self, usuario, periodo_id):
        if not self.ac.puede_habilitar_periodo(usuario):
            raise PermissionError('Solo el director puede habilitar periodos')

        periodo = Periodos.objects.get(id=periodo_id, activo=True)
        if periodo.estado != 'pendiente':
            raise ValueError(f'El periodo esta en estado "{periodo.estado}", no se puede habilitar')

        # Cerrar el periodo anterior de la misma gestion (nota definitiva)
        periodo_anterior = Periodos.objects.filter(
            gestion=periodo.gestion, estado='activo'
        ).exclude(id=periodo.id).first()
        if periodo_anterior:
            periodo_anterior.estado = 'cerrado'
            periodo_anterior.cerrado_por = usuario
            periodo_anterior.cerrado_en = timezone.now()
            periodo_anterior.save(update_fields=['estado', 'cerrado_por', 'cerrado_en'])

        periodo.estado = 'activo'
        periodo.habilitado_por = usuario
        periodo.habilitado_en = timezone.now()
        periodo.save(update_fields=['estado', 'habilitado_por', 'habilitado_en'])
        self.audit.record(usuario, accion='ENABLE', tabla='periodos', registro_id=periodo.id, datos_nuevo={'estado': 'activo'})
        return self._to_dict(periodo)

    def cerrar(self, usuario, periodo_id):
        if not self.ac.puede_cerrar_periodo(usuario):
            raise PermissionError('Solo el director o secretaria pueden cerrar periodos')

        periodo = Periodos.objects.get(id=periodo_id)
        if periodo.estado != 'activo':
            raise ValueError('Solo se puede cerrar un periodo activo')

        # Validar que todas las actividades del periodo tengan notas
        actividades_sin_notas = []
        for act in Actividades.objects.filter(periodo_id=periodo_id, activo=True).only('id', 'nombre', 'docente_asignacion_id'):
            tiene_notas = ActividadNotas.objects.filter(actividad_id=act.id).exists()
            if not tiene_notas:
                da = DocenteAsignacion.objects.filter(id=act.docente_asignacion_id).select_related('curso', 'area').first()
                curso = str(da.curso) if da else '?'
                area = da.area.nombre if da and da.area else '?'
                actividades_sin_notas.append(f'{act.nombre} ({curso} - {area})')

        if actividades_sin_notas:
            raise ValueError(
                'No se puede cerrar el periodo: las siguientes actividades no tienen notas registradas:\n'
                + '\n'.join(f'- {a}' for a in actividades_sin_notas[:20])
                + (f'\n... y {len(actividades_sin_notas) - 20} mas' if len(actividades_sin_notas) > 20 else '')
            )

        # Validar que todos los docentes hayan cerrado sus asignaciones
        docentes_sin_cierre = DocenteAsignacion.objects.filter(
            activo=True, gestion=periodo.gestion
        ).exclude(
            id__in=PeriodoCierreDocente.objects.filter(
                periodo=periodo
            ).values('docente_asignacion_id')
        ).select_related('docente__usuario', 'area')

        if docentes_sin_cierre.exists():
            pendientes = [
                f'{da.usuario.nombre_completo} ({da.area.nombre})'
                for da in docentes_sin_cierre[:20]
            ]
            raise ValueError(
                'No se puede cerrar el periodo: los siguientes docentes no han cerrado sus asignaciones:\n'
                + '\n'.join(f'- {p}' for p in pendientes)
                + (f'\n... y {docentes_sin_cierre.count() - 20} mas' if docentes_sin_cierre.count() > 20 else '')
            )

        periodo.estado = 'cerrado'
        periodo.cerrado_por = usuario
        periodo.cerrado_en = timezone.now()
        periodo.save(update_fields=['estado', 'cerrado_por', 'cerrado_en'])
        self.audit.record(usuario, accion='CLOSE', tabla='periodos', registro_id=periodo.id, datos_nuevo={'estado': 'cerrado'})
        return self._to_dict(periodo)

    def _to_dict(self, periodo):
        return {
            'id': periodo.id,
            'nombre': periodo.nombre,
            'numero': periodo.numero,
            'gestion': periodo.gestion,
            'estado': periodo.estado,
            'fecha_inicio': str(periodo.fecha_inicio),
            'fecha_fin': str(periodo.fecha_fin),
            'marcado_como_enviado': periodo.marcado_como_enviado,
            'enviado_por': periodo.enviado_por.nombre_completo if periodo.enviado_por else None,
            'enviado_en': periodo.enviado_en.isoformat() if periodo.enviado_en else None,
        }

    def get_periodo_activo(self, gestion=None):
        qs = Periodos.objects.filter(estado='activo')
        if gestion:
            qs = qs.filter(gestion=gestion)
        return qs.first()

    def get_periodos_gestion(self, gestion):
        return Periodos.objects.filter(gestion=gestion).order_by('numero')
