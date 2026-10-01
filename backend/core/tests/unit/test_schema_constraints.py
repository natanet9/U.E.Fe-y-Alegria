import pytest
from django.db import IntegrityError
from django.db.models import Q

from core.models import (
    Areas, Asistencias, Cursos, DimensionesEvaluacion,
    DocenteAsignacion, Docentes, Estudiantes, Grados,
    Inscripciones, Niveles, Paralelos, Periodos, Roles, Usuarios,
)


@pytest.mark.django_db
class TestAsistenciasPartialUnique:

    def _setup(self):
        rol = Roles.objects.create(nombre='director')
        usuario = Usuarios.objects.create(
            nombre='Test', primer_apellido='User', email='t@t.com',
            password_hash='hash', rol=rol,
        )
        estudiante = Estudiantes.objects.create(
            nombres='Juan', primer_apellido='Perez',
            rude='RUDE001', ci='12345',
        )
        return usuario, estudiante

    def _make_asignacion(self, docente, curso, area, gestion=2026):
        return DocenteAsignacion.objects.create(
            docente=docente, curso=curso, area=area, gestion=gestion,
        )

    def test_duplicate_with_asignacion_raises(self):
        usuario, estudiante = self._setup()
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, numero=1, nombre='1ro')
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematicas')
        docente = Docentes.objects.create(usuario=usuario)
        da = self._make_asignacion(docente, curso, area)

        Asistencias.objects.create(
            estudiante=estudiante, docente_asignacion=da,
            fecha='2026-03-15', estado='presente', tipo='por_asignacion',
            registrado_por=usuario,
        )
        with pytest.raises(IntegrityError):
            Asistencias.objects.create(
                estudiante=estudiante, docente_asignacion=da,
                fecha='2026-03-15', estado='ausente', tipo='por_asignacion',
                registrado_por=usuario,
            )

    def test_duplicate_without_asignacion_raises(self):
        usuario, estudiante = self._setup()
        Asistencias.objects.create(
            estudiante=estudiante, docente_asignacion=None,
            fecha='2026-03-15', estado='presente', tipo='administrativa',
            registrado_por=usuario,
        )
        with pytest.raises(IntegrityError):
            Asistencias.objects.create(
                estudiante=estudiante, docente_asignacion=None,
                fecha='2026-03-15', estado='presente', tipo='administrativa',
                registrado_por=usuario,
            )

    def test_same_student_diff_asignacion_allowed(self):
        usuario, estudiante = self._setup()
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, numero=1, nombre='1ro')
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematicas')
        docente = Docentes.objects.create(usuario=usuario)
        da1 = self._make_asignacion(docente, curso, area)
        area2 = Areas.objects.create(nombre='Lenguaje')
        da2 = self._make_asignacion(docente, curso, area2)

        Asistencias.objects.create(
            estudiante=estudiante, docente_asignacion=da1,
            fecha='2026-03-15', estado='presente', tipo='por_asignacion',
            registrado_por=usuario,
        )
        Asistencias.objects.create(
            estudiante=estudiante, docente_asignacion=da2,
            fecha='2026-03-15', estado='presente', tipo='por_asignacion',
            registrado_por=usuario,
        )

    def test_one_with_null_one_with_asignacion_allowed(self):
        usuario, estudiante = self._setup()
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, numero=1, nombre='1ro')
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematicas')
        docente = Docentes.objects.create(usuario=usuario)
        da = self._make_asignacion(docente, curso, area)

        Asistencias.objects.create(
            estudiante=estudiante, docente_asignacion=None,
            fecha='2026-03-15', estado='presente', tipo='administrativa',
            registrado_por=usuario,
        )
        Asistencias.objects.create(
            estudiante=estudiante, docente_asignacion=da,
            fecha='2026-03-15', estado='presente', tipo='por_asignacion',
            registrado_por=usuario,
        )


@pytest.mark.django_db
class TestInscripcionesPartialUnique:

    def _setup(self):
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, numero=1, nombre='1ro')
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        estudiante = Estudiantes.objects.create(
            nombres='Juan', primer_apellido='Perez',
            rude='RUDE001', ci='12345',
        )
        return estudiante, curso

    def test_duplicate_activo_raises(self):
        estudiante, curso = self._setup()
        Inscripciones.objects.create(
            estudiante=estudiante, curso=curso, gestion=2026, estado='activo',
        )
        with pytest.raises(IntegrityError):
            Inscripciones.objects.create(
                estudiante=estudiante, curso=curso, gestion=2026, estado='activo',
            )

    def test_retired_then_re_enroll_allowed(self):
        estudiante, curso = self._setup()
        Inscripciones.objects.create(
            estudiante=estudiante, curso=curso, gestion=2026, estado='retirado', activo=False,
        )
        Inscripciones.objects.create(
            estudiante=estudiante, curso=curso, gestion=2026, estado='activo',
        )

    def test_same_student_diff_gestion_allowed(self):
        estudiante, curso = self._setup()
        Inscripciones.objects.create(
            estudiante=estudiante, curso=curso, gestion=2026, estado='activo',
        )
        Inscripciones.objects.create(
            estudiante=estudiante, curso=curso, gestion=2027, estado='activo',
        )


@pytest.mark.django_db
class TestPeriodosNumeroUniqueness:

    def _setup(self):
        rol = Roles.objects.create(nombre='director')
        usuario = Usuarios.objects.create(nombre='Admin', email='a@a.com', password_hash='hash', rol=rol)
        return usuario

    def test_duplicate_numero_gestion_raises(self):
        self._setup()
        Periodos.objects.create(nombre='Trim1', gestion=2026, numero=1, fecha_inicio='2026-01-01', fecha_fin='2026-03-31')
        with pytest.raises(IntegrityError):
            Periodos.objects.create(nombre='Trim1dup', gestion=2026, numero=1, fecha_inicio='2026-01-01', fecha_fin='2026-03-31')

    def test_same_numero_diff_gestion_allowed(self):
        self._setup()
        Periodos.objects.create(nombre='Trim1', gestion=2026, numero=1, fecha_inicio='2026-01-01', fecha_fin='2026-03-31')
        Periodos.objects.create(nombre='Trim1_2027', gestion=2027, numero=1, fecha_inicio='2027-01-01', fecha_fin='2027-03-31')

    def test_diff_numero_same_gestion_allowed(self):
        self._setup()
        Periodos.objects.create(nombre='Trim1', gestion=2026, numero=1, fecha_inicio='2026-01-01', fecha_fin='2026-03-31')
        Periodos.objects.create(nombre='Trim2', gestion=2026, numero=2, fecha_inicio='2026-04-01', fecha_fin='2026-06-30')


@pytest.mark.django_db
class TestCursosGestionUniqueness:

    def _setup(self):
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, numero=1, nombre='1ro')
        paralelo = Paralelos.objects.create(nombre='A')
        return grado, paralelo

    def test_duplicate_grado_paralelo_gestion_raises(self):
        grado, paralelo = self._setup()
        Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        with pytest.raises(IntegrityError):
            Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)

    def test_same_grado_paralelo_diff_gestion_allowed(self):
        grado, paralelo = self._setup()
        Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2027)


@pytest.mark.django_db
class TestDimensionesEvaluacionUniqueness:

    def test_duplicate_nombre_gestion_raises(self):
        DimensionesEvaluacion.objects.create(nombre='SER', gestion=2026, orden=1)
        with pytest.raises(IntegrityError):
            DimensionesEvaluacion.objects.create(nombre='SER', gestion=2026, orden=1)

    def test_same_nombre_diff_gestion_allowed(self):
        DimensionesEvaluacion.objects.create(nombre='SER', gestion=2026, orden=1)
        DimensionesEvaluacion.objects.create(nombre='SER', gestion=2027, orden=1)

    def test_diff_nombre_same_gestion_allowed(self):
        DimensionesEvaluacion.objects.create(nombre='SER', gestion=2026, orden=1)
        DimensionesEvaluacion.objects.create(nombre='SABER', gestion=2026, orden=2)


@pytest.mark.django_db
class TestConfiguracionEscuelaSingleton:

    def test_get_or_create_returns_existing(self):
        from core.models import ConfiguracionEscuela
        ConfiguracionEscuela.objects.create(
            nombre='U.E. Original', gestion_actual=2026,
        )
        config, created = ConfiguracionEscuela.objects.get_or_create(id=1)
        assert created is False
        assert config.nombre == 'U.E. Original'

    def test_get_or_create_creates_first(self):
        from core.models import ConfiguracionEscuela
        config, created = ConfiguracionEscuela.objects.get_or_create(id=1)
        assert created is True
        assert config.nombre == 'Unidad Educativa'
