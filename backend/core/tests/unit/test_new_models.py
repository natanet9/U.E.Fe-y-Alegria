import pytest

from core.models import (
    Actividades, ActividadNotas, Areas, Cursos, DimensionesEvaluacion,
    DocenteAsignacion, Docentes, Estudiantes, Grados, Niveles, Paralelos, Periodos, Roles, Usuarios,
)


@pytest.mark.django_db
class TestModels:

    def test_crear_actividad(self):
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Arte')
        rol = Roles.objects.create(nombre='docente')
        usuario = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash='hash', rol=rol,
        )
        docente_model = Docentes.objects.create(usuario=usuario)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31',
        )
        dim = DimensionesEvaluacion.objects.create(nombre='SABER', orden=2, gestion=2026)
        act = Actividades.objects.create(
            docente_asignacion=da, periodo=periodo, dimension=dim,
            nombre='Tarea 1', puntaje_maximo=100, fecha_actividad='2026-02-10',
        )
        assert act.puntaje_maximo == 100

    def test_actividad_notas_unique(self):
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Arte')
        rol = Roles.objects.create(nombre='docente')
        usuario = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash='hash', rol=rol,
        )
        docente_model = Docentes.objects.create(usuario=usuario)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        periodo = Periodos.objects.create(
            nombre='T1', gestion=2026, numero=1,
            fecha_inicio='2026-01-01', fecha_fin='2026-03-31',
        )
        dim = DimensionesEvaluacion.objects.create(nombre='SABER', orden=2, gestion=2026)
        act = Actividades.objects.create(
            docente_asignacion=da, periodo=periodo, dimension=dim,
            nombre='Tarea 1', puntaje_maximo=100, fecha_actividad='2026-02-10',
        )
        est = Estudiantes.objects.create(
            rude='RUD001', ci='12345678', nombres='Ana', primer_apellido='Perez',
        )
        ActividadNotas.objects.create(actividad=act, estudiante=est, valor=88)
        assert ActividadNotas.objects.count() == 1
        with pytest.raises(Exception):
            ActividadNotas.objects.create(actividad=act, estudiante=est, valor=90)

    def test_estudiante_duplicate_apellido(self):
        Estudiantes.objects.create(
            rude='RUD001', ci='11111111', nombres='Ana',
            primer_apellido='Perez',
        )
        Estudiantes.objects.create(
            rude='RUD002', ci='22222222', nombres='Luis',
            primer_apellido='Perez',
        )
        assert Estudiantes.objects.filter(primer_apellido='Perez').count() == 2

    def test_usuario_unique_email(self):
        rol = Roles.objects.create(nombre='docente')
        Usuarios.objects.create(
            nombre='U1', email='same@test.com',
            password_hash='hash', rol=rol,
        )
        with pytest.raises(Exception):
            Usuarios.objects.create(
                nombre='U2', email='same@test.com',
                password_hash='hash2', rol=rol,
            )

    def test_inscripcion_unique_per_gestion(self):
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        est = Estudiantes.objects.create(
            rude='RUD001', ci='11111111', nombres='Ana',
            primer_apellido='Perez',
        )
        from core.models import Inscripciones
        Inscripciones.objects.create(estudiante=est, curso=curso, gestion=2026)
        with pytest.raises(Exception):
            Inscripciones.objects.create(estudiante=est, curso=curso, gestion=2026)
