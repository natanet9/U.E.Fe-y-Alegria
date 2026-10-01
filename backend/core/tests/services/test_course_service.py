import pytest
from django.contrib.auth.hashers import make_password

from core.models import Areas, Cursos, DocenteAsignacion, Docentes, Grados, Niveles, Paralelos, Roles, Usuarios
from core.services.course_service import CourseService


@pytest.mark.django_db
class TestCourseService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'),
            Roles(nombre='docente'), Roles(nombre='regente'), Roles(nombre='tutor'),
        ])}
        director = Usuarios.objects.create(
            nombre='Director', email='dir@test.com',
            password_hash=make_password('123456'), rol=roles['director'],
        )
        docente = Usuarios.objects.create(
            nombre='Docente', email='doc@test.com',
            password_hash=make_password('123456'), rol=roles['docente'],
        )
        regente = Usuarios.objects.create(
            nombre='Regente', email='reg@test.com',
            password_hash=make_password('123456'), rol=roles['regente'],
        )
        tutor = Usuarios.objects.create(
            nombre='Tutor', email='tut@test.com',
            password_hash=make_password('123456'), rol=roles['tutor'],
        )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Lenguaje')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        return {
            'director': director, 'docente': docente, 'regente': regente,
            'tutor': tutor, 'da': da, 'curso': curso, 'area': area,
        }

    def test_listar_asignaciones_admin(self, setup):
        result = CourseService().listar_asignaciones(setup['director'])
        assert len(result) == 1
        assert result[0]['docente'] == 'Docente'

    def test_listar_asignaciones_docente(self, setup):
        result = CourseService().listar_asignaciones(setup['docente'])
        assert len(result) == 1
        assert result[0]['docente'] == 'Docente'

    def test_listar_asignaciones_other_docente(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro', email='otro@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        result = CourseService().listar_asignaciones(otro)
        assert result == []

    def test_listar_asignaciones_tutor(self, setup):
        result = CourseService().listar_asignaciones(setup['tutor'])
        assert result == []

    def test_listar_asignaciones_regente(self, setup):
        result = CourseService().listar_asignaciones(setup['regente'])
        assert len(result) == 1

    def test_crear_asignacion_success(self, setup):
        area2 = Areas.objects.create(nombre='Matematicas')
        result = CourseService().crear_asignacion(setup['director'], {
            'usuario_id': setup['docente'].id,
            'curso_id': setup['curso'].id,
            'area_id': area2.id,
            'gestion': 2026,
        })
        assert result['usuario'] == 'Docente'
        assert result['gestion'] == 2026

    def test_crear_asignacion_permision(self, setup):
        with pytest.raises(PermissionError):
            CourseService().crear_asignacion(setup['tutor'], {
                'usuario_id': 1, 'curso_id': 1, 'area_id': 1, 'gestion': 2026,
            })

    def test_crear_asignacion_validation(self, setup):
        with pytest.raises(ValueError, match='Campos requeridos faltantes'):
            CourseService().crear_asignacion(setup['director'], {
                'usuario_id': 1, 'curso_id': 1,
            })

    def test_crear_asignacion_usuario_not_found(self, setup):
        with pytest.raises(Usuarios.DoesNotExist):
            CourseService().crear_asignacion(setup['director'], {
                'usuario_id': 99999, 'curso_id': setup['curso'].id,
                'area_id': setup['area'].id, 'gestion': 2026,
            })

    def test_eliminar_y_restaurar_asignacion(self, setup):
        service = CourseService()
        service.eliminar(setup['director'], setup['da'].id)
        setup['da'].refresh_from_db()
        assert setup['da'].activo is False

        restored = service.restaurar(setup['director'], setup['da'].id)
        setup['da'].refresh_from_db()
        assert setup['da'].activo is True
        assert restored['usuario'] == 'Docente'

    def test_eliminar_asignacion_permision(self, setup):
        with pytest.raises(PermissionError):
            CourseService().eliminar(setup['tutor'], setup['da'].id)

    def test_actualizar_asignacion(self, setup):
        area2 = Areas.objects.create(nombre='Matematicas')
        actualizado = CourseService().actualizar_asignacion(setup['director'], setup['da'].id, {
            'area_id': area2.id,
            'gestion': 2027,
        })
        assert actualizado['area'] == 'Matematicas'
        assert actualizado['gestion'] == 2027

    def test_actualizar_asignacion_permision(self, setup):
        with pytest.raises(PermissionError):
            CourseService().actualizar_asignacion(setup['tutor'], setup['da'].id, {'gestion': 2027})
