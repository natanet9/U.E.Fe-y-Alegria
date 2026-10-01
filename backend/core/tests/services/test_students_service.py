import pytest
from django.contrib.auth.hashers import make_password

from core.models import Estudiantes, Roles, Usuarios, Docentes, Niveles, Grados, Paralelos, Cursos, Areas, DocenteAsignacion, Inscripciones, Tutores, EstudianteTutor
from core.services.students_service import StudentsService


@pytest.mark.django_db
class TestStudentsService:

    @pytest.fixture
    def roles(self):
        return {r.nombre: r for r in Roles.objects.bulk_create([
            Roles(nombre='director'), Roles(nombre='secretaria'), Roles(nombre='docente'),
            Roles(nombre='regente'), Roles(nombre='tutor'),
        ])}

    @pytest.fixture
    def users(self, roles):
        return {
            'secretaria': Usuarios.objects.create(
                nombre='Sec', email='sec@test.com',
                password_hash=make_password('123456'), rol=roles['secretaria'],
            ),
            'docente': Usuarios.objects.create(
                nombre='Doc', email='doc@test.com',
                password_hash=make_password('123456'), rol=roles['docente'],
            ),
            'director': Usuarios.objects.create(
                nombre='Dir', email='dir@test.com',
                password_hash=make_password('123456'), rol=roles['director'],
            ),
            'regente': Usuarios.objects.create(
                nombre='Reg', email='reg@test.com',
                password_hash=make_password('123456'), rol=roles['regente'],
            ),
        }

    def test_crear_estudiante(self, users):
        data = StudentsService().crear(users['secretaria'], {
            'rude': 'RUD001', 'ci': '12345678',
            'nombres': 'Juan', 'primer_apellido': 'Perez',
        })
        assert data['nombres'] == 'Juan'
        assert data['estado'] == 'activo'

    def test_crear_estudiante_docente_fails(self, users):
        with pytest.raises(PermissionError):
            StudentsService().crear(users['docente'], {
                'rude': 'RUD002', 'ci': '87654321',
                'nombres': 'Maria', 'primer_apellido': 'Lopez',
            })

    def test_listar_estudiantes(self, users):
        svc = StudentsService()
        svc.crear(users['secretaria'], {
            'rude': 'RUD001', 'ci': '11111111',
            'nombres': 'Juan', 'primer_apellido': 'A',
        })
        svc.crear(users['secretaria'], {
            'rude': 'RUD002', 'ci': '22222222',
            'nombres': 'Maria', 'primer_apellido': 'B',
        })
        result = svc.listar(users['secretaria'])
        assert result['total'] == 2

    def test_listar_docente_no_permiso(self, users):
        result = StudentsService().listar(users['docente'])
        assert result['total'] == 0

    def test_listar_incluir_inactivos_and_page_bounds(self, users):
        svc = StudentsService()
        activo = svc.crear(users['secretaria'], {
            'rude': 'RUDINA1', 'ci': '88888888',
            'nombres': 'Activo', 'primer_apellido': 'Uno',
            'segundo_apellido': 'Segundo', 'genero': 'M',
            'pais_nacimiento': 'Bolivia', 'tiene_discapacidad': True,
            'tipo_discapacidad': 'Auditiva', 'tiene_tea': False,
            'dificultad_aprendizaje': 'None',
        })
        inactivo = svc.crear(users['secretaria'], {
            'rude': 'RUDINA2', 'ci': '99999998',
            'nombres': 'Inactivo', 'primer_apellido': 'Dos',
        })
        svc.eliminar(users['secretaria'], inactivo['id'])

        solo_activos = svc.listar(users['secretaria'])
        assert solo_activos['total'] == 1
        assert solo_activos['estudiantes'][0]['id'] == activo['id']

        con_inactivos = svc.listar(users['secretaria'], incluir_inactivos=True, page=99, page_size=999)
        assert con_inactivos['total'] == 2
        assert con_inactivos['page'] == 1
        assert con_inactivos['page_size'] == 999
        assert any(item['estado'] == 'inactivo' for item in con_inactivos['estudiantes'])

    def test_buscar_estudiante(self, users):
        svc = StudentsService()
        svc.crear(users['secretaria'], {
            'rude': 'RUDXXX', 'ci': '99999999',
            'nombres': 'Buscar', 'primer_apellido': 'Me',
        })
        result = svc.listar(users['secretaria'], query='Buscar')
        assert result['total'] == 1

    def test_eliminar_estudiante(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDDEL', 'ci': '00000000',
            'nombres': 'Eliminar', 'primer_apellido': 'Me',
        })
        svc.eliminar(users['secretaria'], e['id'])
        estudiante = Estudiantes.objects.get(id=e['id'])
        assert estudiante.estado == 'inactivo'

    def test_restaurar_estudiante(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDRES', 'ci': '10101010',
            'nombres': 'Restaurar', 'primer_apellido': 'Me',
        })
        svc.eliminar(users['secretaria'], e['id'])
        restored = svc.restaurar(users['secretaria'], e['id'])
        assert restored['estado'] == 'activo'

    def test_restaurar_permision(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDRES2', 'ci': '12121212',
            'nombres': 'NoRest', 'primer_apellido': 'Test',
        })
        svc.eliminar(users['secretaria'], e['id'])
        with pytest.raises(PermissionError):
            svc.restaurar(users['docente'], e['id'])

    def test_obtener_estudiante(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDO01', 'ci': '11111111',
            'nombres': 'Obtener', 'primer_apellido': 'Test',
        })
        result = svc.obtener(users['secretaria'], e['id'])
        assert result['nombres'] == 'Obtener'

    def test_obtener_permision(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDO02', 'ci': '22222222',
            'nombres': 'NoPerm', 'primer_apellido': 'Test',
        })
        with pytest.raises(PermissionError):
            svc.obtener(users['docente'], e['id'])

    def test_actualizar_estudiante(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDA01', 'ci': '33333333',
            'nombres': 'Original', 'primer_apellido': 'Test',
        })
        result = svc.actualizar(users['secretaria'], e['id'], {
            'nombres': 'Actualizado',
            'ci': '33333334',
            'rude': 'RUDA02',
            'segundo_apellido': 'Nuevo',
            'fecha_nacimiento': '2026-05-01',
            'genero': 'F',
            'pais_nacimiento': 'Peru',
            'tiene_discapacidad': True,
            'tipo_discapacidad': 'Visual',
            'tiene_tea': True,
            'dificultad_aprendizaje': 'Lectura',
        })
        assert result['nombres'] == 'Actualizado'
        assert result['ci'] == '33333334'
        assert result['rude'] == 'RUDA02'
        assert result['segundo_apellido'] == 'Nuevo'
        assert result['fecha_nacimiento'] == '2026-05-01'
        assert result['genero'] == 'F'
        assert result['pais_nacimiento'] == 'Peru'
        assert result['tiene_discapacidad'] is True
        assert result['tipo_discapacidad'] == 'Visual'
        assert result['tiene_tea'] is True
        assert result['dificultad_aprendizaje'] == 'Lectura'

    def test_actualizar_permision(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDA02', 'ci': '44444444',
            'nombres': 'NoEdit', 'primer_apellido': 'Test',
        })
        with pytest.raises(PermissionError):
            svc.actualizar(users['docente'], e['id'], {'nombres': 'Hack'})

    def test_eliminar_permision(self, users):
        svc = StudentsService()
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDEL2', 'ci': '55555555',
            'nombres': 'NoDel', 'primer_apellido': 'Test',
        })
        with pytest.raises(PermissionError):
            svc.eliminar(users['docente'], e['id'])

    def test_crear_validation(self, users):
        with pytest.raises(ValueError, match='requeridos'):
            StudentsService().crear(users['secretaria'], {})

    def test_crear_validation_formats(self, users):
        svc = StudentsService()
        with pytest.raises(ValueError, match='RUDE'):
            svc.crear(users['secretaria'], {
                'rude': 'bad', 'ci': '12345678', 'nombres': 'X', 'primer_apellido': 'Y',
            })
        with pytest.raises(ValueError, match='CI'):
            svc.crear(users['secretaria'], {
                'rude': 'RUDOK1', 'ci': 'bad', 'nombres': 'X', 'primer_apellido': 'Y',
            })

    def test_validar_data_private(self, users):
        with pytest.raises(ValueError, match='Campos requeridos faltantes'):
            StudentsService()._validar_data({'rude': 'RUD'})

    def test_listar_por_grado(self, users):
        from core.models import Cursos, Grados, Niveles, Paralelos
        from core.services.enrollment_service import EnrollmentService
        svc = StudentsService()
        nivel = Niveles.objects.create(nombre='Test')
        grado = Grados.objects.create(nivel=nivel, nombre='GradoTest', numero=99)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDG01', 'ci': '66666666',
            'nombres': 'Grado', 'primer_apellido': 'Test',
        })
        EnrollmentService().enroll_new_student(users['secretaria'], {
            'estudiante': {'rude': 'RUDG01'},
            'curso_id': curso.id, 'gestion': 2026,
        })
        result = svc.listar(users['secretaria'], grado_id=grado.id)
        assert result['total'] == 1

    def test_listar_docente_con_asignacion(self, users, roles):
        """Test que un docente ve solo los estudiantes de sus cursos."""
        svc = StudentsService()
        
        # Crear estudiante 1
        e1 = svc.crear(users['secretaria'], {
            'rude': 'RUDDS1', 'ci': '77777771',
            'nombres': 'Estudiante', 'primer_apellido': 'Uno',
        })
        
        # Crear estudiante 2
        e2 = svc.crear(users['secretaria'], {
            'rude': 'RUDDS2', 'ci': '77777772',
            'nombres': 'Estudiante', 'primer_apellido': 'Dos',
        })
        
        # Crear estructura académica
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matemáticas')
        
        # Crear docente y asignación
        docente_model = Docentes.objects.create(usuario=users['docente'])
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026
        )
        
        # Inscribir solo e1 en el curso
        Inscripciones.objects.create(
            estudiante_id=e1['id'], curso=curso, gestion=2026, estado='activo'
        )
        
        # El docente debe ver solo e1
        result = svc.listar(users['docente'])
        assert result['total'] == 1
        assert result['estudiantes'][0]['id'] == e1['id']
        
        # El director ve ambos
        result_dir = svc.listar(users['director'])
        assert result_dir['total'] == 2
        
    def test_obtener_estudiante_docente_autorizado(self, users, roles):
        """Test que un docente puede obtener un estudiante de su curso."""
        svc = StudentsService()
        
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDOA1', 'ci': '88888881',
            'nombres': 'Estudiante', 'primer_apellido': 'Autorizado',
        })
        
        # Crear estructura y asignación
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='Primero', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matemáticas')
        docente_model = Docentes.objects.create(usuario=users['docente'])
        da = DocenteAsignacion.objects.create(
            docente=docente_model, curso=curso, area=area, gestion=2026
        )
        Inscripciones.objects.create(
            estudiante_id=e['id'], curso=curso, gestion=2026, estado='activo'
        )
        
        # Debe poder obtenerlo
        result = svc.obtener(users['docente'], e['id'])
        assert result['id'] == e['id']
        
    def test_obtener_estudiante_docente_no_autorizado(self, users, roles):
        """Test que un docente NO puede obtener un estudiante que NO es suyo."""
        svc = StudentsService()
        
        e = svc.crear(users['secretaria'], {
            'rude': 'RUDNO1', 'ci': '99999991',
            'nombres': 'Estudiante', 'primer_apellido': 'NoAutorizado',
        })
        
        # Intentar obtenerlo sin estar autorizado
        with pytest.raises(PermissionError):
            svc.obtener(users['docente'], e['id'])
            
    def test_listar_tutor_ve_solo_sus_hijos(self, users, roles):
        """Test que un tutor ve solo sus hijos."""
        svc = StudentsService()
        
        # Crear estudiantes
        e1 = svc.crear(users['secretaria'], {
            'rude': 'RUDT1', 'ci': '10101010',
            'nombres': 'Hijo', 'primer_apellido': 'Uno',
        })
        e2 = svc.crear(users['secretaria'], {
            'rude': 'RUDT2', 'ci': '20202020',
            'nombres': 'Hijo', 'primer_apellido': 'Dos',
        })
        e3 = svc.crear(users['secretaria'], {
            'rude': 'RUDT3', 'ci': '30303030',
            'nombres': 'NoHijo', 'primer_apellido': 'Tres',
        })
        
        # Crear tutor
        tutor_ci = '40404040'
        tutor = Tutores.objects.create(
            ci=tutor_ci, nombres='Tutor', primer_apellido='Test'
        )
        
        # Asignar e1 y e2 al tutor
        EstudianteTutor.objects.create(estudiante_id=e1['id'], tutor=tutor, activo=True)
        EstudianteTutor.objects.create(estudiante_id=e2['id'], tutor=tutor, activo=True)
        
        # Crear usuario tutor con el mismo CI
        tutor_user = Usuarios.objects.create(
            ci=tutor_ci, nombre='Tutor', primer_apellido='User', email='tutor@test.com',
            password_hash=make_password('123456'), rol=roles['tutor']
        )
        
        # El tutor debe ver solo e1 y e2
        result = svc.listar(tutor_user)
        assert result['total'] == 2
        ids_result = {e['id'] for e in result['estudiantes']}
        assert e1['id'] in ids_result
        assert e2['id'] in ids_result
        assert e3['id'] not in ids_result
