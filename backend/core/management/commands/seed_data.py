from datetime import date, timedelta
from decimal import Decimal
from random import choice, randint, seed as random_seed

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from core.models import (
    Actividades, ActividadNotas, Areas, Asistencias, Cursos,
    DimensionConfigPeriodo, DimensionesEvaluacion, DocenteAsignacion,
    Docentes, Estudiantes, EstudianteTutor, Grados, Inscripciones,
    Niveles, Paralelos, Periodos, PeriodoCierreDocente, Roles, Tutores, Usuarios,
    NotaObservaciones, Licencias, Horarios,
)


class Command(BaseCommand):
    help = 'Siembra datos demo: 1 curso, 20 estudiantes, 4 docentes'

    def handle(self, *args, **options):
        random_seed(42)
        self._clear_all()
        self._seed_roles()
        self._seed_niveles()
        self._seed_grados()
        self._seed_paralelos()
        self._seed_areas()
        self._seed_dimensiones()
        self._seed_usuarios()
        self._seed_cursos()
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
        self.stdout.write(self.style.SUCCESS('Seed completado'))

    def _clear_all(self):
        models = [
            ActividadNotas, NotaObservaciones, Asistencias, Horarios,
            Actividades, Licencias, EstudianteTutor, Inscripciones,
            DocenteAsignacion, PeriodoCierreDocente, DimensionConfigPeriodo, Periodos,
            Docentes, Cursos, Grados, Estudiantes, Tutores,
            Niveles, Paralelos, Areas, DimensionesEvaluacion,
            Usuarios, Roles,
        ]
        for model in models:
            model.objects.all().delete()
        self.stdout.write('  datos anteriores eliminados')

    def _seed_roles(self):
        for name in ('director', 'secretaria', 'docente', 'regente', 'tutor'):
            Roles.objects.create(nombre=name)
        self.stdout.write('  roles OK')

    def _seed_niveles(self):
        Niveles.objects.create(nombre='Primario')
        self.stdout.write('  niveles OK')

    def _seed_grados(self):
        nivel = Niveles.objects.get(nombre='Primario')
        Grados.objects.create(nivel=nivel, nombre='Primero de Primaria', numero=1)
        self.stdout.write('  grados OK')

    def _seed_paralelos(self):
        Paralelos.objects.create(nombre='A')
        self.stdout.write('  paralelos OK')

    def _seed_areas(self):
        for name in (
            'Matematicas', 'Lenguaje y Comunicacion', 'Ciencias Sociales',
            'Ciencias Naturales', 'Artes Plasticas', 'Educacion Fisica',
            'Tecnica Tecnologica', 'Educacion Musical',
            'Valores,Ecspiritualidad y Religiones',
        ):
            Areas.objects.create(nombre=name)
        self.stdout.write('  areas OK')

    def _seed_dimensiones(self):
        for name, order in (('SER', 1), ('SABER', 2), ('HACER', 3), ('AUTOEVALUACION', 4)):
            DimensionesEvaluacion.objects.create(nombre=name, gestion=2026, orden=order)
        self.stdout.write('  dimensiones OK')

    def _seed_usuarios(self):
        data = [
            ('director@uepanama.com', 'Carlos Mendoza', 'director'),
            ('secretaria@uepanama.com', 'Ana Rojas', 'secretaria'),
            ('regente@uepanama.com', 'Laura Vargas', 'regente'),
            ('docente1@uepanama.com', 'Roberto Vargas', 'docente'),
            ('docente2@uepanama.com', 'Carlos Jimenez', 'docente'),
            ('docente3@uepanama.com', 'Maria Gutierrez', 'docente'),
            ('docente4@uepanama.com', 'Jose Fernandez', 'docente'),
            ('docente5@uepanama.com', 'Andrea Morales', 'docente'),
            ('docente6@uepanama.com', 'Fernando Quispe', 'docente'),
        ]
        rol_map = {r.nombre: r for r in Roles.objects.all()}
        for email, full_name, rol_name in data:
            parts = full_name.split(' ', 1)
            Usuarios.objects.create(
                email=email,
                nombre=parts[0],
                primer_apellido=parts[1] if len(parts) > 1 else '',
                password_hash=make_password('123456'),
                rol=rol_map[rol_name],
                activo=True,
            )
        self.stdout.write('  usuarios OK')

    def _seed_cursos(self):
        grado = Grados.objects.get(nombre='Primero de Primaria')
        paralelo = Paralelos.objects.get(nombre='A')
        Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        self.stdout.write('  cursos OK')

    def _seed_docentes(self):
        for email in ('docente1@uepanama.com', 'docente2@uepanama.com',
                      'docente3@uepanama.com', 'docente4@uepanama.com',
                      'docente5@uepanama.com', 'docente6@uepanama.com'):
            usuario = Usuarios.objects.get(email=email)
            Docentes.objects.create(usuario=usuario)
        self.stdout.write('  docentes OK')

    def _seed_periodos(self):
        director = Usuarios.objects.get(email='director@uepanama.com')
        for num, trimestre in enumerate(('Primer Trimestre', 'Segundo Trimestre'), start=1):
            fecha_ini = date(2026, (num - 1) * 4 + 1, 1)
            fecha_fin = date(2026, min((num * 4), 12), 28)
            estado = 'activo' if num == 1 else 'pendiente'
            Periodos.objects.create(
                nombre=trimestre,
                numero=num,
                gestion=2026,
                fecha_inicio=fecha_ini,
                fecha_fin=fecha_fin,
                estado=estado,
                habilitado_por=director if estado == 'activo' else None,
            )
        self.stdout.write('  periodos OK')

    def _seed_dimension_config(self):
        puntajes = {'SER': 10, 'SABER': 45, 'HACER': 40, 'AUTOEVALUACION': 5}
        for periodo in Periodos.objects.filter(gestion=2026):
            for dim_nombre, puntaje in puntajes.items():
                dim = DimensionesEvaluacion.objects.get(nombre=dim_nombre, gestion=2026)
                DimensionConfigPeriodo.objects.create(
                    periodo=periodo,
                    dimension=dim,
                    puntaje_maximo=puntaje,
                )
        self.stdout.write('  dimension_config OK')

    def _seed_estudiantes(self):
        apellidos = ['Quispe', 'Mamani', 'Flores', 'Condori', 'Choque',
                     'Huanca', 'Paco', 'Vargas', 'Morales', 'Ramos',
                     'Gutierrez', 'Torrez', 'Zeballos', 'Cruz', 'Paredes',
                     'Rojas', 'Mendoza', 'Cardenas', 'Loza', 'Aguilar']
        generos = ['M', 'F']
        for i in range(1, 21):
            genero = generos[i % 2]
            ci = f'100000{i:02d}'
            is_new = i > 18
            Estudiantes.objects.create(
                ci=ci,
                rude=f'RUD2026{i:03d}',
                nombres=f'Estudiante{"M" if genero == "M" else "F"}{i}',
                primer_apellido=apellidos[i - 1],
                genero=genero,
                fecha_nacimiento=date(2014 + choice([0, 1, 2]), randint(1, 12), randint(1, 28)),
                estado='nuevo' if is_new else 'activo',
            )
        self.stdout.write('  estudiantes OK')

    def _seed_tutores(self):
        data = [
            ('1111111', 'Juan', 'Quispe', '77760001'),
            ('1111112', 'Rosa', 'Mamani', '77760002'),
            ('1111113', 'Luis', 'Flores', '77760003'),
            ('1111114', 'Eva', 'Condori', '77760004'),
            ('1111115', 'Oscar', 'Choque', '77760005'),
            ('1111116', 'Carla', 'Huanca', '77760006'),
            ('1111117', 'Pedro', 'Paco', '77760007'),
            ('1111118', 'Sonia', 'Vargas', '77760008'),
            ('1111119', 'Miguel', 'Morales', '77760009'),
            ('1111120', 'Diana', 'Ramos', '77760010'),
            ('1111121', 'Luis', 'Gutierrez', '77760011'),
            ('1111122', 'Maria', 'Torrez', '77760012'),
        ]
        for ci, nombres, apellido, celular in data:
            Tutores.objects.create(
                ci=ci,
                nombres=nombres,
                primer_apellido=apellido,
                celular=celular,
            )
        self.stdout.write('  tutores OK')

    def _seed_estudiante_tutor(self):
        tutores = list(Tutores.objects.all())
        for i, estudiante in enumerate(Estudiantes.objects.all()):
            tutor = tutores[i % len(tutores)]
            EstudianteTutor.objects.create(
                estudiante=estudiante,
                tutor=tutor,
                es_principal=True,
            )
        self.stdout.write('  estudiante_tutor OK')

    def _seed_inscripciones(self):
        curso = Cursos.objects.get(grado__nombre='Primero de Primaria', gestion=2026)
        for estudiante in Estudiantes.objects.all():
            Inscripciones.objects.create(
                estudiante=estudiante,
                curso=curso,
                gestion=2026,
                estado='activo',
            )
        self.stdout.write('  inscripciones OK')

    def _seed_docente_asignaciones(self):
        areas = {a.nombre: a for a in Areas.objects.all()}
        curso = Cursos.objects.get(grado__nombre='Primero de Primaria', gestion=2026)
        docente1 = Docentes.objects.get(usuario__email='docente1@uepanama.com')
        docente2 = Docentes.objects.get(usuario__email='docente2@uepanama.com')
        docente3 = Docentes.objects.get(usuario__email='docente3@uepanama.com')
        docente4 = Docentes.objects.get(usuario__email='docente4@uepanama.com')
        docente5 = Docentes.objects.get(usuario__email='docente5@uepanama.com')
        docente6 = Docentes.objects.get(usuario__email='docente6@uepanama.com')

        general_areas = ['Matematicas', 'Lenguaje y Comunicacion', 'Ciencias Sociales',
                         'Ciencias Naturales', 'Artes Plasticas', 'Educacion Fisica']

        for area_nombre in general_areas:
            DocenteAsignacion.objects.create(
                docente=docente1,
                curso=curso,
                area=areas[area_nombre],
                gestion=2026,
            )

        for docente in (docente2, docente3, docente4):
            DocenteAsignacion.objects.get_or_create(
                curso=curso,
                area=areas['Tecnica Tecnologica'],
                gestion=2026,
                defaults={'docente': docente},
            )

        DocenteAsignacion.objects.get_or_create(
            docente=docente5,
            curso=curso,
            area=areas['Educacion Musical'],
            gestion=2026,
        )
        DocenteAsignacion.objects.get_or_create(
            docente=docente6,
            curso=curso,
            area=areas['Valores,Ecspiritualidad y Religiones'],
            gestion=2026,
        )
        self.stdout.write('  docente_asignaciones OK')

    def _seed_actividades(self):
        areas_db = {a.nombre: a for a in Areas.objects.all()}
        periodo1 = Periodos.objects.get(numero=1, gestion=2026)
        dimensiones = list(DimensionesEvaluacion.objects.filter(gestion=2026))

        asignaciones = {
            da.area.nombre: da
            for da in DocenteAsignacion.objects.filter(curso__gestion=2026).select_related('area')
        }

        activity_names = {
            'Matematicas': ['Sumas y Restas', 'Multiplicacion', 'Problemas Basicos'],
            'Lenguaje y Comunicacion': ['Lectura Comprensiva', 'Escritura Creativa', 'Ortografia'],
            'Ciencias Sociales': ['Mapas y Ubicacion', 'Historia Local', 'Civismo'],
            'Ciencias Naturales': ['El Cuerpo Humano', 'Los Animales', 'Las Plantas'],
            'Artes Plasticas': ['Dibujo Libre', 'Pintura', 'Mosaico'],
            'Educacion Fisica': ['Ejercicios de Calentamiento', 'Juegos Deportivos', 'Coordinacion'],
            'Tecnica Tecnologica': ['Herramientas Basicas', 'Proyecto Tecnologico', 'Materiales'],
            'Educacion Musical': ['Canciones Escolares', 'Instrumentos Musicales', 'Ritmo y Percusion'],
            'Valores,Ecspiritualidad y Religiones': ['Valores Familiares', 'Espiritualidad', 'Religion y Cultura'],
        }

        actividades = []
        idx = 0
        for area_nombre, names in activity_names.items():
            asignacion = asignaciones.get(area_nombre)
            if not asignacion:
                continue
            for aname in names:
                dim = dimensiones[idx % len(dimensiones)]
                actividades.append(Actividades(
                    docente_asignacion=asignacion,
                    periodo=periodo1,
                    dimension=dim,
                    nombre=aname,
                    descripcion=f'{aname} - {area_nombre}',
                    puntaje_maximo=Decimal('20.00'),
                    fecha_actividad=date(2026, 3, 1 + idx),
                ))
                idx += 1

        Actividades.objects.bulk_create(actividades)
        self.stdout.write('  actividades OK')

    def _seed_notas(self):
        actividades = list(Actividades.objects.all())
        estudiantes = list(Estudiantes.objects.all())

        notas = []
        for actividad in actividades:
            for estudiante in estudiantes:
                valor = Decimal(str(randint(10, 20)))
                notas.append(ActividadNotas(
                    actividad=actividad,
                    estudiante=estudiante,
                    valor=valor,
                ))

        ActividadNotas.objects.bulk_create(notas, ignore_conflicts=True)
        self.stdout.write('  notas OK')

    def _seed_asistencias(self):
        director = Usuarios.objects.get(email='director@uepanama.com')
        asignaciones = list(DocenteAsignacion.objects.filter(gestion=2026).select_related('curso'))
        if not asignaciones:
            self.stdout.write('  asistencias: no hay asignaciones, saltando')
            return

        start = date(2026, 3, 1)
        school_days = []
        d = start
        while len(school_days) < 20:
            if d.weekday() < 5:
                school_days.append(d)
            d += timedelta(days=1)

        # Pre-fetch students per (curso_id, gestion) for all asignaciones
        from collections import defaultdict

        inscripciones = Inscripciones.objects.filter(
            curso_id__in=[da.curso_id for da in asignaciones],
            gestion=2026,
            estado='activo',
        ).select_related('estudiante')

        curso_estudiantes = defaultdict(list)
        for ins in inscripciones:
            curso_estudiantes[ins.curso_id].append(ins.estudiante)

        asistencias = []
        estados_opts = ['presente', 'presente', 'presente', 'presente', 'presente',
                        'presente', 'presente', 'presente', 'ausente', 'con_licencia']
        for da in asignaciones:
            estudiantes = curso_estudiantes.get(da.curso_id, [])
            for dia in school_days:
                for estudiante in estudiantes:
                    estado = choice(estados_opts)
                    asistencias.append(Asistencias(
                        estudiante=estudiante,
                        docente_asignacion=da,
                        fecha=dia,
                        estado=estado,
                        tipo='por_asignacion',
                        registrado_por=director,
                    ))

        Asistencias.objects.bulk_create(asistencias, ignore_conflicts=True, batch_size=500)
        self.stdout.write('  asistencias OK')

    def _seed_horarios(self):
        from collections import defaultdict
        asignaciones = {
            da.area.nombre: da
            for da in DocenteAsignacion.objects.filter(gestion=2026).select_related('area')
        }

        schedule = [
            # (area_nombre, dia, hora_inicio, hora_fin, aula)
            ('Matematicas',              1, '08:00', '08:45', 'Aula 1'),
            ('Matematicas',              3, '09:00', '09:45', 'Aula 1'),
            ('Lenguaje y Comunicacion',  1, '09:00', '09:45', 'Aula 2'),
            ('Lenguaje y Comunicacion',  3, '10:00', '10:45', 'Aula 2'),
            ('Ciencias Sociales',        2, '08:00', '08:45', 'Aula 3'),
            ('Ciencias Sociales',        4, '09:00', '09:45', 'Aula 3'),
            ('Ciencias Naturales',       2, '09:00', '09:45', 'Aula 4'),
            ('Ciencias Naturales',       5, '08:00', '08:45', 'Aula 4'),
            ('Artes Plasticas',          4, '08:00', '08:45', 'Aula 5'),
            ('Artes Plasticas',          5, '10:00', '10:45', 'Aula 5'),
            ('Educacion Fisica',         2, '10:00', '10:45', 'Cancha'),
            ('Educacion Fisica',         5, '09:00', '09:45', 'Cancha'),
            ('Tecnica Tecnologica',      1, '10:00', '10:45', 'Taller 1'),
            ('Tecnica Tecnologica',      3, '08:00', '08:45', 'Taller 2'),
            ('Tecnica Tecnologica',      4, '10:00', '10:45', 'Taller 3'),
            ('Educacion Musical',        2, '11:00', '11:45', 'Musica'),
            ('Educacion Musical',        4, '11:00', '11:45', 'Musica'),
            ('Valores,Ecspiritualidad y Religiones', 3, '11:00', '11:45', 'Aula 6'),
            ('Valores,Ecspiritualidad y Religiones', 5, '11:00', '11:45', 'Aula 6'),
        ]

        horarios = []
        for area_nombre, dia, h_ini, h_fin, aula in schedule:
            da = asignaciones.get(area_nombre)
            if not da:
                continue
            horarios.append(Horarios(
                docente_asignacion=da,
                dia_semana=dia,
                hora_inicio=h_ini,
                hora_fin=h_fin,
                aula=aula,
                activo=True,
            ))
        Horarios.objects.bulk_create(horarios)
        self.stdout.write('  horarios OK')
