import pytest
from datetime import date
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Actividades, ActividadNotas, Areas, Cursos, DimensionesEvaluacion,
    DocenteAsignacion, Docentes, Estudiantes, Grados, Inscripciones, Niveles,
    Paralelos, Periodos, Roles, Usuarios,
)


@pytest.mark.django_db
class TestCompleteGradeWorkflow:
    """Login -> crear curso -> asignar docente -> inscribir estudiante -> poner notas -> cerrar periodo"""

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
        return {
            'director': director, 'secretaria': secretaria, 'docente': docente,
            'curso': curso, 'area': area, 'periodo': periodo, 'dimension': dim,
            'grado': grado, 'nivel': nivel,
        }

    def test_full_grading_flow(self, setup):
        from core.services.course_service import CourseService
        from core.services.enrollment_service import EnrollmentService
        from core.services.activity_service import ActivityService
        from core.services.grades_service import GradesService

        # 1. Asignar docente al curso
        asignacion = CourseService().crear_asignacion(setup['director'], {
            'usuario_id': setup['docente'].id,
            'curso_id': setup['curso'].id,
            'area_id': setup['area'].id,
            'gestion': 2026,
        })
        da_id = asignacion['id']

        # 2. Inscribir estudiante
        insc = EnrollmentService().enroll_new_student(setup['secretaria'], {
            'estudiante': {
                'rude': 'RUD001', 'ci': '12345678',
                'nombres': 'Juan', 'primer_apellido': 'Perez',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        estudiante_id = insc['estudiante_id']

        # 3. Crear actividad
        actividad = ActivityService().crear_actividad(setup['docente'], {
            'docente_asignacion_id': da_id,
            'nombre': 'Examen Final', 'dimension_id': setup['dimension'].id,
            'periodo_id': setup['periodo'].id, 'fecha_actividad': date.today().isoformat(),
            'puntaje_maximo': 100,
        })

        # 4. Poner notas
        ActivityService().guardar_notas_actividad(
            setup['docente'], actividad['id'],
            {str(estudiante_id): 85},
        )

        # 5. Verificar nota guardada directamente
        nota_obj = ActividadNotas.objects.get(actividad_id=actividad['id'], estudiante_id=estudiante_id)
        assert nota_obj.valor == 85

        # 6. Verificar notas del estudiante
        notas = ActivityService().get_notas_estudiante(setup['docente'], da_id, estudiante_id)
        assert str(actividad['id']) in notas

    def test_license_approval_flow(self, setup):
        from core.services.license_service import LicenseService
        from core.models import Licencias, Tutores

        Roles.objects.get_or_create(nombre='regente')
        regente_role = Roles.objects.get(nombre='regente')
        regente = Usuarios.objects.create(
            nombre='Regente', email='reg@test.com',
            password_hash=make_password('123456'), rol=regente_role, activo=True,
        )

        estudiante = Estudiantes.objects.create(
            rude='RUD002', ci='87654321', nombres='Maria', primer_apellido='Lopez',
        )
        tutor = Tutores.objects.create(
            ci='11111111', nombres='Tutor', primer_apellido='Test', celular='77700000',
        )

        # Crear licencia como regente
        result = LicenseService().crear(regente, {
            'estudiante_id': estudiante.id, 'motivo': 'Enfermedad',
            'fecha_inicio': '2026-05-01', 'fecha_fin': '2026-05-03',
            'tutor_id': tutor.id,
        })
        licencia_id = result['id']

        # Aprobar como secretaria
        result = LicenseService().aprobar(setup['secretaria'], licencia_id, aceptar=True)
        assert result['estado'] == 'aprobada'


@pytest.mark.django_db
class TestAttendanceAndScheduleIntegration:
    """Flujo completo: horarios + asistencia"""

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
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
        area = Areas.objects.create(nombre='Geografia')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        estudiante = Estudiantes.objects.create(
            rude='RUD003', ci='99999999', nombres='Ana', primer_apellido='Cruz',
        )
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        return {
            'secretaria': secretaria, 'docente': docente, 'da': da,
            'estudiante': estudiante, 'curso': curso, 'grado': grado,
        }

    def test_schedule_and_attendance(self, setup):
        from core.services.schedule_service import ScheduleService
        from core.services.attendance_service import AttendanceService

        # 1. Crear horario
        ScheduleService().guardar_horario(setup['secretaria'], {
            'docente_asignacion_id': setup['da'].id,
            'dia_semana': 1, 'hora_inicio': '08:00', 'hora_fin': '09:30', 'aula': 'A101',
        })

        # 2. Listar horarios por curso
        horarios = ScheduleService().listar_horarios(setup['secretaria'], curso_id=setup['curso'].id)
        assert len(horarios) >= 1

        # 3. Marcar asistencia
        hoy = date.today().isoformat()
        AttendanceService().marcar_asistencias(
            setup['docente'], setup['da'].id, hoy,
            {str(setup['estudiante'].id): 'presente'},
        )

        # 4. Listar asistencia
        asistencias = AttendanceService().listar_asistencias(
            setup['docente'], setup['da'].id, hoy,
        )
        assert len(asistencias) == 1
        assert asistencias[0]['estado'] == 'presente'


@pytest.mark.django_db
class TestStudentLifecycle:
    """Crear estudiante -> buscar -> actualizar -> soft-delete -> (falta restore)"""

    @pytest.fixture
    def setup(self):
        role = Roles.objects.get_or_create(nombre='secretaria')[0]
        usuario = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=role, activo=True,
        )
        return {'usuario': usuario}

    def test_student_lifecycle(self, setup):
        from core.services.students_service import StudentsService
        svc = StudentsService()

        # 1. Crear
        e = svc.crear(setup['usuario'], {
            'rude': 'RUDLIFE', 'ci': '77777777',
            'nombres': 'Lifecycle', 'primer_apellido': 'Test',
        })
        e_id = e['id']

        # 2. Obtener
        obtenido = svc.obtener(setup['usuario'], e_id)
        assert obtenido['nombres'] == 'Lifecycle'

        # 3. Buscar
        resultados = svc.listar(setup['usuario'], query='Lifecycle')
        assert resultados['total'] == 1

        # 4. Actualizar
        actualizado = svc.actualizar(setup['usuario'], e_id, {'nombres': 'Updated'})
        assert actualizado['nombres'] == 'Updated'

        # 5. Soft delete
        svc.eliminar(setup['usuario'], e_id)
        from core.models import Estudiantes
        estudiante_db = Estudiantes.objects.get(id=e_id)
        assert estudiante_db.estado == 'inactivo'
