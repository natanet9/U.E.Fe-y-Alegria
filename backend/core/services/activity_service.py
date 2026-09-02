from django.db import transaction
from django.utils import timezone

from ..models import AuditLog, Actividades, ActividadNotas, DimensionesEvaluacion, DocenteAsignacion, Periodos
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_fecha, validar_puntaje_maximo, validar_nota, ValidationError


@trace_service_class
class ActivityService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def crear_actividad(self, usuario, data):
        da_id = data.get('docente_asignacion_id')
        if not self.ac.puede_editar_notas_libremente(usuario, da_id):
            raise PermissionError('No tienes permisos para crear actividades')

        validar_required(data, ['nombre', 'dimension_id', 'fecha_actividad', 'docente_asignacion_id'])
        validar_fecha(data.get('fecha_actividad'), 'fecha_actividad', permitir_pasado=False)
        validar_puntaje_maximo(data.get('puntaje_maximo'))

        nombre = data.get('nombre')
        dimension_id = data.get('dimension_id')
        fecha = data.get('fecha_actividad')

        # Auto-detect active period if not provided
        periodo_id = data.get('periodo_id')
        if not periodo_id:
            da = DocenteAsignacion.objects.get(id=da_id)
            periodo = Periodos.objects.filter(gestion=da.gestion, estado='activo').order_by('fecha_inicio').first()
            if not periodo:
                raise ValueError('No hay un periodo activo para la gestion actual. El director debe habilitar un periodo.')
            periodo_id = periodo.id

        dimension = DimensionesEvaluacion.objects.get(id=dimension_id)
        if dimension.nombre == 'AUTOEVALUACION':
            raise ValueError('La autoevaluacion se registra como nota fija del periodo')

        actividad = Actividades.objects.create(
            docente_asignacion_id=da_id,
            periodo_id=periodo_id,
            dimension_id=dimension_id,
            nombre=nombre,
            descripcion=data.get('descripcion', ''),
            puntaje_maximo=data.get('puntaje_maximo', 100),
            fecha_actividad=fecha,
        )
        self.audit.record_actividad_change(usuario, 'CREATE', actividad.id, {'nombre': nombre, 'dimension_id': dimension_id})
        return {
            'id': actividad.id,
            'nombre': actividad.nombre,
            'puntaje_maximo': float(actividad.puntaje_maximo),
            'dimension_id': actividad.dimension_id,
            'dimension_nombre': actividad.dimension.nombre,
            'periodo_id': actividad.periodo_id,
            'fecha_actividad': str(actividad.fecha_actividad),
        }

    def eliminar_actividad(self, usuario, actividad_id):
        actividad = Actividades.objects.select_related('docente_asignacion').get(id=actividad_id)
        da_id = actividad.docente_asignacion_id
        if not self.ac.puede_editar_notas_libremente(usuario, da_id):
            raise PermissionError('No tienes permisos para eliminar esta actividad')
        actividad.activo = False
        actividad.save(update_fields=['activo'])
        self.audit.record_actividad_change(usuario, 'DELETE', actividad_id, {'activo': False})

    def obtener_actividad(self, usuario, actividad_id):
        # check permission early (tests patch puede_editar_notas)
        if not self.ac.puede_editar_notas(usuario, actividad_id):
            raise PermissionError('No tienes permisos para ver esta actividad')
        actividad = Actividades.objects.select_related('docente_asignacion', 'dimension', 'periodo').get(id=actividad_id)
        return {
            'id': actividad.id,
            'docente_asignacion_id': actividad.docente_asignacion_id,
            'periodo_id': actividad.periodo_id,
            'dimension_id': actividad.dimension_id,
            'nombre': actividad.nombre,
            'descripcion': actividad.descripcion or '',
            'puntaje_maximo': float(actividad.puntaje_maximo),
            'fecha_actividad': str(actividad.fecha_actividad),
            'activo': actividad.activo,
        }

    def actualizar_actividad(self, usuario, actividad_id, data):
        # check permission early so tests can patch without DB access
        if not self.ac.puede_editar_notas_libremente(usuario, actividad_id):
            raise PermissionError('No tienes permisos para modificar esta actividad')
        actividad = Actividades.objects.select_related('docente_asignacion').get(id=actividad_id)

        if 'nombre' in data:
            actividad.nombre = data['nombre']
        if 'descripcion' in data:
            actividad.descripcion = data['descripcion']
        if 'fecha_actividad' in data:
            validar_fecha(data.get('fecha_actividad'), 'fecha_actividad', permitir_pasado=False)
            actividad.fecha_actividad = data['fecha_actividad']
        if 'puntaje_maximo' in data:
            validar_puntaje_maximo(data['puntaje_maximo'])
            actividad.puntaje_maximo = data['puntaje_maximo']
        actividad.save()
        self.audit.record_actividad_change(usuario, 'UPDATE', actividad_id, {k: data[k] for k in data if k in data})
        return {
            'id': actividad.id,
            'nombre': actividad.nombre,
            'descripcion': actividad.descripcion or '',
            'puntaje_maximo': float(actividad.puntaje_maximo),
            'fecha_actividad': str(actividad.fecha_actividad),
        }

    def restaurar_actividad(self, usuario, actividad_id):
        actividad = Actividades.objects.get(id=actividad_id)
        da_id = actividad.docente_asignacion_id
        if not self.ac.puede_editar_notas_libremente(usuario, da_id):
            raise PermissionError('No tienes permisos para restaurar esta actividad')
        actividad.activo = True
        actividad.save(update_fields=['activo'])
        self.audit.record_actividad_change(usuario, 'RESTORE', actividad_id, {'activo': True})
        return {'mensaje': 'Actividad restaurada exitosamente'}

    def guardar_notas_actividad(self, usuario, actividad_id, notas_dict, motivo=None):
        actividad = Actividades.objects.get(id=actividad_id)
        da_id = actividad.docente_asignacion_id

        if self.ac.puede_editar_notas_libremente(usuario, da_id):
            pass
        elif self.ac.puede_modificar_notas_con_motivo(usuario) and motivo:
            pass
        else:
            raise PermissionError('No tienes permisos para modificar notas')

        existing = {
            str(an.estudiante_id): an
            for an in ActividadNotas.objects.filter(actividad_id=actividad_id)
        }

        for v in (notas_dict or {}).values():
            validar_nota(v)

        for estudiante_id, valor in (notas_dict or {}).items():
            an, created = ActividadNotas.objects.update_or_create(
                actividad_id=actividad_id,
                estudiante_id=estudiante_id,
                defaults={'valor': valor if valor is not None else None},
            )
            old_valor = existing.get(str(estudiante_id))
            if not created and old_valor and old_valor.valor != valor:
                self.audit.record_nota_change(
                    usuario, an.id, old_valor.valor, valor, int(estudiante_id),
                )
            elif created:
                self.audit.record_nota_change(
                    usuario, an.id, None, valor, int(estudiante_id),
                )

        return list(notas_dict.keys()) if notas_dict else []

    def guardar_notas_batch(self, usuario, actividades, motivo=None):
        if not actividades:
            return []

        actividad_ids = [a['actividad_id'] for a in actividades if a.get('actividad_id')]
        if not actividad_ids:
            return []

        actividades_qs = list(Actividades.objects.filter(id__in=actividad_ids).select_related('docente_asignacion'))
        if not actividades_qs:
            return []

        da_ids = {a.docente_asignacion_id for a in actividades_qs}
        if len(da_ids) != 1:
            raise ValueError('Todas las actividades deben pertenecer a la misma asignación')
        da_id = da_ids.pop()
        actividad_map = {a.id: a for a in actividades_qs}

        if not (self.ac.puede_editar_notas_libremente(usuario, da_id) or
                (self.ac.puede_modificar_notas_con_motivo(usuario) and motivo)):
            raise PermissionError('No tienes permisos para modificar notas')

        notas_por_actividad = {}
        all_estudiante_ids = set()
        for item in actividades:
            aid = item.get('actividad_id')
            notas = item.get('notas', {})
            if not aid or aid not in actividad_map:
                continue
            for v in notas.values():
                validar_nota(v)
            items_list = [(int(eid), valor) for eid, valor in notas.items()]
            notas_por_actividad[aid] = items_list
            all_estudiante_ids.update(eid for eid, _ in items_list)

        existing = {}
        if all_estudiante_ids:
            existing = {
                (an.actividad_id, an.estudiante_id): an
                for an in ActividadNotas.objects.filter(
                    actividad_id__in=actividad_ids,
                    estudiante_id__in=list(all_estudiante_ids),
                )
            }

        now = timezone.now()
        to_create = []
        to_update = []
        audit_entries = []

        for actividad_id, notas_items in notas_por_actividad.items():
            for estudiante_id, valor in notas_items:
                valor_normalizado = valor if valor is not None else None
                current = existing.get((actividad_id, estudiante_id))
                if current:
                    if current.valor != valor_normalizado:
                        old_valor = current.valor
                        current.valor = valor_normalizado
                        current.activo = True
                        current.modificado_en = now
                        to_update.append(current)
                        audit_entries.append((current.id, old_valor, valor_normalizado, estudiante_id))
                else:
                    to_create.append(ActividadNotas(
                        actividad_id=actividad_id,
                        estudiante_id=estudiante_id,
                        valor=valor_normalizado,
                        activo=True,
                    ))

        with transaction.atomic():
            created = ActividadNotas.objects.bulk_create(to_create) if to_create else []
            if to_update:
                ActividadNotas.objects.bulk_update(to_update, ['valor', 'activo', 'modificado_en'])

            audit_logs = [
                AuditLog(
                    tabla='actividad_notas',
                    registro_id=nota.id,
                    accion='CREATE',
                    datos_anterior=None,
                    datos_nuevo={'valor': float(nota.valor) if nota.valor is not None else None, 'estudiante_id': nota.estudiante_id},
                    usuario=usuario,
                    fecha_cambio=now,
                )
                for nota in created
            ]
            audit_logs.extend(
                AuditLog(
                    tabla='actividad_notas',
                    registro_id=nota_id,
                    accion='UPDATE',
                    datos_anterior={'valor': float(valor_anterior) if valor_anterior is not None else None},
                    datos_nuevo={'valor': float(valor_nuevo) if valor_nuevo is not None else None, 'estudiante_id': estudiante_id},
                    usuario=usuario,
                    fecha_cambio=now,
                )
                for nota_id, valor_anterior, valor_nuevo, estudiante_id in audit_entries
            )
            if audit_logs:
                AuditLog.objects.bulk_create(audit_logs)

        if motivo:
            self.audit.record(usuario, accion='GRADE_BATCH', tabla='actividad_notas',
                              datos_nuevo={'motivo': motivo, 'actividades': actividad_ids})

        return [{'actividad_id': aid, 'updated_count': len(notas)} for aid, notas in notas_por_actividad.items()]

    def get_notas_estudiante(self, usuario, docente_asignacion_id, estudiante_id):
        if not self.ac.puede_editar_notas(usuario, docente_asignacion_id):
            raise PermissionError('No tienes permisos')
        qs = ActividadNotas.objects.filter(
            actividad__docente_asignacion_id=docente_asignacion_id,
            estudiante_id=estudiante_id,
        ).select_related('actividad')
        return {
            str(an.actividad_id): float(an.valor) if an.valor is not None else None
            for an in qs
        }

    def obtener_nota(self, usuario, nota_id):
        # check permission early (tests patch puede_editar_notas)
        if not self.ac.puede_editar_notas(usuario, nota_id):
            raise PermissionError('No tienes permisos')
        an = ActividadNotas.objects.select_related('actividad', 'estudiante').get(id=nota_id)
        return {
            'id': an.id,
            'actividad_id': an.actividad_id,
            'actividad_nombre': an.actividad.nombre,
            'estudiante_id': an.estudiante_id,
            'estudiante_nombre': str(an.estudiante),
            'valor': float(an.valor) if an.valor is not None else None,
            'registrado_en': an.registrado_en.isoformat(),
        }

    def eliminar_nota(self, usuario, nota_id):
        # check permission early so tests can patch puede_editar_notas without DB access
        if not self.ac.puede_editar_notas(usuario, nota_id):
            raise PermissionError('No tienes permisos')

        an = ActividadNotas.objects.select_related('actividad').get(id=nota_id)
        if not self.ac.puede_editar_notas_libremente(usuario, an.actividad.docente_asignacion_id):
            raise PermissionError('No tienes permisos')
        an.activo = False
        an.save(update_fields=['activo'])
        self.audit.record(usuario, accion='DELETE', tabla='actividad_notas',
                          registro_id=nota_id, datos_anterior={'valor': float(an.valor) if an.valor else None})
        return {'mensaje': 'Nota eliminada'}

    def update_notas_directo(self, usuario, data):
        da_id = data.get('docente_asignacion_id')
        if self.ac.puede_editar_notas_libremente(usuario, da_id):
            motivo = None
        elif self.ac.puede_modificar_notas_con_motivo(usuario):
            motivo = data.get('motivo', '').strip()
            if not motivo:
                raise PermissionError('El director debe indicar un motivo para modificar notas')
        else:
            raise PermissionError('No tienes permisos para modificar notas')

        periodo_id = data.get('periodo_id')
        notas = data.get('notas', {})
        if not da_id or not periodo_id or not notas:
            raise ValueError('Debe enviar docente_asignacion_id, periodo_id y notas')

        if isinstance(notas, list):
            notas = {
                str(item.get('estudiante_id')): item.get('valor')
                for item in notas
                if item.get('estudiante_id') is not None
            }
        elif not hasattr(notas, 'items'):
            raise ValueError('El campo notas debe ser un diccionario o una lista de registros')

        for v in notas.values():
            validar_nota(v)

        actividades = list(Actividades.objects.filter(
            docente_asignacion_id=da_id, periodo_id=periodo_id
        ).values_list('id', flat=True))

        if not actividades:
            raise ValueError('No hay actividades en este periodo para la asignacion')

        estudiante_ids = []
        for estudiante_id in notas.keys():
            try:
                estudiante_ids.append(int(estudiante_id))
            except (TypeError, ValueError):
                raise ValidationError('Los identificadores de estudiante deben ser numericos')

        existing = {
            (an.actividad_id, an.estudiante_id): an
            for an in ActividadNotas.objects.filter(
                actividad_id__in=actividades,
                estudiante_id__in=estudiante_ids,
            )
        }

        now = timezone.now()
        to_create = []
        to_update = []
        audit_entries = []

        for actividad_id in actividades:
            for estudiante_id_text, valor in notas.items():
                estudiante_id = int(estudiante_id_text)
                valor_normalizado = valor if valor is not None else None
                current = existing.get((actividad_id, estudiante_id))
                if current:
                    if current.valor != valor_normalizado:
                        old_valor = current.valor
                        current.valor = valor_normalizado
                        current.activo = True
                        current.modificado_en = now
                        to_update.append(current)
                        audit_entries.append((current.id, old_valor, valor_normalizado, estudiante_id))
                else:
                    to_create.append(ActividadNotas(
                        actividad_id=actividad_id,
                        estudiante_id=estudiante_id,
                        valor=valor_normalizado,
                        activo=True,
                    ))

        with transaction.atomic():
            created = ActividadNotas.objects.bulk_create(to_create) if to_create else []
            if to_update:
                ActividadNotas.objects.bulk_update(to_update, ['valor', 'activo', 'modificado_en'])

            audit_logs = [
                AuditLog(
                    tabla='actividad_notas',
                    registro_id=nota.id,
                    accion='UPDATE',
                    datos_anterior={'valor': None},
                    datos_nuevo={'valor': float(nota.valor) if nota.valor is not None else None, 'estudiante_id': nota.estudiante_id},
                    usuario=usuario,
                    fecha_cambio=now,
                )
                for nota in created
            ]
            audit_logs.extend(
                AuditLog(
                    tabla='actividad_notas',
                    registro_id=nota_id,
                    accion='UPDATE',
                    datos_anterior={'valor': float(valor_anterior) if valor_anterior is not None else None},
                    datos_nuevo={'valor': float(valor_nuevo) if valor_nuevo is not None else None, 'estudiante_id': estudiante_id},
                    usuario=usuario,
                    fecha_cambio=now,
                )
                for nota_id, valor_anterior, valor_nuevo, estudiante_id in audit_entries
            )
            if audit_logs:
                AuditLog.objects.bulk_create(audit_logs)

        return {'mensaje': f'Notas actualizadas para {len(notas)} estudiantes'}

    def _list_actividades(self, docente_asignacion_id, page=None, page_size=None):
        qs = Actividades.objects.filter(docente_asignacion_id=docente_asignacion_id, activo=True).order_by('fecha_actividad')
        # if no pagination requested, return plain list
        if page is None:
            items = list(qs)
            return [
                {
                    'id': a.id,
                    'nombre': a.nombre,
                    'descripcion': a.descripcion or '',
                    'puntaje_maximo': float(a.puntaje_maximo),
                    'dimension_id': a.dimension_id,
                    'dimension_nombre': a.dimension.nombre,
                    'periodo_id': a.periodo_id,
                    'fecha_actividad': str(a.fecha_actividad),
                }
                for a in items
            ]

        # pagination requested; apply defaults
        page_size = page_size if page_size is not None else 20
        total = qs.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages) if total > 0 else 1
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]
        return {
            'data': [
                {
                    'id': a.id,
                    'nombre': a.nombre,
                    'descripcion': a.descripcion or '',
                    'puntaje_maximo': float(a.puntaje_maximo),
                    'dimension_id': a.dimension_id,
                    'dimension_nombre': a.dimension.nombre,
                    'periodo_id': a.periodo_id,
                    'fecha_actividad': str(a.fecha_actividad),
                }
                for a in items
            ],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }
