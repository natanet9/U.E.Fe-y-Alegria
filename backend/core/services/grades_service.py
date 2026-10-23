from django.db.models import Avg
from django.utils import timezone

from ..models import (
    Actividades, ActividadNotas, DimensionConfigPeriodo,
    DimensionesEvaluacion, DocenteAsignacion, Estudiantes,
    Grados, Inscripciones, Periodos, Asistencias,
)
from .access_service import AccessControlService
from ..tracing import trace_service_class


@trace_service_class
class GradesService:

    def __init__(self):
        self.ac = AccessControlService()

    def _ensure_auto_actividad(self, docente_asignacion_id, periodo_id):
        dimension = DimensionesEvaluacion.objects.filter(
            nombre__iexact='AUTOEVALUACION', activo=True
        ).first()
        if not dimension:
            return None
        config = DimensionConfigPeriodo.objects.filter(
            periodo_id=periodo_id, dimension=dimension
        ).first()
        puntaje_maximo = float(config.puntaje_maximo) if config and config.puntaje_maximo else (
            float(dimension.puntaje_maximo) if dimension.puntaje_maximo else 5
        )
        actividad, _ = Actividades.objects.get_or_create(
            docente_asignacion_id=docente_asignacion_id,
            periodo_id=periodo_id,
            dimension=dimension,
            defaults={
                'nombre': 'AUTOEVALUACION',
                'puntaje_maximo': puntaje_maximo,
                'fecha_actividad': timezone.now().date(),
            },
        )
        return actividad.id

    def get_course_detail(self, usuario, docente_asignacion_id, periodo_id=None):
        da = DocenteAsignacion.objects.select_related(
            'curso__grado__nivel', 'curso__paralelo', 'area'
        ).get(id=docente_asignacion_id)

        if not self.ac.puede_editar_notas(usuario, docente_asignacion_id):
            raise PermissionError('No tienes permisos para ver este curso')

        gestion = da.gestion
        estudiantes = self._get_estudiantes_curso(da.curso, gestion)
        periodos = self._list_periodos(gestion)
        if not periodo_id:
            periodo_activo = next((p for p in periodos if p['estado'] == 'activo'), periodos[0] if periodos else None)
            periodo_id = periodo_activo['id'] if periodo_activo else None
        dimensiones = self._list_dimensiones(periodo_id)
        if periodo_id:
            self._ensure_auto_actividad(docente_asignacion_id, periodo_id)
        from .activity_service import ActivityService
        actividades = ActivityService()._list_actividades(docente_asignacion_id)
        actividad_notas = self._get_actividad_notas_map(docente_asignacion_id)
        notas_dimension = self._get_notas_dimension(docente_asignacion_id, periodo_id)

        # Compute rendimiento (average of actividad notas) and asistencia (%) for this docente asignacion
        try:
            rendimiento_agg = ActividadNotas.objects.filter(actividad__docente_asignacion_id=docente_asignacion_id).aggregate(promedio=Avg('valor'))
            rendimiento = round(float(rendimiento_agg['promedio']), 1) if rendimiento_agg and rendimiento_agg['promedio'] is not None else None
        except Exception:
            rendimiento = None

        try:
            total_asist = Asistencias.objects.filter(docente_asignacion_id=docente_asignacion_id).count()
            presentes = Asistencias.objects.filter(docente_asignacion_id=docente_asignacion_id, estado='presente').count()
            asistencia = round(presentes / total_asist * 100, 1) if total_asist > 0 else None
        except Exception:
            asistencia = None

        asignaciones_curso = DocenteAsignacion.objects.filter(
            curso=da.curso, gestion=gestion, activo=True
        ).select_related('area', 'docente__usuario').order_by('area__nombre')

        from .cierre_service import CierreService
        cerrado_info = CierreService().obtener_estado(docente_asignacion_id, periodo_id) if periodo_id else {'cerrado': False}

        return {
            'curso': {
                'id': da.curso.id,
                'grado': da.curso.grado.nombre,
                'paralelo': da.curso.paralelo.nombre,
                'area': da.area.nombre,
                'area_id': da.area_id,
                'nivel': da.curso.grado.nivel.nombre,
            },
            'asignaciones': [
                {
                    'id': a.id,
                    'area': a.area.nombre,
                    'area_id': a.area_id,
                    'docente': a.docente.usuario.nombre_completo if a.docente and a.docente.usuario else None,
                }
                for a in asignaciones_curso
            ],
            'rendimiento': rendimiento,
            'asistencia': asistencia,
            'estudiantes': estudiantes,
            'periodos': periodos,
            'dimensiones': dimensiones,
            'actividades': actividades,
            'actividad_notas': actividad_notas,
            'notas_dimension': notas_dimension,
            'cerrado': cerrado_info['cerrado'],
        }

    def _get_estudiantes_curso(self, curso, gestion):
        inscripciones = Inscripciones.objects.filter(
            curso=curso, gestion=gestion, estado='activo'
        ).select_related('estudiante')
        return [
            {
                'id': ins.estudiante.id,
                'nombres': ins.estudiante.nombres,
                'primer_apellido': ins.estudiante.primer_apellido,
                'rude': ins.estudiante.rude,
            }
            for ins in inscripciones
        ]

    def _list_periodos(self, gestion):
        return [
            {'id': p.id, 'nombre': p.nombre, 'numero': p.numero, 'gestion': p.gestion, 'estado': p.estado}
            for p in Periodos.objects.filter(gestion=gestion, estado='activo').order_by('numero')
        ]

    def _list_dimensiones(self, periodo_id=None):
        config_map = {}
        gestion = None
        if periodo_id:
            config_map = {
                c.dimension_id: float(c.puntaje_maximo)
                for c in DimensionConfigPeriodo.objects.filter(periodo_id=periodo_id)
            }
            try:
                periodo = Periodos.objects.get(id=periodo_id)
                gestion = periodo.gestion
            except Periodos.DoesNotExist:
                pass
        qs = DimensionesEvaluacion.objects.all().order_by('orden')
        if gestion:
            qs = qs.filter(gestion=gestion)
        return [
            {
                'id': d.id,
                'nombre': d.nombre,
                'orden': d.orden,
                'gestion': d.gestion,
                'puntaje_maximo': config_map.get(d.id, float(d.puntaje_maximo) if d.puntaje_maximo is not None else 0),
            }
            for d in qs
        ]

    def _get_actividad_notas_map(self, docente_asignacion_id):
        qs = ActividadNotas.objects.filter(
            actividad__docente_asignacion_id=docente_asignacion_id
        ).select_related('actividad', 'estudiante')
        result = {}
        for an in qs:
            act_key = str(an.actividad_id)
            est_key = str(an.estudiante_id)
            result.setdefault(act_key, {})[est_key] = float(an.valor) if an.valor is not None else None
        return result

    def _calcular_notas_dimension(self, docente_asignacion_id, periodo_id):
        """Calcula nota por (estudiante, dimension) usando ORM puro.

        Lógica equivalente a la vista v_notas_por_dimension:
          - Promedia las notas de las actividades de cada dimensión
            (cada actividad pesa igual, normalizada sobre su puntaje_maximo)
          - Escala el promedio al puntaje_maximo configurado para esa dimensión
            en el período (DimensionConfigPeriodo) o al puntaje de la dimensión.

        Retorna dict: {str(estudiante_id): {str(dimension_id): nota_float}}
        """
        if not periodo_id:
            return {}

        # Obtener puntajes máximos configurados por dimensión en este período
        config_map = {
            c.dimension_id: float(c.puntaje_maximo)
            for c in DimensionConfigPeriodo.objects.filter(periodo_id=periodo_id)
        }
        # Fallback al puntaje de la dimensión si no hay config
        dim_puntaje_map = {
            d.id: float(d.puntaje_maximo or 0)
            for d in DimensionesEvaluacion.objects.all()
        }

        # Traer todas las notas de actividades de esta asignación/período
        notas_qs = (
            ActividadNotas.objects
            .filter(
                actividad__docente_asignacion_id=docente_asignacion_id,
                actividad__periodo_id=periodo_id,
            )
            .select_related('actividad')
            .values('estudiante_id', 'actividad__dimension_id',
                    'actividad__puntaje_maximo', 'valor')
        )

        # Agrupar por (estudiante, dimension) → lista de (valor, puntaje_max)
        grupos = {}
        for row in notas_qs:
            key = (row['estudiante_id'], row['actividad__dimension_id'])
            grupos.setdefault(key, []).append((
                float(row['valor'] or 0),
                float(row['actividad__puntaje_maximo'] or 0),
            ))

        result = {}
        for (est_id, dim_id), pares in grupos.items():
            puntaje_dim = config_map.get(dim_id, dim_puntaje_map.get(dim_id, 0))
            # Promedio de ratios (valor / puntaje_maximo_actividad)
            ratios = [v / p for v, p in pares if p > 0]
            if ratios:
                promedio = sum(ratios) / len(ratios)
                nota = round(promedio * puntaje_dim, 2)
            else:
                nota = 0.0
            result.setdefault(str(est_id), {})[str(dim_id)] = nota

        return result

    def _get_notas_dimension(self, docente_asignacion_id, periodo_id=None):
        """Interfaz compatible con el código existente."""
        return self._calcular_notas_dimension(docente_asignacion_id, periodo_id)

    def get_notas_totales(self, usuario, docente_asignacion_id, periodo_id):
        if not self.ac.puede_editar_notas(usuario, docente_asignacion_id) and not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No tienes permisos para ver estas notas')

        notas_dim = self._calcular_notas_dimension(docente_asignacion_id, periodo_id)
        result = []
        for est_id_str, dims in notas_dim.items():
            total = round(sum(dims.values()), 2)
            result.append({
                'estudiante_id': int(est_id_str),
                'periodo_id': periodo_id,
                'nota_total': total,
                'dimensiones_evaluadas': len(dims),
            })
        return result

    def get_notas_por_dimension(self, usuario, docente_asignacion_id, periodo_id, _skip_perm_check=False):
        if not _skip_perm_check:
            if not self.ac.puede_editar_notas(usuario, docente_asignacion_id) and not self.ac.puede_ver_todo(usuario):
                raise PermissionError('No tienes permisos para ver estas notas')

        config_map = {
            c.dimension_id: float(c.puntaje_maximo)
            for c in DimensionConfigPeriodo.objects.filter(periodo_id=periodo_id)
        }
        dims = {d.id: d for d in DimensionesEvaluacion.objects.all().order_by('orden')}

        notas_qs = (
            ActividadNotas.objects
            .filter(
                actividad__docente_asignacion_id=docente_asignacion_id,
                actividad__periodo_id=periodo_id,
            )
            .select_related('actividad')
            .values('estudiante_id', 'actividad__dimension_id',
                    'actividad__puntaje_maximo', 'valor')
        )

        grupos = {}
        for row in notas_qs:
            key = (row['estudiante_id'], row['actividad__dimension_id'])
            grupos.setdefault(key, []).append((
                float(row['valor'] or 0),
                float(row['actividad__puntaje_maximo'] or 0),
            ))

        result = []
        for (est_id, dim_id), pares in grupos.items():
            dim = dims.get(dim_id)
            puntaje_dim = config_map.get(dim_id, float(dim.puntaje_maximo or 0) if dim else 0)
            ratios = [v / p for v, p in pares if p > 0]
            if ratios:
                promedio = sum(ratios) / len(ratios)
                nota = round(promedio * puntaje_dim, 2)
            else:
                promedio = 0.0
                nota = 0.0
            result.append({
                'estudiante_id': est_id,
                'dimension_id': dim_id,
                'nota': nota,
                'promedio': round(promedio, 4) if ratios else 0.0,
                'puntaje_maximo': puntaje_dim,
                'dimension_nombre': dim.nombre if dim else '',
            })
        # Ordenar por estudiante y orden de dimensión
        result.sort(key=lambda r: (r['estudiante_id'], dims[r['dimension_id']].orden if r['dimension_id'] in dims else 0))
        return result

    def get_notas_por_dimension_interno(self, docente_asignacion_id, periodo_id):
        """Versión sin verificación de permisos para uso interno (ej. reports_service)."""
        return self.get_notas_por_dimension(
            usuario=None,
            docente_asignacion_id=docente_asignacion_id,
            periodo_id=periodo_id,
            _skip_perm_check=True,
        )
