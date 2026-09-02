from datetime import date, time, timedelta
from random import choice, randint, random

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from core.models import (
    Actividades, ActividadNotas, Areas, Asistencias,
    ConfiguracionEscuela, Cursos, DimensionConfigPeriodo,
    DimensionesEvaluacion, DocenteAsignacion, Docentes,
    Estudiantes, EstudianteTutor, Grados, Horarios,
    Inscripciones, Niveles, NotaObservaciones,
    Paralelos, Periodos,
    Roles, Tutores, Usuarios,
)

GENERO = ('M', 'F')
NOMBRES_M = ('Carlos', 'Luis', 'Jorge', 'Miguel', 'Diego', 'Pablo', 'Andres', 'Santiago', 'Mateo', 'Gabriel')
NOMBRES_F = ('Maria', 'Ana', 'Sofia', 'Valentina', 'Camila', 'Isabella', 'Luciana', 'Ximena', 'Fernanda', 'Daniela')
APELLIDOS = ('Quispe', 'Mamani', 'Flores', 'Condori', 'Morales', 'Garcia', 'Lopez', 'Rodriguez', 'Martinez', 'Perez',
             'Vargas', 'Rojas', 'Torrez', 'Gutierrez', 'Alvarez', 'Romero', 'Cruz', 'Diaz', 'Castro', 'Ortiz')


class Command(BaseCommand):
    help = 'Crea un unico curso demo completo con 20 estudiantes, 4 docentes, actividades, notas, asistencias, etc.'

    def handle(self, *args, **options):
        self._limpiar_datos()
        self._seed_roles()
        self._seed_niveles()
        self._seed_grados()
        self._seed_paralelos()
        self._seed_cursos()
        self._seed_areas()
        self._seed_configuracion()
        self._seed_dimensiones()
        self._seed_usuarios()
        self._seed_docentes()
        self._seed_periodos()
        self._seed_dimension_config()
        self._seed_estudiantes()
        self._seed_tutores()
        self._seed_estudiante_tutor()
        self._seed_inscripciones()
        self._seed_docente_asignaciones()
        self._seed_actividades()
        self._seed_notas()
        self._seed_asistencias()
        self._seed_horarios()
        self._seed_nota_observaciones()
        self.stdout.write(self.style.SUCCESS('Demo curso completado exitosamente'))

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _rand_estado_asistencia(self):
        r = random()
        if r < 0.7:
            return 'presente'
        if r < 0.85:
            return 'ausente'
        return 'con_licencia'

    def _rand_nota(self, max_val=100):
        return round(random() * max_val, 2)

    # ------------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------------
    def _limpiar_datos(self):
        models = [
            NotaObservaciones, ActividadNotas, Actividades,
            Horarios, Asistencias, PeriodoCierreDocente := None,
            DocenteAsignacion, Inscripciones, EstudianteTutor, Estudiantes, Tutores,
            Docentes, Usuarios, Periodos, DimensionConfigPeriodo, DimensionesEvaluacion,
            Cursos, Grados, Niveles, Paralelos, Areas, Roles,
        ]
        # Delete in reverse FK order
        self.stdout.write('Limpiando datos existentes...')
        # Import here to avoid top-level import issues
        from core.models import PeriodoCierreDocente as PCD
        PCD.objects.all().delete()
        NotaObservaciones.objects.all().delete()
        ActividadNotas.objects.all().delete()
        Actividades.objects.all().delete()
        Horarios.objects.all().delete()
        Asistencias.objects.all().delete()
        DocenteAsignacion.objects.all().delete()
        Inscripciones.objects.all().delete()
        EstudianteTutor.objects.all().delete()
        Estudiantes.objects.all().delete()
        Tutores.objects.all().delete()
        Docentes.objects.all().delete()
        Usuarios.objects.exclude(email__in=('director@uepanama.com', 'secretaria@uepanama.com', 'regente@uepanama.com')).delete()
        Periodos.objects.all().delete()
        DimensionConfigPeriodo.objects.all().delete()
        DimensionesEvaluacion.objects.all().delete()
        Cursos.objects.all().delete()
        Grados.objects.all().delete()
        Niveles.objects.all().delete()
        Paralelos.objects.all().delete()
        Areas.objects.all().delete()
        Roles.objects.all().delete()
        self.stdout.write('  datos limpiados OK')

    # ------------------------------------------------------------------
    # SEED STEPS
    # ------------------------------------------------------------------
    def _seed_roles(self):
        for name in ('director', 'secretaria', 'docente', 'regente', 'tutor'):
            Roles.objects.create(nombre=name)
        self.stdout.write('  roles OK')

    def _seed_niveles(self):
        self.nivel = Niveles.objects.create(nombre='Secundaria')
        self.stdout.write('  niveles OK')

    def _seed_grados(self):
        self.grado_primero = Grados.objects.create(nivel=self.nivel, nombre='Primero de Secundaria', numero=1)
        self.grado_segundo = Grados.objects.create(nivel=self.nivel, nombre='Segundo de Secundaria', numero=2)
        self.stdout.write('  grados OK')

    def _seed_paralelos(self):
        self.paralelo_a = Paralelos.objects.create(nombre='A')
        self.stdout.write('  paralelos OK')

    def _seed_cursos(self):
        # Historical course (for promoted students)
        self.curso_primero = Cursos.objects.create(grado=self.grado_primero, paralelo=self.paralelo_a, gestion=2025)
        # Active course
        self.curso_segundo = Cursos.objects.create(grado=self.grado_segundo, paralelo=self.paralelo_a, gestion=2026)
        self.stdout.write('  cursos OK')

    def _seed_areas(self):
        self.areas_data = [
            'Matematicas', 'Lenguaje y Comunicacion', 'Ciencias Sociales',
            'Ciencias Naturales', 'Educacion Fisica', 'Artes Plasticas',
            'Informatica', 'Electricidad', 'Mecanica',
        ]
        self.areas = {}
        for name in self.areas_data:
            a = Areas.objects.create(nombre=name)
            self.areas[name] = a
        self.stdout.write('  areas OK')

    def _seed_configuracion(self):
        ConfiguracionEscuela.objects.all().delete()
        ConfiguracionEscuela.objects.create(
            nombre='Unidad Educativa Panama',
            direccion='Av. Principal #123',
            telefono='291-12345',
            email='uepanama@educacion.bo',
            ciudad='El Alto',
            gestion_actual=2026,
            escala_aprobacion=51.00,
        )
        self.stdout.write('  configuracion OK')

    def _seed_dimensiones(self):
        self.dims = {}
        for name, order in (('SER', 1), ('SABER', 2), ('HACER', 3), ('AUTOEVALUACION', 4)):
            d = DimensionesEvaluacion.objects.create(nombre=name, orden=order, gestion=2026)
            self.dims[name] = d
        self.stdout.write('  dimensiones OK')

    def _seed_usuarios(self):
        rol_map = {r.nombre: r for r in Roles.objects.all()}
        pw = make_password('123456')

        data = [
            ('director@uepanama.com', 'Carlos Mendoza', 'director', '12345601'),
            ('secretaria@uepanama.com', 'Ana Rojas', 'secretaria', '12345602'),
            ('regente@uepanama.com', 'Laura Vargas', 'regente', '12345603'),
            ('docente1@uepanama.com', 'Pedro Garcia', 'docente', '12345604'),
            ('docente2@uepanama.com', 'Rosa Quispe', 'docente', '12345605'),
            ('docente3@uepanama.com', 'Mario Lopez', 'docente', '12345606'),
            ('docente4@uepanama.com', 'Elena Condori', 'docente', '12345607'),
        ]
        self.usuarios = {}
        for email, nombre, rol_name, ci in data:
            u = Usuarios.objects.create(
                email=email, nombre_completo=nombre,
                password_hash=pw, rol=rol_map[rol_name],
                ci=ci, activo=True,
            )
            self.usuarios[rol_name] = u
        # Director + Secretaria + Regente kept from original; store aliases
        self.usuarios['director'] = Usuarios.objects.get(email='director@uepanama.com')
        self.usuarios['secretaria'] = Usuarios.objects.get(email='secretaria@uepanama.com')
        self.usuarios['regente'] = Usuarios.objects.get(email='regente@uepanama.com')
        self.stdout.write('  usuarios OK')

    def _seed_docentes(self):
        self.docentes = {}
        docente_role = Roles.objects.get(nombre='docente')
        for key, email in (('general', 'docente1@uepanama.com'),
                           ('tecnico1', 'docente2@uepanama.com'),
                           ('tecnico2', 'docente3@uepanama.com'),
                           ('tecnico3', 'docente4@uepanama.com')):
            usr = Usuarios.objects.get(email=email)
            d, _ = Docentes.objects.get_or_create(usuario=usr)
            self.docentes[key] = d
        self.stdout.write('  docentes OK')

    def _seed_periodos(self):
        director = self.usuarios['director']
        self.periodos = {}
        for gestion in (2025, 2026):
            Periodos.objects.filter(gestion=gestion, estado='activo').update(
                estado='pendiente', habilitado_por=None, habilitado_en=None)
            for num, nombre in enumerate(('Primer Trimestre', 'Segundo Trimestre', 'Tercer Trimestre'), start=1):
                fecha_ini = date(gestion, (num - 1) * 4 + 1, 1)
                fecha_fin = date(gestion, min(num * 4, 12), 28)
                # Only Primer Trimestre 2026 is active
                estado = 'activo' if (gestion == 2026 and num == 1) else 'pendiente'
                p, _ = Periodos.objects.update_or_create(
                    numero=num, gestion=gestion,
                    defaults={
                        'nombre': nombre,
                        'fecha_inicio': fecha_ini,
                        'fecha_fin': fecha_fin,
                        'estado': estado,
                        'habilitado_por': director if estado == 'activo' else None,
                    },
                )
                self.periodos[(gestion, num)] = p
        self.active_periodo = self.periodos[(2026, 1)]
        self.stdout.write('  periodos OK')

    def _seed_dimension_config(self):
        puntajes = {'SER': 5, 'SABER': 45, 'HACER': 40, 'AUTOEVALUACION': 5}
        for p in Periodos.objects.filter(gestion=2026):
            for dim_nombre, puntaje in puntajes.items():
                dim = self.dims[dim_nombre]
                DimensionConfigPeriodo.objects.create(
                    periodo=p, dimension=dim, puntaje_maximo=puntaje,
                )
        self.stdout.write('  dimension_config OK')

    def _seed_estudiantes(self):
        self.estudiantes = []
        for i in range(1, 21):
            gen = GENERO[i % 2]
            nombres_pool = NOMBRES_F if gen == 'F' else NOMBRES_M
            nombres = f'{choice(nombres_pool)} {choice(nombres_pool)}'
            apellido = f'{choice(APELLIDOS)} {choice(APELLIDOS)}'
            e = Estudiantes.objects.create(
                rude=f'RUD{i:05d}',
                ci=f'100000{i:02d}',
                nombres=nombres,
                primer_apellido=apellido.split()[0],
                segundo_apellido=apellido.split()[1] if len(apellido.split()) > 1 else '',
                genero=gen,
                fecha_nacimiento=date(2008 + randint(0, 2), randint(1, 12), randint(1, 28)),
                estado='activo',
            )
            self.estudiantes.append(e)
        self.stdout.write('  estudiantes OK')

    def _seed_tutores(self):
        self.tutores = []
        for i in range(1, 21):
            t = Tutores.objects.create(
                ci=f'7000000{i:02d}',
                nombres=choice(NOMBRES_M if i % 2 == 0 else NOMBRES_F),
                primer_apellido=choice(APELLIDOS),
                celular=f'777{i:05d}',
                parentesco=choice(('Padre', 'Madre', 'Tio', 'Abuelo')),
            )
            self.tutores.append(t)
        self.stdout.write('  tutores OK')

    def _seed_estudiante_tutor(self):
        # Each student gets 2 tutors
        for idx, e in enumerate(self.estudiantes):
            t1 = self.tutores[idx]
            t2 = self.tutores[(idx + 1) % len(self.tutores)]
            EstudianteTutor.objects.create(estudiante=e, tutor=t1, es_principal=True)
            if t2 != t1:
                EstudianteTutor.objects.create(estudiante=e, tutor=t2, es_principal=False)
        self.stdout.write('  estudiante_tutor OK')

    def _seed_inscripciones(self):
        # First 18 students were in Primero 2025 (promoted)
        for e in self.estudiantes[:18]:
            Inscripciones.objects.create(estudiante=e, curso=self.curso_primero, gestion=2025, estado='activo')
        # All 20 students are in Segundo 2026
        for e in self.estudiantes:
            Inscripciones.objects.create(estudiante=e, curso=self.curso_segundo, gestion=2026, estado='activo')
        self.stdout.write('  inscripciones OK')

    def _seed_docente_asignaciones(self):
        # Teacher 1 (general): all academic subjects
        general_areas = ['Matematicas', 'Lenguaje y Comunicacion', 'Ciencias Sociales',
                         'Ciencias Naturales', 'Educacion Fisica', 'Artes Plasticas']
        technical_map = {'Informatica': 'tecnico1', 'Electricidad': 'tecnico2', 'Mecanica': 'tecnico3'}

        self.asignaciones = []
        for area_name in general_areas:
            da = DocenteAsignacion.objects.create(
                docente=self.docentes['general'],
                curso=self.curso_segundo,
                area=self.areas[area_name],
                gestion=2026,
            )
            self.asignaciones.append(da)

        for area_name, doc_key in technical_map.items():
            da = DocenteAsignacion.objects.create(
                docente=self.docentes[doc_key],
                curso=self.curso_segundo,
                area=self.areas[area_name],
                gestion=2026,
            )
            self.asignaciones.append(da)

        self.stdout.write('  docente_asignaciones OK')

    def _seed_actividades(self):
        self.actividades = []
        periodos_2026 = [p for key, p in self.periodos.items() if key[0] == 2026]
        for da in self.asignaciones:
            for periodo in periodos_2026:
                for dim_name, dim_obj in self.dims.items():
                    dc = DimensionConfigPeriodo.objects.get(
                        periodo=periodo, dimension=dim_obj)
                    month = periodo.numero * 4 - 2  # ~Feb, Jun, Oct
                    act = Actividades.objects.create(
                        docente_asignacion=da,
                        periodo=periodo,
                        dimension=dim_obj,
                        nombre=f'{da.area.nombre} - {dim_name} ({periodo.nombre})',
                        descripcion=f'Actividad de {da.area.nombre} - Dimension {dim_name}',
                        puntaje_maximo=dc.puntaje_maximo,
                        fecha_actividad=date(2026, min(month, 12), randint(1, 25)),
                    )
                    self.actividades.append(act)
        self.stdout.write(f'  actividades OK ({len(self.actividades)} creadas)')

    def _seed_notas(self):
        count = 0
        for act in self.actividades:
            for e in self.estudiantes:
                # Random grade within puntaje_maximo
                max_val = float(act.puntaje_maximo)
                valor = self._rand_nota(max_val)
                ActividadNotas.objects.create(
                    actividad=act, estudiante=e, valor=valor,
                )
                count += 1
        self.stdout.write(f'  notas OK ({count} registradas)')

    def _seed_asistencias(self):
        # Generate 90 days of attendance per student (approx 1 trimester)
        start_date = date(2026, 2, 1)
        regente = self.usuarios['regente']
        count = 0
        for da in self.asignaciones:
            for e in self.estudiantes:
                for day_offset in range(90):
                    d = start_date + timedelta(days=day_offset)
                    # Skip weekends
                    if d.weekday() >= 5:
                        continue
                    estado = self._rand_estado_asistencia()
                    Asistencias.objects.create(
                        estudiante=e, docente_asignacion=da,
                        fecha=d, estado=estado, tipo='por_asignacion',
                        registrado_por=regente,
                    )
                    count += 1
        self.stdout.write(f'  asistencias OK ({count} registradas)')

    def _seed_horarios(self):
        dias = {1: 'Lunes', 2: 'Martes', 3: 'Miercoles', 4: 'Jueves', 5: 'Viernes'}
        slots = [
            (time(8, 0), time(8, 45)),
            (time(8, 45), time(9, 30)),
            (time(9, 45), time(10, 30)),
            (time(10, 30), time(11, 15)),
            (time(11, 15), time(12, 0)),
        ]
        count = 0
        for da in self.asignaciones:
            for dia in (1, 3):  # Monday and Wednesday
                hora_ini, hora_fin = choice(slots)
                Horarios.objects.create(
                    docente_asignacion=da,
                    dia_semana=dia,
                    hora_inicio=hora_ini,
                    hora_fin=hora_fin,
                    aula=choice(('101', '102', '103', 'Lab A', 'Lab B', 'Taller')),
                )
                count += 1
        self.stdout.write(f'  horarios OK ({count} creados)')

    def _seed_nota_observaciones(self):
        for e in self.estudiantes[:5]:  # Only 5 students get nota-observations
            for da in self.asignaciones[:2]:  # Only first 2 asignaciones
                NotaObservaciones.objects.create(
                    estudiante=e,
                    docente_asignacion=da,
                    periodo=self.periodos[(2026, 1)],
                    indicador=choice(('PA', 'SA', 'A', 'EA')),
                    observacion=f'Observacion de nota para {e.nombres} en {da.area.nombre}',
                )
        self.stdout.write('  nota_observaciones OK')
