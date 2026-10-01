import pytest
from django.contrib.auth.hashers import make_password

from core.models import (
    Areas, Cursos, Estudiantes, Grados, Inscripciones, Niveles,
    Paralelos, Roles, Tutores, Usuarios,
)
from core.services.enrollment_service import EnrollmentService


@pytest.mark.django_db
class TestEnrollmentService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        usuario = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'],
        )
        inicial = Niveles.objects.create(nombre='Inicial')
        grado = Grados.objects.create(nivel=inicial, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        return {'usuario': usuario, 'curso': curso, 'grado': grado}

    def test_search_existing_student_not_found(self, setup):
        result = EnrollmentService().search_existing_student(setup['usuario'], 'NOEXIST')
        assert result is None

    def test_enroll_new_student(self, setup):
        result = EnrollmentService().enroll_new_student(setup['usuario'], {
            'estudiante': {
                'rude': 'RUD001', 'ci': '12345678',
                'nombres': 'Juan', 'primer_apellido': 'Perez',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        assert result['mensaje'] == 'Estudiante inscrito exitosamente'
        assert Inscripciones.objects.count() == 1

    def test_enroll_with_tutor(self, setup):
        result = EnrollmentService().enroll_new_student(setup['usuario'], {
            'estudiante': {
                'rude': 'RUD002', 'ci': '87654321',
                'nombres': 'Maria', 'primer_apellido': 'Lopez',
            },
            'tutor': {
                'ci': '11111111', 'nombres': 'Padre',
                'primer_apellido': 'Tutor', 'celular': '77700000',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        assert Tutores.objects.count() == 1

    def test_re_enroll_student(self, setup):
        EnrollmentService().enroll_new_student(setup['usuario'], {
            'estudiante': {
                'rude': 'RUD003', 'ci': '55555555',
                'nombres': 'Test', 'primer_apellido': 'Reinscripcion',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        result = EnrollmentService().re_enroll_existing_student(
            setup['usuario'], 'RUD003', setup['curso'].id
        )
        assert 'reinscrito' in result['mensaje']

    def test_get_catalogs(self, setup):
        catalogs = EnrollmentService().get_enrollment_catalogs(setup['usuario'])
        assert 'grados' in catalogs
        assert 'cursos' in catalogs
        assert len(catalogs['grados']) >= 1

    def test_search_existing_student_found(self, setup):
        EnrollmentService().enroll_new_student(setup['usuario'], {
            'estudiante': {
                'rude': 'RUDSEARCH', 'ci': '99999999',
                'nombres': 'Search', 'primer_apellido': 'Test',
            },
            'curso_id': setup['curso'].id,
            'gestion': 2026,
        })
        result = EnrollmentService().search_existing_student(setup['usuario'], 'RUDSEARCH')
        assert result is not None
        assert result['rude'] == 'RUDSEARCH'

    def test_search_student_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            EnrollmentService().search_existing_student(otro, 'RUD001')

    def test_enroll_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc2', email='doc2@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            EnrollmentService().enroll_new_student(otro, {
                'estudiante': {'rude': 'RUDX'},
                'curso_id': setup['curso'].id,
            })

    def test_enroll_validation(self, setup):
        with pytest.raises(ValueError, match='Debe enviar'):
            EnrollmentService().enroll_new_student(setup['usuario'], {})

    def test_re_enroll_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc3', email='doc3@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            EnrollmentService().re_enroll_existing_student(otro, 'RUDXXX', 1)

    def test_re_enroll_not_found(self, setup):
        with pytest.raises(ValueError, match='no encontrado'):
            EnrollmentService().re_enroll_existing_student(setup['usuario'], 'NOEXIST', 1)

    def test_get_catalogs_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc4', email='doc4@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            EnrollmentService().get_enrollment_catalogs(otro)

    def test_search_tutor_by_ci(self, setup):
        result = EnrollmentService().search_tutor_by_ci(setup['usuario'], 'NOEXIST')
        assert result is None
