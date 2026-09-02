from ..models import Cursos, DocenteAsignacion, Grados, Horarios
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService
from .validation import validar_required, validar_dia_semana, validar_hora, ValidationError


@trace_service_class
class ScheduleService:

    DIAS = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes'}

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def listar_horarios(self, usuario, grado_id=None, curso_id=None, page=None, page_size=None):
        if self.ac.puede_ver_todo(usuario):
            if curso_id:
                qs = DocenteAsignacion.objects.filter(curso_id=curso_id, activo=True)
            elif grado_id:
                cursos = Cursos.objects.filter(grado_id=grado_id)
                qs = DocenteAsignacion.objects.filter(curso__in=cursos, activo=True)
            else:
                qs = DocenteAsignacion.objects.filter(activo=True)
        elif self.ac.es_docente(usuario):
            qs = DocenteAsignacion.objects.filter(docente__usuario=usuario, activo=True)
        else:
            raise PermissionError('No tienes permisos para ver horarios')

        qs = qs.select_related('curso__grado__nivel', 'curso__paralelo', 'area', 'docente__usuario')

        horarios = Horarios.objects.select_related(
            'docente_asignacion__curso__grado',
            'docente_asignacion__area',
            'docente_asignacion__docente__usuario',
        ).filter(docente_asignacion__in=qs).order_by('dia_semana', 'hora_inicio')

        if page is None or page_size is None:
            horarios_paginated = horarios
        else:
            total = horarios.count()
            total_pages = max(1, (total + page_size - 1) // page_size)
            page = min(page, total_pages) if total > 0 else 1
            offset = (page - 1) * page_size
            horarios_paginated = horarios[offset:offset + page_size]

        result = {}
        for h in horarios_paginated:
            da = h.docente_asignacion
            key = f'{da.curso.grado.nombre} {da.curso.paralelo.nombre}'
            result.setdefault(key, {
                'curso': key,
                'grado': da.curso.grado.nombre,
                'paralelo': da.curso.paralelo.nombre,
                'horarios': [],
            })
            result[key]['horarios'].append({
                'id': h.id,
                'dia': self.DIAS.get(h.dia_semana, ''),
                'dia_semana': h.dia_semana,
                'hora_inicio': str(h.hora_inicio),
                'hora_fin': str(h.hora_fin),
                'aula': h.aula or '',
                'area': da.area.nombre,
                'docente': da.usuario.nombre_completo,
                'docente_asignacion_id': da.id,
            })
        if page is None or page_size is None:
            return list(result.values())
        return {
            'data': list(result.values()),
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }

    def guardar_horario(self, usuario, data):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos')

        validar_required(data, ['docente_asignacion_id', 'dia_semana', 'hora_inicio', 'hora_fin'])
        validar_dia_semana(data.get('dia_semana'))
        validar_hora(data.get('hora_inicio'), 'hora_inicio')
        validar_hora(data.get('hora_fin'), 'hora_fin')

        docente_asignacion_id = data.get('docente_asignacion_id')
        dia_semana = data.get('dia_semana')
        hora_inicio = data.get('hora_inicio')
        hora_fin = data.get('hora_fin')

        horario, created = Horarios.objects.update_or_create(
            docente_asignacion_id=docente_asignacion_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            defaults={
                'hora_fin': hora_fin,
                'aula': data.get('aula', ''),
            },
        )

        self.audit.record(usuario, accion='CREATE' if created else 'UPDATE', tabla='horarios', registro_id=horario.id, datos_nuevo={'docente_asignacion_id': docente_asignacion_id, 'dia_semana': dia_semana, 'hora_inicio': str(hora_inicio), 'hora_fin': str(hora_fin)})
        return {
            'id': horario.id,
            'mensaje': 'Horario creado' if created else 'Horario actualizado',
        }

    def actualizar_horario(self, usuario, horario_id, data):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos')

        try:
            horario = Horarios.objects.get(id=horario_id, activo=True)
        except Horarios.DoesNotExist:
            raise

        if 'dia_semana' in data:
            validar_dia_semana(data.get('dia_semana'))
            horario.dia_semana = data['dia_semana']
        if 'hora_inicio' in data:
            validar_hora(data.get('hora_inicio'), 'hora_inicio')
            horario.hora_inicio = data['hora_inicio']
        if 'hora_fin' in data:
            validar_hora(data.get('hora_fin'), 'hora_fin')
            horario.hora_fin = data['hora_fin']
        if 'aula' in data:
            horario.aula = data['aula']
        if 'docente_asignacion_id' in data:
            horario.docente_asignacion_id = data['docente_asignacion_id']
        horario.save()

        self.audit.record(usuario, accion='UPDATE', tabla='horarios', registro_id=horario.id, datos_nuevo={k: data[k] for k in data if k in data})
        return {
            'id': horario.id,
            'mensaje': 'Horario actualizado',
            'dia_semana': horario.dia_semana,
            'hora_inicio': str(horario.hora_inicio),
            'hora_fin': str(horario.hora_fin),
            'aula': horario.aula or '',
        }

    def eliminar_horario(self, usuario, horario_id):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos')

        Horarios.objects.filter(id=horario_id).update(activo=False)
        self.audit.record(usuario, accion='DELETE', tabla='horarios', registro_id=horario_id)
