import pytest
from django.contrib.auth.hashers import make_password

from core.models import Areas, Cursos, DocenteAsignacion, Docentes, Estudiantes, Grados, Inscripciones, Niveles, Paralelos, Roles, Usuarios, Tutores, EstudianteTutor
from core.services.access_service import AccessControlService


@pytest.mark.django_db
class TestAccessControlService:

    @pytest.fixture
    def roles(self):
        return {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
            Roles(nombre='regente'), Roles(nombre='tutor'),
        ])}

    def _make_user(self, roles, rol_name, ci=None):
        return Usuarios.objects.create(
            ci=ci,
            nombre='User',
            email=f'{rol_name}@test.com',
            password_hash=make_password('123456'),
            rol=roles[rol_name],
        )

    def test_director_permissions(self, roles):
        u = self._make_user(roles, 'director')
        ac = AccessControlService()
        assert ac.es_director(u)
        assert ac.puede_ver_todo(u)
        assert ac.puede_habilitar_periodo(u)
        assert ac.puede_ver_auditoria(u)
        assert ac.puede_exportar(u)
        assert ac.puede_cerrar_periodo(u)

    def test_secretaria_permissions(self, roles):
        u = self._make_user(roles, 'secretaria')
        ac = AccessControlService()
        assert ac.es_secretaria(u)
        assert ac.puede_ver_todo(u)
        assert ac.puede_cerrar_periodo(u)
        assert ac.puede_gestionar_inscripciones(u)
        assert ac.puede_gestionar_usuarios(u)
        assert not ac.puede_habilitar_periodo(u)

    def test_docente_permissions(self, roles):
        u = self._make_user(roles, 'docente')
        ac = AccessControlService()
        assert ac.es_docente(u)
        assert not ac.puede_ver_todo(u)
        assert not ac.puede_cerrar_periodo(u)
        assert not ac.puede_gestionar_usuarios(u)
        assert ac.puede_exportar(u)

    def test_regente_permissions(self, roles):
        u = self._make_user(roles, 'regente')
        ac = AccessControlService()
        assert ac.es_regente(u)
        assert ac.puede_ver_todo(u)
        assert ac.puede_gestionar_licencias(u)
        assert ac.puede_aprobar_licencia_directa(u, 3)
        assert not ac.puede_aprobar_licencia_directa(u, 4)

    def test_tutor_permissions(self, roles):
        u = self._make_user(roles, 'tutor')
        ac = AccessControlService()
        assert ac.es_tutor(u)
        assert not ac.puede_ver_todo(u)
        assert not ac.puede_gestionar_licencias(u)
        assert not ac.puede_exportar(u)

    def test_is_admin(self, roles):
        ac = AccessControlService()
        assert ac.es_admin(self._make_user(roles, 'director'))
        assert ac.es_admin(self._make_user(roles, 'secretaria'))
        assert not ac.es_admin(self._make_user(roles, 'docente'))

    def test_none_user(self):
        ac = AccessControlService()
        assert ac.get_role_name(None) is None
        assert not ac.puede_ver_todo(None)

    def test_docente_asignado_and_relations(self, roles):
        docente = self._make_user(roles, 'docente')
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Ciencias')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(docente=docente_model, curso=curso, area=area, gestion=2026)
        estudiante = Estudiantes.objects.create(rude='RUD002', ci='12345679', nombres='Ana', primer_apellido='Lopez')
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)

        ac = AccessControlService()
        assert ac.puede_editar_notas(docente, da.id)
        assert ac.get_cursos_asignados(docente) == [curso.id]
        assert list(ac.get_asignaciones_docente(docente)) == [da]
        assert ac.get_estudiantes_ids_por_asignacion(da.id) == [estudiante.id]

    def test_docente_no_asignado_cannot_edit_specific_assignment(self, roles):
        docente = self._make_user(roles, 'docente')
        other = self._make_user(roles, 'secretaria')
        nivel = Niveles.objects.create(nombre='Secundaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Segundo', numero=2)
        paralelo = Paralelos.objects.create(nombre='B')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Historia')
        docente_model2 = Docentes.objects.create(usuario=other)
        DocenteAsignacion.objects.create(docente=docente_model2, curso=curso, area=area, gestion=2026)

        ac = AccessControlService()
        assert ac.puede_editar_notas(docente, 99999) is False
        assert ac.puede_editar_notas(docente) is True
        
    def test_get_estudiantes_ids_docente(self, roles):
        """Test que obtiene los estudiantes de un docente."""
        docente = self._make_user(roles, 'docente')
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Ciencias')
        docente_model = Docentes.objects.create(usuario=docente)
        da = DocenteAsignacion.objects.create(docente=docente_model, curso=curso, area=area, gestion=2026)
        estudiante = Estudiantes.objects.create(rude='RUD003', ci='12345680', nombres='Luis', primer_apellido='Gomez')
        Inscripciones.objects.create(estudiante=estudiante, curso=curso, gestion=2026)
        
        ac = AccessControlService()
        ids = ac.get_estudiantes_ids_docente(docente)
        assert ids == [estudiante.id]
        
    def test_get_estudiantes_ids_tutor(self, roles):
        """Test que obtiene los estudiantes de un tutor."""
        tutor_ci = '12345678'
        tutor_user = self._make_user(roles, 'tutor', ci=tutor_ci)
        tutor = Tutores.objects.create(ci=tutor_ci, nombres='Tutor', primer_apellido='Test')
        estudiante = Estudiantes.objects.create(rude='RUD004', ci='87654321', nombres='Hijo', primer_apellido='Test')
        EstudianteTutor.objects.create(estudiante=estudiante, tutor=tutor, activo=True)
        
        ac = AccessControlService()
        ids = ac.get_estudiantes_ids_tutor(tutor_user)
        assert ids == [estudiante.id]
        
    def test_get_estudiantes_autorizados(self, roles):
        """Test que devuelve los estudiantes autorizados según el rol."""
        director = self._make_user(roles, 'director')
        docente = self._make_user(roles, 'docente')
        tutor_ci = '11112222'
        tutor = self._make_user(roles, 'tutor', ci=tutor_ci)
        
        ac = AccessControlService()
        
        # Director ve todos (None)
        assert ac.get_estudiantes_autorizados(director) is None
        
        # Docente sin asignaciones ve []
        assert ac.get_estudiantes_autorizados(docente) == []
        
        # Tutor sin relación ve []
        assert ac.get_estudiantes_autorizados(tutor) == []
