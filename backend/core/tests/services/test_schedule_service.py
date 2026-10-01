import pytest
from django.contrib.auth.hashers import make_password

from core.models import (
    Areas, Cursos, DocenteAsignacion, Docentes, Grados, Horarios, Niveles, Paralelos,
    Roles, Usuarios,
)
from core.services.schedule_service import ScheduleService


@pytest.mark.django_db
class TestScheduleService:

    @pytest.fixture
    def setup(self):
        roles = {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
        ])}
        secretaria = Usuarios.objects.create(
            nombre='Sec', email='sec@test.com',
            password_hash=make_password('123456'), rol=roles['secretaria'],
        )
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Geografia')
        docente_model = Docentes.objects.create(usuario=secretaria)
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026,
        )
        return {'secretaria': secretaria, 'da': da, 'curso': curso}

    def test_listar_horarios(self, setup):
        result = ScheduleService().listar_horarios(setup['secretaria'], curso_id=setup['curso'].id)
        assert result == []

    def test_crear_horario(self, setup):
        result = ScheduleService().guardar_horario(setup['secretaria'], {
            'docente_asignacion_id': setup['da'].id,
            'dia_semana': 1,
            'hora_inicio': '08:00',
            'hora_fin': '09:30',
            'aula': 'A101',
        })
        assert Horarios.objects.count() == 1
        h = Horarios.objects.first()
        assert h.dia_semana == 1

    def test_eliminar_horario(self, setup):
        h = Horarios.objects.create(
            docente_asignacion=setup['da'], dia_semana=1,
            hora_inicio='08:00', hora_fin='09:30', aula='A101',
        )
        ScheduleService().eliminar_horario(setup['secretaria'], h.id)
        h.refresh_from_db()
        assert h.activo is False

    def test_listar_horarios_por_grado(self, setup):
        result = ScheduleService().listar_horarios(setup['secretaria'], grado_id=setup['da'].curso.grado_id)
        assert isinstance(result, list)

    def test_listar_horarios_docente(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc', email='doc@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        docente_model2 = Docentes.objects.create(usuario=otro)
        area2 = Areas.objects.create(nombre='Historia')
        da2 = DocenteAsignacion.objects.create(
            docente=docente_model2, curso=setup['da'].curso, area=area2, gestion=2026,
        )
        Horarios.objects.create(
            docente_asignacion=da2, dia_semana=1,
            hora_inicio='08:00', hora_fin='09:30', aula='B202',
        )
        result = ScheduleService().listar_horarios(otro)
        assert len(result) >= 1

    def test_listar_horarios_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Otro', email='otro@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        result = ScheduleService().listar_horarios(otro)
        assert result == []

    def test_guardar_horario_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc2', email='doc2@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            ScheduleService().guardar_horario(otro, {})

    def test_guardar_horario_validation(self, setup):
        with pytest.raises(ValueError, match='Campos requeridos faltantes'):
            ScheduleService().guardar_horario(setup['secretaria'], {})

    def test_eliminar_horario_permision(self, setup):
        otro_rol = Roles.objects.get(nombre='docente')
        otro = Usuarios.objects.create(
            nombre='Doc3', email='doc3@test.com',
            password_hash=make_password('123456'), rol=otro_rol,
        )
        with pytest.raises(PermissionError):
            ScheduleService().eliminar_horario(otro, 1)
