import pytest
from datetime import date
from django.contrib.auth.hashers import make_password

from core.models import (
    Actividades, ActividadNotas, Areas, Cursos, DimensionesEvaluacion,
    DocenteAsignacion, Docentes, Estudiantes, Grados, Inscripciones, Niveles,
    Paralelos, Periodos, PeriodoCierreDocente, Roles, Usuarios,
)


@pytest.mark.django_db
class TestDocenteFullFlow:
    """Flujo completo: roles -> usuarios -> curso -> asignacion -> notas -> cierre -> boletin"""

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        director = Usuarios.objects.create(
            nombre='Director', email='dir@test.com',
            password_hash=make_password('123456'), rol=roles['director'], activo=True,
        )
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'], activo=True,
        )
        docente = Usuarios.objects.create(
            nombre='Docente', email='doc@test.com',
            password_hash=make_password('123456'), rol=roles['docente'], activo=True,
        )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematica')
        periodo = Periodos.objects.create(
            nombre='Trimestre 1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31', estado='activo',
        )
        dim = DimensionesEvaluacion.objects.create(nombre='SABER', orden=1, gestion=2026)
        docente_model = Docentes.objects.create(usuario=docente)
        from django.db import connection
        with connection.cursor() as c:
            c.execute(
                "CREATE VIEW IF NOT EXISTS v_notas_totales AS "
                "SELECT an.estudiante_id, a.docente_asignacion_id, "
                "a.periodo_id, COALESCE(SUM(an.valor), 0) AS nota_total, "
                "COUNT(DISTINCT a.id) AS dimensiones_evaluadas "
                "FROM actividades a "
                "JOIN actividad_notas an ON an.actividad_id = a.id "
                "GROUP BY an.estudiante_id, a.docente_asignacion_id, a.periodo_id"
            )
        return {
            'director': director, 'secretaria': secretaria, 'docente': docente,
            'docente_model': docente_model,
            'curso': curso, 'area': area, 'periodo': periodo, 'dimension': dim,
            'grado': grado, 'nivel': nivel,
        }

    def test_docente_full_flow(self, setup):
        from core.services.course_service import CourseService
        from core.services.enrollment_service import EnrollmentService
        from core.services.activity_service import ActivityService
        from core.services.cierre_service import CierreService
        from core.services.report_card_service import ReportCardService

        # 1. Crear DocenteAsignacion
        asignacion = CourseService().crear_asignacion(setup['director'], {
            'usuario_id': setup['docente'].id,
            'curso_id': setup['curso'].id,
            'area_id': setup['area'].id,
            'gestion': 2026,
        })
        da_id = asignacion['id']

        # 2. Inscribir 2 estudiantes
        est1 = EnrollmentService().enroll_new_student(setup['secretaria'], {
            'estudiante': {
                'rude': 'RUD100', 'ci': '10000001',
                'nombres': 'Juan', 'primer_apellido': 'Perez',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        est2 = EnrollmentService().enroll_new_student(setup['secretaria'], {
            'estudiante': {
                'rude': 'RUD101', 'ci': '10000002',
                'nombres': 'Ana', 'primer_apellido': 'Lopez',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        e1_id = est1['estudiante_id']
        e2_id = est2['estudiante_id']

        # 3. Login como docente -> crear actividad
        actividad = ActivityService().crear_actividad(setup['docente'], {
            'docente_asignacion_id': da_id,
            'nombre': 'Examen Trimestral',
            'dimension_id': setup['dimension'].id,
            'periodo_id': setup['periodo'].id,
            'fecha_actividad': date.today().isoformat(),
            'puntaje_maximo': 100,
        })
        act_id = actividad['id']

        # 4. Batch save notas for both students
        result = ActivityService().guardar_notas_batch(setup['docente'], [
            {
                'actividad_id': act_id,
                'notas': {str(e1_id): 85, str(e2_id): 90},
            },
        ])
        assert len(result) == 1
        assert result[0]['actividad_id'] == act_id
        assert result[0]['updated_count'] == 2

        # 5. Verify notas were created correctly
        notas_qs = ActividadNotas.objects.filter(actividad_id=act_id).order_by('estudiante_id')
        assert notas_qs.count() == 2
        notas_dict = {n.estudiante_id: float(n.valor) for n in notas_qs}
        assert notas_dict[e1_id] == 85
        assert notas_dict[e2_id] == 90

        # 6. Cerrar docente periodo (as director)
        cierre_result = CierreService().cerrar_docente(
            setup['director'], da_id, setup['periodo'].id,
        )
        assert cierre_result['mensaje'] == 'Periodo cerrado exitosamente para el docente'
        assert 'cierre_id' in cierre_result

        # 7. Verify PeriodoCierreDocente was created
        cierre = PeriodoCierreDocente.objects.get(
            docente_asignacion_id=da_id, periodo_id=setup['periodo'].id,
        )
        assert cierre.cerrado_por == setup['director']
        assert cierre.reabierto_por is None

        # 8. Verify cierre is persisted in DB
        cierres = PeriodoCierreDocente.objects.filter(docente_asignacion_id=da_id, periodo_id=setup['periodo'].id)
        assert cierres.count() == 1
        assert cierres.first().reabierto_por is None

        # 9. Director can list the cierre via CierreService.listar_cierres
        cierres = CierreService().listar_cierres(setup['director'])
        cierre_ids = [c['id'] for c in cierres]
        assert cierre.id in cierre_ids

        # 10. ReportCardService.generar_boletin works for the student
        boletin = ReportCardService().generar_boletin(
            setup['director'], e1_id, gestion=2026,
        )
        assert boletin['estudiante']['id'] == e1_id
        assert boletin['estudiante']['nombres'] == 'Juan'
        assert boletin['gestion'] == 2026
        assert len(boletin['materias']) >= 1
        # Find the Matematica area in materias
        matematica = [m for m in boletin['materias'] if m['area'] == 'Matematica']
        assert len(matematica) == 1
        periodo_str = str(setup['periodo'].id)
        nota_periodo = matematica[0]['notas_por_periodo'].get(periodo_str)
        assert nota_periodo is not None
        assert float(nota_periodo) > 0
