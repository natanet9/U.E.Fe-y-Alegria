from django.db import connection
from django.utils import timezone

from ..models import PeriodoCierreDocente
from ..tracing import trace_service_class
from .access_service import AccessControlService
from .audit_service import AuditService


@trace_service_class
class CierreService:

    def __init__(self):
        self.ac = AccessControlService()
        self.audit = AuditService()

    def _validar_completitud(self, docente_asignacion_id, periodo_id):
        """Verifica que todos los estudiantes tengan nota en el periodo."""
        from ..models import Inscripciones, DocenteAsignacion
        da = DocenteAsignacion.objects.get(id=docente_asignacion_id)
        total = Inscripciones.objects.filter(
            curso=da.curso, gestion=da.gestion, estado='activo'
        ).count()
        if not total:
            return
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(DISTINCT v.estudiante_id)
                   FROM v_notas_totales v
                   WHERE v.docente_asignacion_id = %s AND v.periodo_id = %s""",
                [docente_asignacion_id, periodo_id],
            )
            con_notas = cursor.fetchone()[0] or 0
        if con_notas < total:
            raise ValueError(
                f'Faltan notas para {total - con_notas} estudiante(s). '
                'Complete todas las notas antes de cerrar.'
            )

    def cerrar_docente(self, usuario, docente_asignacion_id, periodo_id):
        if not self.ac.puede_cerrar_propio_periodo(usuario, docente_asignacion_id):
            raise PermissionError('No tienes permiso para cerrar este periodo')

        self._validar_completitud(docente_asignacion_id, periodo_id)

        cierre, created = PeriodoCierreDocente.objects.get_or_create(
            docente_asignacion_id=docente_asignacion_id,
            periodo_id=periodo_id,
            defaults={
                'cerrado_por': usuario,
                'cerrado_en': timezone.now(),
            },
        )

        if not created:
            return {'mensaje': 'El periodo ya estaba cerrado para este docente'}

        self.audit.record(usuario, accion='CLOSE', tabla='periodo_cierre_docente', registro_id=cierre.id, datos_nuevo={'docente_asignacion_id': docente_asignacion_id, 'periodo_id': periodo_id})
        return {
            'mensaje': 'Periodo cerrado exitosamente para el docente',
            'cierre_id': cierre.id,
        }

    def reabrir_docente(self, usuario, docente_asignacion_id, periodo_id):
        if not self.ac.puede_cerrar_periodo(usuario):
            raise PermissionError('Solo el director o secretaria pueden reabrir periodos cerrados')

        cierre = PeriodoCierreDocente.objects.filter(
            docente_asignacion_id=docente_asignacion_id,
            periodo_id=periodo_id,
        ).first()

        if not cierre:
            raise ValueError('No hay cierre para esta combinacion')

        cierre.reabierto_por = usuario
        cierre.reabierto_en = timezone.now()
        cierre.save(update_fields=['reabierto_por', 'reabierto_en'])

        self.audit.record(usuario, accion='REOPEN', tabla='periodo_cierre_docente', registro_id=cierre.id, datos_nuevo={'docente_asignacion_id': docente_asignacion_id, 'periodo_id': periodo_id})
        return {'mensaje': 'Periodo reabierto exitosamente'}

    def listar_cierres(self, usuario, docente_asignacion_id=None, periodo_id=None):
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos')

        qs = PeriodoCierreDocente.objects.select_related(
            'periodo', 'docente_asignacion__docente__usuario',
            'docente_asignacion__area', 'cerrado_por',
        )

        if docente_asignacion_id:
            qs = qs.filter(docente_asignacion_id=docente_asignacion_id)
        if periodo_id:
            qs = qs.filter(periodo_id=periodo_id)

        return [
            {
                'id': c.id,
                'docente_asignacion_id': c.docente_asignacion_id,
                'docente': c.docente_asignacion.usuario.nombre_completo,
                'area': c.docente_asignacion.area.nombre,
                'periodo': c.periodo.nombre,
                'gestion': c.periodo.gestion,
                'cerrado_por': c.cerrado_por.nombre_completo,
                'cerrado_en': str(c.cerrado_en),
                'reabierto': c.reabierto_por is not None,
            }
            for c in qs
        ]

    def obtener_estado(self, docente_asignacion_id, periodo_id):
        """Returns {'cerrado': True/False} for a given assignment+period."""
        existe = PeriodoCierreDocente.objects.filter(
            docente_asignacion_id=docente_asignacion_id,
            periodo_id=periodo_id,
            reabierto_por__isnull=True,
        ).exists()
        return {'cerrado': existe}
