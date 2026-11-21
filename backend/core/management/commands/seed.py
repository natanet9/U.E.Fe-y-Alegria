"""
Comando único y maestro de sembrado de datos (Seed) para la U.E. Fe y Alegría.

Genera un conjunto integral, funcional y realista de datos tanto para:
1. El sistema web administrativo y de docentes (calificaciones, dimensiones,
   horarios, asistencias, reportes, licencias, periodos y cierres).
2. El portal móvil PWA para padres de familia (cuentas de tutor autenticables con CI,
   familias multihijo en primaria/secundaria, boletines con materias aprobadas y
   reprobadas < 51 pts para probar el Agente IA, observaciones docentes y asistencias).

Uso:
    python manage.py seed          # Inserta o actualiza datos sin duplicar
    python manage.py seed --flush  # Limpia la base de datos y vuelve a sembrar desde cero
"""

from datetime import date, time, timedelta
from decimal import Decimal
from random import choice, randint, random, seed as random_seed

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from core.models import (
    Actividades, ActividadNotas, Areas, Asistencias,
    ConfiguracionEscuela, Cursos, DimensionConfigPeriodo,
    DimensionesEvaluacion, DocenteAsignacion, Docentes,
    Estudiantes, EstudianteTutor, Grados, Horarios,
    Inscripciones, Licencias, Niveles, NotaObservaciones,
    Notificacion, Paralelos, Periodos, PeriodoCierreDocente,
    Roles, Tutores, Usuarios,
)

PASSWORD_DEFAULT = make_password('123456')


class Command(BaseCommand):
    help = 'Puebla la base de datos con información demo funcional y completa para docentes y padres.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Elimina todos los datos previos antes de ejecutar el sembrado.',
        )

    def handle(self, *args, **options):
        random_seed(2026)

        if options.get('flush'):
            self.stdout.write(self.style.WARNING('Limpiando base de datos completa...'))
            self._limpiar_todo()

        with transaction.atomic():
            self._seed_configuracion()
            self._seed_roles()
            self._seed_niveles()
            self._seed_grados()
            self._seed_paralelos()
            self._seed_areas()
            self._seed_dimensiones()
            self._seed_periodos()
            self._seed_dimension_config()
            self._seed_cursos()
            self._seed_usuarios_y_docentes()
            self._seed_tutores_y_estudiantes()
            self._seed_inscripciones()
            self._seed_docente_asignaciones()
            self._seed_horarios()
            self._seed_actividades_y_notas()
            self._seed_observaciones()
            self._seed_asistencias()
            self._seed_licencias()
            self._seed_notificaciones()

        self._imprimir_resumen()

    # -------------------------------------------------------------------------
    # 1. LIMPIEZA TOTAL
    # -------------------------------------------------------------------------
    def _limpiar_todo(self):
        models_to_delete = [
            Notificacion,
            NotaObservaciones,
            ActividadNotas,
            Actividades,
            Horarios,
            Asistencias,
            Licencias,
            PeriodoCierreDocente,
            DocenteAsignacion,
            Inscripciones,
            EstudianteTutor,
            Estudiantes,
            Tutores,
            Docentes,
            Usuarios,
            DimensionConfigPeriodo,
            Periodos,
            DimensionesEvaluacion,
            Cursos,
            Grados,
            Niveles,
            Paralelos,
            Areas,
            Roles,
            ConfiguracionEscuela,
        ]
        for m in models_to_delete:
            try:
                m.objects.all().delete()
            except Exception as e:
                self.stdout.write(f'  aviso al limpiar {m.__name__}: {e}')
        self.stdout.write(self.style.SUCCESS('  Base de datos limpiada.'))

    # -------------------------------------------------------------------------
    # 2. CONFIGURACIÓN INSTITUCIONAL
    # -------------------------------------------------------------------------
    def _seed_configuracion(self):
        ConfiguracionEscuela.objects.update_or_create(
            id=1,
            defaults={
                'nombre': 'U.E. Fe y Alegría',
                'direccion': 'Av. Principal #123, Zona Villa Fátima',
                'telefono': '22841234',
                'email': 'contacto@feya.edu.bo',
                'ciudad': 'La Paz',
                'gestion_actual': 2026,
                'escala_aprobacion': Decimal('51.00'),
            },
        )
        self.stdout.write('  Configuración institucional OK')

    # -------------------------------------------------------------------------
    # 3. ROLES
    # -------------------------------------------------------------------------
    def _seed_roles(self):
        roles_data = [
            ('director', 'Director de la unidad educativa'),
            ('secretaria', 'Personal administrativo'),
            ('docente', 'Maestro o maestra de aula/área'),
            ('regente', 'Regente de disciplina y control de asistencia'),
            ('tutor', 'Padre, madre o tutor legal'),
        ]
        for nombre, desc in roles_data:
            Roles.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc, 'activo': True})
        self.stdout.write('  Roles OK')

    # -------------------------------------------------------------------------
    # 4. ESTRUCTURA ACADÉMICA (NIVELES, GRADOS, PARALELOS)
    # -------------------------------------------------------------------------
    def _seed_niveles(self):
        for n in ('Primario', 'Secundario'):
            Niveles.objects.get_or_create(nombre=n, defaults={'activo': True})
        self.stdout.write('  Niveles OK')

    def _seed_grados(self):
        prim = Niveles.objects.get(nombre='Primario')
        sec = Niveles.objects.get(nombre='Secundario')

        grados_prim = [
            (1, 'Primero de Primaria'),
            (2, 'Segundo de Primaria'),
            (3, 'Tercero de Primaria'),
            (4, 'Cuarto de Primaria'),
            (5, 'Quinto de Primaria'),
            (6, 'Sexto de Primaria'),
        ]
        grados_sec = [
            (1, 'Primero de Secundaria'),
            (2, 'Segundo de Secundaria'),
            (3, 'Tercero de Secundaria'),
            (4, 'Cuarto de Secundaria'),
            (5, 'Quinto de Secundaria'),
            (6, 'Sexto de Secundaria'),
        ]

        for num, nombre in grados_prim:
            Grados.objects.get_or_create(nivel=prim, numero=num, defaults={'nombre': nombre, 'activo': True})
        for num, nombre in grados_sec:
            Grados.objects.get_or_create(nivel=sec, numero=num, defaults={'nombre': nombre, 'activo': True})
        self.stdout.write('  Grados OK')

    def _seed_paralelos(self):
        for p in ('A', 'B'):
            Paralelos.objects.get_or_create(nombre=p, defaults={'activo': True})
        self.stdout.write('  Paralelos OK')

    # -------------------------------------------------------------------------
    # 5. ÁREAS (MATERIAS)
    # -------------------------------------------------------------------------
    def _seed_areas(self):
        areas = [
            'Matematicas',
            'Lenguaje y Comunicacion',
            'Ciencias Sociales',
            'Ciencias Naturales',
            'Artes Plasticas',
            'Educacion Fisica',
            'Tecnica Tecnologica',
            'Educacion Musical',
            'Valores, Espiritualidad y Religiones',
            'Ingles',
            'Biologia - Geografia',
            'Fisica - Quimica',
        ]
        for nombre in areas:
            Areas.objects.get_or_create(nombre=nombre, defaults={'activo': True})
        self.stdout.write('  Áreas de conocimiento OK')

    # -------------------------------------------------------------------------
    # 6. DIMENSIONES DE EVALUACIÓN (LEY 070)
    # -------------------------------------------------------------------------
    def _seed_dimensiones(self):
        dims = [
            ('SER', 1, Decimal('10.00')),
            ('SABER', 2, Decimal('45.00')),
            ('HACER', 3, Decimal('40.00')),
            ('AUTOEVALUACION', 4, Decimal('5.00')),
        ]
        for gestion in (2025, 2026):
            for nombre, orden, pts in dims:
                DimensionesEvaluacion.objects.get_or_create(
                    nombre=nombre,
                    gestion=gestion,
                    defaults={'orden': orden, 'puntaje_maximo': pts, 'activo': True},
                )
        self.stdout.write('  Dimensiones curriculares OK (SER:10, SABER:45, HACER:40, AUTO:5)')

    # -------------------------------------------------------------------------
    # 7. PERIODOS (TRIMESTRES)
    # -------------------------------------------------------------------------
    def _seed_periodos(self):
        # Trimestres 2026: T1 cerrado, T2 activo, T3 pendiente
        trims_2026 = [
            (1, 'Primer Trimestre', date(2026, 2, 2), date(2026, 4, 30), 'cerrado'),
            (2, 'Segundo Trimestre', date(2026, 5, 4), date(2026, 8, 28), 'activo'),
            (3, 'Tercer Trimestre', date(2026, 9, 1), date(2026, 11, 27), 'pendiente'),
        ]
        for num, nombre, f_ini, f_fin, estado in trims_2026:
            Periodos.objects.get_or_create(
                numero=num,
                gestion=2026,
                defaults={
                    'nombre': nombre,
                    'fecha_inicio': f_ini,
                    'fecha_fin': f_fin,
                    'estado': estado,
                    'activo': True,
                },
            )

        # Trimestres 2025 para historial
        trims_2025 = [
            (1, 'Primer Trimestre', date(2025, 2, 3), date(2025, 4, 30), 'cerrado'),
            (2, 'Segundo Trimestre', date(2025, 5, 5), date(2025, 8, 29), 'cerrado'),
            (3, 'Tercer Trimestre', date(2025, 9, 1), date(2025, 11, 28), 'cerrado'),
        ]
        for num, nombre, f_ini, f_fin, estado in trims_2025:
            Periodos.objects.get_or_create(
                numero=num,
                gestion=2025,
                defaults={
                    'nombre': nombre,
                    'fecha_inicio': f_ini,
                    'fecha_fin': f_fin,
                    'estado': estado,
                    'activo': True,
                },
            )
        self.stdout.write('  Periodos escolares OK')

    def _seed_dimension_config(self):
        puntajes = {'SER': 10, 'SABER': 45, 'HACER': 40, 'AUTOEVALUACION': 5}
        for periodo in Periodos.objects.all():
            for dim_nombre, pts in puntajes.items():
                dim = DimensionesEvaluacion.objects.filter(nombre=dim_nombre, gestion=periodo.gestion).first()
                if dim:
                    DimensionConfigPeriodo.objects.get_or_create(
                        periodo=periodo,
                        dimension=dim,
                        defaults={'puntaje_maximo': Decimal(str(pts))},
                    )
        self.stdout.write('  Configuración de puntajes por periodo OK')

    # -------------------------------------------------------------------------
    # 8. CURSOS
    # -------------------------------------------------------------------------
    def _seed_cursos(self):
        paralelo_a = Paralelos.objects.get(nombre='A')
        paralelo_b = Paralelos.objects.get(nombre='B')

        # Cursos 2026 clave para pruebas
        cursos_data = [
            ('Primario', 1, paralelo_a, 2026),
            ('Primario', 1, paralelo_b, 2026),
            ('Primario', 2, paralelo_a, 2026),
            ('Primario', 3, paralelo_a, 2026),
            ('Primario', 4, paralelo_a, 2026),
            ('Secundario', 1, paralelo_a, 2026),
            ('Secundario', 2, paralelo_a, 2026),
            # Cursos 2025 para antecedentes
            ('Primario', 1, paralelo_a, 2025),
            ('Primario', 2, paralelo_a, 2025),
        ]
        for nivel_n, grado_num, par, gestion in cursos_data:
            grado = Grados.objects.get(nivel__nombre=nivel_n, numero=grado_num)
            Cursos.objects.get_or_create(
                grado=grado,
                paralelo=par,
                gestion=gestion,
                defaults={'activo': True},
            )
        self.stdout.write('  Cursos OK (Primaria y Secundaria 2026/2025)')

    # -------------------------------------------------------------------------
    # 9. USUARIOS Y DOCENTES
    # -------------------------------------------------------------------------
    def _seed_usuarios_y_docentes(self):
        rol_dir = Roles.objects.get(nombre='director')
        rol_sec = Roles.objects.get(nombre='secretaria')
        rol_reg = Roles.objects.get(nombre='regente')
        rol_doc = Roles.objects.get(nombre='docente')

        personal = [
            ('director@feya.edu.bo', '1000001', 'Carlos', 'Mendoza', 'Vargas', rol_dir),
            ('secretaria@feya.edu.bo', '1000002', 'Ana', 'Rojas', 'Flores', rol_sec),
            ('regente@feya.edu.bo', '1000003', 'Laura', 'Vargas', 'Mamani', rol_reg),
        ]
        for email, ci, nom, ap1, ap2, rol in personal:
            Usuarios.objects.get_or_create(
                email=email,
                defaults={
                    'ci': ci,
                    'nombre': nom,
                    'primer_apellido': ap1,
                    'segundo_apellido': ap2,
                    'usuario': ci,
                    'correo_personal': email,
                    'password_hash': PASSWORD_DEFAULT,
                    'rol': rol,
                    'activo': True,
                },
            )

        # 8 Docentes con perfiles reales
        docentes_data = [
            ('docente1@feya.edu.bo', '1000004', 'Roberto', 'Vargas', 'Quispe', 'Lic.', 'Matematicas', 12),
            ('docente2@feya.edu.bo', '1000005', 'Carmen', 'Flores', 'Morales', 'Lic.', 'Lenguaje y Comunicacion', 10),
            ('docente3@feya.edu.bo', '1000006', 'Jorge', 'Torrez', 'Ramos', 'Lic.', 'Ciencias Sociales', 8),
            ('docente4@feya.edu.bo', '1000007', 'Ana', 'Gutierrez', 'Cruz', 'Mgr.', 'Ciencias Naturales', 14),
            ('docente5@feya.edu.bo', '1000008', 'Luis', 'Paredes', 'Mamani', 'Prof.', 'Artes Plasticas', 6),
            ('docente6@feya.edu.bo', '1000009', 'Sandra', 'Rojas', 'Condori', 'Lic.', 'Educacion Fisica', 9),
            ('docente7@feya.edu.bo', '1000010', 'Carlos', 'Mendoza', 'Aguilar', 'Ing.', 'Tecnica Tecnologica', 7),
            ('docente8@feya.edu.bo', '1000011', 'Monica', 'Huanca', 'Vargas', 'Mgr.', 'Ingles', 11),
        ]
        for email, ci, nom, ap1, ap2, titulo, esp, exp in docentes_data:
            usr, _ = Usuarios.objects.get_or_create(
                email=email,
                defaults={
                    'ci': ci,
                    'nombre': nom,
                    'primer_apellido': ap1,
                    'segundo_apellido': ap2,
                    'usuario': ci,
                    'correo_personal': email,
                    'password_hash': PASSWORD_DEFAULT,
                    'rol': rol_doc,
                    'activo': True,
                },
            )
            Docentes.objects.get_or_create(
                usuario=usr,
                defaults={
                    'titulo_academico': titulo,
                    'especialidad': esp,
                    'fecha_ingreso_institucion': date(2015, 2, 1),
                    'anos_experiencia': exp,
                    'activo': True,
                },
            )
        self.stdout.write('  Usuarios administrativos y 8 Docentes OK')

    # -------------------------------------------------------------------------
    # 10. TUTORES (PADRES) Y ESTUDIANTES (MULTIHIJO Y CASOS DE PRUEBA MASIVOS)
    # -------------------------------------------------------------------------
    def _seed_tutores_y_estudiantes(self):
        rol_tutor = Roles.objects.get(nombre='tutor')

        # Catálogo masivo y coherente de 35 tutores (todos con cuenta de usuario activa y contraseña 123456)
        tutores_seed = [
            # Clave 1: Caso Multihijo #1 (3 hijos: Primaria y Secundaria, hijo en riesgo <51 pts)
            ('7000001', 'Juan Carlos', 'Perez', 'Mamani', 'Padre', '77700001'),
            # Clave 2: Caso Multihijo #2 (2 hijas en Primaria)
            ('7000002', 'Rosa Maria', 'Condori', 'Flores', 'Madre', '77700002'),
            # Clave 3: Caso Hijo Único de alto rendimiento
            ('7000003', 'Luis Alberto', 'Choque', 'Vargas', 'Padre', '77700003'),
            # Clave 4: Caso Inclusión / Estudiante con Discapacidad
            ('7000004', 'Elena Sofia', 'Huanca', 'Paco', 'Madre', '77700004'),
            # Clave 5: Caso Multihijo con Estudiante TEA en Primaria y hermano en Secundaria
            ('7000005', 'Oscar Rene', 'Torrez', 'Morales', 'Padre', '77700005'),
            # Clave 6: Caso Hija Única en Primaria
            ('7000006', 'Carla Patricia', 'Ramos', 'Gutierrez', 'Madre', '77700006'),
            # Clave 7: Caso Multihijo Primaria y Secundaria
            ('7000007', 'Pedro Antonio', 'Zeballos', 'Cruz', 'Padre', '77700007'),
            ('7000008', 'Sonia Beatriz', 'Paredes', 'Rojas', 'Madre', '77700008'),
            ('7000009', 'Miguel Angel', 'Mendoza', 'Cardenas', 'Padre', '77700009'),
            ('7000010', 'Diana Carolina', 'Loza', 'Aguilar', 'Madre', '77700010'),
            ('7000011', 'Fernando Javier', 'Quispe', 'Callisaya', 'Padre', '77700011'),
            ('7000012', 'Maria Teresa', 'Alvarez', 'Ticona', 'Madre', '77700012'),
            ('7000013', 'Gonzalo Mauricio', 'Gutierrez', 'Chavez', 'Padre', '77700013'),
            ('7000014', 'Patricia Rocio', 'Colque', 'Blanco', 'Madre', '77700014'),
            ('7000015', 'Victor Hugo', 'Machaca', 'Aruquipa', 'Padre', '77700015'),
            ('7000016', 'Silvia Veronica', 'Limachi', 'Villca', 'Madre', '77700016'),
            ('7000017', 'Jorge Eduardo', 'Chambi', 'Apaza', 'Padre', '77700017'),
            ('7000018', 'Lourdes Maribel', 'Yujra', 'Cusi', 'Madre', '77700018'),
            ('7000019', 'Ramiro Marcelo', 'Chura', 'Luna', 'Padre', '77700019'),
            ('7000020', 'Beatriz Roxana', 'Acarapi', 'Nina', 'Madre', '77700020'),
            ('7000021', 'Guillermo Andres', 'Sirpa', 'Quenta', 'Padre', '77700021'),
            ('7000022', 'Norma Gladys', 'Canaviri', 'Velasco', 'Madre', '77700022'),
            ('7000023', 'Rolando Esteban', 'Huarachi', 'Mollo', 'Padre', '77700023'),
            ('7000024', 'Cecilia Andrea', 'Tancara', 'Pinto', 'Madre', '77700024'),
            ('7000025', 'Edgar David', 'Molle', 'Mamani', 'Padre', '77700025'),
            ('7000026', 'Miriam Roxana', 'Vera', 'Ochoa', 'Madre', '77700026'),
            ('7000027', 'Hugo Hernan', 'Suxo', 'Bautista', 'Padre', '77700027'),
            ('7000028', 'Jenny Elizabeth', 'Tintaya', 'Miranda', 'Madre', '77700028'),
            ('7000029', 'Raul Ignacio', 'Larico', 'Quisbert', 'Padre', '77700029'),
            ('7000030', 'Maritza Paola', 'Quispe', 'Herrera', 'Madre', '77700030'),
            ('7000031', 'Walter Alejandro', 'Maldonado', 'Gomez', 'Padre', '77700031'),
            ('7000032', 'Gladys Teresa', 'Salazar', 'Romero', 'Madre', '77700032'),
            ('7000033', 'Jaime Orlando', 'Navarro', 'Salinas', 'Padre', '77700033'),
            ('7000034', 'Nancy Marlene', 'Espinoza', 'Zambrana', 'Madre', '77700034'),
            ('7000035', 'Ruben Dario', 'Camacho', 'Delgado', 'Padre', '77700035'),
        ]

        tutores_objs = {}
        for ci, nom, ap1, ap2, parentesco, cel in tutores_seed:
            email_tutor = f'tutor.{ci}@feya.edu.bo'
            usr, _ = Usuarios.objects.get_or_create(
                ci=ci,
                defaults={
                    'email': email_tutor,
                    'nombre': nom,
                    'primer_apellido': ap1,
                    'segundo_apellido': ap2,
                    'usuario': ci,
                    'correo_personal': email_tutor,
                    'password_hash': PASSWORD_DEFAULT,
                    'rol': rol_tutor,
                    'activo': True,
                },
            )
            # Asegurar que contraseña sea PASSWORD_DEFAULT
            if usr.password_hash != PASSWORD_DEFAULT:
                usr.password_hash = PASSWORD_DEFAULT
                usr.activo = True
                usr.save(update_fields=['password_hash', 'activo'])

            tut, _ = Tutores.objects.get_or_create(
                ci=ci,
                defaults={
                    'usuario': usr,
                    'nombres': nom,
                    'primer_apellido': ap1,
                    'segundo_apellido': ap2,
                    'parentesco': parentesco,
                    'celular': cel,
                    'tipo_documento': 'CI',
                    'idioma_frecuente': 'Español',
                    'fecha_nacimiento': date(1982, 5, 12),
                    'activo': True,
                },
            )
            if tut.usuario_id != usr.id:
                tut.usuario = usr
                tut.save(update_fields=['usuario'])
            tutores_objs[ci] = tut

        # Catálogo masivo de 71 estudiantes distribuidos coherentemente:
        # 1° Primaria A (15 estudiantes), 2° Primaria A (12 estudiantes), 3° Primaria A (12 estudiantes),
        # 4° Primaria A (10 estudiantes), 1° Secundaria A (12 estudiantes), 2° Secundaria A (10 estudiantes)
        estudiantes_data = [
            # --- 1° PRIMARIA A (15 estudiantes) ---
            ('30000002', 'RUD2026002', 'Mateo', 'Perez', 'Mamani', 'M', date(2019, 8, 15), False, False, '7000001', '1-Prim-A'),
            ('30000006', 'RUD2026006', 'Gabriel', 'Choque', 'Vargas', 'M', date(2019, 1, 14), False, False, '7000003', '1-Prim-A'),
            ('30000007', 'RUD2026007', 'Daniela', 'Huanca', 'Paco', 'F', date(2019, 2, 18), True, False, '7000004', '1-Prim-A'),
            ('30000008', 'RUD2026008', 'Diego', 'Torrez', 'Morales', 'M', date(2019, 6, 25), False, True, '7000005', '1-Prim-A'),
            ('30000009', 'RUD2026009', 'Luciana', 'Ramos', 'Gutierrez', 'F', date(2019, 7, 30), False, False, '7000006', '1-Prim-A'),
            ('30000010', 'RUD2026010', 'Andres', 'Zeballos', 'Cruz', 'M', date(2019, 9, 12), False, False, '7000007', '1-Prim-A'),
            ('30000011', 'RUD2026011', 'Valeria', 'Paredes', 'Rojas', 'F', date(2019, 10, 5), False, False, '7000008', '1-Prim-A'),
            ('30000012', 'RUD2026012', 'Santiago', 'Mendoza', 'Cardenas', 'M', date(2019, 12, 1), False, False, '7000009', '1-Prim-A'),
            ('30000013', 'RUD2026013', 'Isabella', 'Loza', 'Aguilar', 'F', date(2019, 3, 21), False, False, '7000010', '1-Prim-A'),
            ('30000016', 'RUD2026016', 'Matias', 'Quispe', 'Callisaya', 'M', date(2019, 4, 11), False, False, '7000011', '1-Prim-A'),
            ('30000018', 'RUD2026018', 'Emma', 'Alvarez', 'Ticona', 'F', date(2019, 5, 29), False, False, '7000012', '1-Prim-A'),
            ('30000020', 'RUD2026020', 'Benjamin', 'Gutierrez', 'Chavez', 'M', date(2019, 7, 18), False, False, '7000013', '1-Prim-A'),
            ('30000022', 'RUD2026022', 'Victoria', 'Colque', 'Blanco', 'F', date(2019, 9, 9), False, False, '7000014', '1-Prim-A'),
            ('30000024', 'RUD2026024', 'Samuel', 'Machaca', 'Aruquipa', 'M', date(2019, 11, 23), False, False, '7000015', '1-Prim-A'),
            ('30000071', 'RUD2026071', 'Julian', 'Mamani', 'Aruquipa', 'M', date(2019, 8, 30), False, False, '7000015', '1-Prim-A'),

            # --- 2° PRIMARIA A (12 estudiantes) ---
            ('30000004', 'RUD2026004', 'Valentina', 'Flores', 'Condori', 'F', date(2018, 4, 5), False, False, '7000002', '2-Prim-A'),
            ('30000025', 'RUD2026025', 'Renata', 'Limachi', 'Villca', 'F', date(2018, 3, 14), False, False, '7000016', '2-Prim-A'),
            ('30000027', 'RUD2026027', 'Leonardo', 'Chambi', 'Apaza', 'M', date(2018, 5, 19), False, False, '7000017', '2-Prim-A'),
            ('30000029', 'RUD2026029', 'Abigail', 'Yujra', 'Cusi', 'F', date(2018, 6, 22), False, False, '7000018', '2-Prim-A'),
            ('30000031', 'RUD2026031', 'Bruno', 'Chura', 'Luna', 'M', date(2018, 8, 17), False, False, '7000019', '2-Prim-A'),
            ('30000033', 'RUD2026033', 'Emilia', 'Acarapi', 'Nina', 'F', date(2018, 10, 4), False, False, '7000020', '2-Prim-A'),
            ('30000035', 'RUD2026035', 'Alejandro', 'Sirpa', 'Quenta', 'M', date(2018, 11, 12), False, False, '7000021', '2-Prim-A'),
            ('30000037', 'RUD2026037', 'Julieta', 'Canaviri', 'Velasco', 'F', date(2018, 1, 28), False, False, '7000022', '2-Prim-A'),
            ('30000039', 'RUD2026039', 'Tomas', 'Huarachi', 'Mollo', 'M', date(2018, 2, 16), False, False, '7000023', '2-Prim-A'),
            ('30000041', 'RUD2026041', 'Amanda', 'Tancara', 'Pinto', 'F', date(2018, 7, 24), False, False, '7000024', '2-Prim-A'),
            ('30000043', 'RUD2026043', 'Agustin', 'Molle', 'Mamani', 'M', date(2018, 9, 3), False, False, '7000025', '2-Prim-A'),
            ('30000045', 'RUD2026045', 'Antonella', 'Vera', 'Ochoa', 'F', date(2018, 12, 15), False, False, '7000026', '2-Prim-A'),

            # --- 3° PRIMARIA A (12 estudiantes) ---
            ('30000001', 'RUD2026001', 'Lucas', 'Perez', 'Mamani', 'M', date(2017, 3, 10), False, False, '7000001', '3-Prim-A'),
            ('30000019', 'RUD2026019', 'Joaquin', 'Alvarez', 'Ticona', 'M', date(2017, 2, 18), False, False, '7000012', '3-Prim-A'),
            ('30000026', 'RUD2026026', 'Sebastian', 'Limachi', 'Villca', 'M', date(2017, 4, 25), False, False, '7000016', '3-Prim-A'),
            ('30000034', 'RUD2026034', 'Felipe', 'Acarapi', 'Nina', 'M', date(2017, 6, 8), False, False, '7000020', '3-Prim-A'),
            ('30000042', 'RUD2026042', 'Martin', 'Tancara', 'Pinto', 'M', date(2017, 7, 19), False, False, '7000024', '3-Prim-A'),
            ('30000047', 'RUD2026047', 'Alvaro', 'Suxo', 'Bautista', 'M', date(2017, 8, 30), False, False, '7000027', '3-Prim-A'),
            ('30000049', 'RUD2026049', 'Carolina', 'Tintaya', 'Miranda', 'F', date(2017, 10, 11), False, False, '7000028', '3-Prim-A'),
            ('30000051', 'RUD2026051', 'Esteban', 'Larico', 'Quisbert', 'M', date(2017, 11, 20), False, False, '7000029', '3-Prim-A'),
            ('30000053', 'RUD2026053', 'Valeria', 'Quispe', 'Herrera', 'F', date(2017, 1, 14), False, False, '7000030', '3-Prim-A'),
            ('30000055', 'RUD2026055', 'Adrian', 'Maldonado', 'Gomez', 'M', date(2017, 5, 23), False, False, '7000031', '3-Prim-A'),
            ('30000057', 'RUD2026057', 'Mariana', 'Salazar', 'Romero', 'F', date(2017, 9, 7), False, False, '7000032', '3-Prim-A'),
            ('30000070', 'RUD2026070', 'Rodrigo', 'Ramos', 'Romero', 'M', date(2017, 12, 5), False, False, '7000032', '3-Prim-A'),

            # --- 4° PRIMARIA A (10 estudiantes) ---
            ('30000005', 'RUD2026005', 'Camila', 'Flores', 'Condori', 'F', date(2016, 9, 22), False, False, '7000002', '4-Prim-A'),
            ('30000021', 'RUD2026021', 'Martina', 'Gutierrez', 'Chavez', 'F', date(2016, 3, 11), False, False, '7000013', '4-Prim-A'),
            ('30000028', 'RUD2026028', 'Mariana', 'Chambi', 'Apaza', 'F', date(2016, 5, 17), False, False, '7000017', '4-Prim-A'),
            ('30000036', 'RUD2026036', 'Paula', 'Sirpa', 'Quenta', 'F', date(2016, 7, 29), False, False, '7000021', '4-Prim-A'),
            ('30000044', 'RUD2026044', 'Sara', 'Molle', 'Mamani', 'F', date(2016, 8, 14), False, False, '7000025', '4-Prim-A'),
            ('30000050', 'RUD2026050', 'Pablo', 'Tintaya', 'Miranda', 'M', date(2016, 10, 6), False, False, '7000028', '4-Prim-A'),
            ('30000056', 'RUD2026056', 'Andrea', 'Maldonado', 'Gomez', 'F', date(2016, 11, 18), False, False, '7000031', '4-Prim-A'),
            ('30000059', 'RUD2026059', 'Simon', 'Navarro', 'Salinas', 'M', date(2016, 2, 9), False, False, '7000033', '4-Prim-A'),
            ('30000061', 'RUD2026061', 'Paulina', 'Espinoza', 'Zambrana', 'F', date(2016, 4, 28), False, False, '7000034', '4-Prim-A'),
            ('30000063', 'RUD2026063', 'Mauricio', 'Camacho', 'Delgado', 'M', date(2016, 6, 15), False, False, '7000035', '4-Prim-A'),

            # --- 1° SECUNDARIA A (12 estudiantes) ---
            ('30000014', 'RUD2026014', 'Carlos', 'Torrez', 'Morales', 'M', date(2013, 5, 14), False, False, '7000005', '1-Sec-A'),
            ('30000017', 'RUD2026017', 'Rodrigo', 'Quispe', 'Callisaya', 'M', date(2013, 6, 20), False, False, '7000011', '1-Sec-A'),
            ('30000030', 'RUD2026030', 'David', 'Yujra', 'Cusi', 'M', date(2013, 7, 25), False, False, '7000018', '1-Sec-A'),
            ('30000038', 'RUD2026038', 'Ignacio', 'Canaviri', 'Velasco', 'M', date(2013, 9, 10), False, False, '7000022', '1-Sec-A'),
            ('30000046', 'RUD2026046', 'Daniel', 'Vera', 'Ochoa', 'M', date(2013, 10, 30), False, False, '7000026', '1-Sec-A'),
            ('30000052', 'RUD2026052', 'Jimena', 'Larico', 'Quisbert', 'F', date(2013, 11, 14), False, False, '7000029', '1-Sec-A'),
            ('30000058', 'RUD2026058', 'Franco', 'Salazar', 'Romero', 'M', date(2013, 1, 22), False, False, '7000032', '1-Sec-A'),
            ('30000062', 'RUD2026062', 'Sergio', 'Espinoza', 'Zambrana', 'M', date(2013, 3, 16), False, False, '7000034', '1-Sec-A'),
            ('30000064', 'RUD2026064', 'Belen', 'Camacho', 'Delgado', 'F', date(2013, 4, 18), False, False, '7000035', '1-Sec-A'),
            ('30000065', 'RUD2026065', 'Javier', 'Pinto', 'Blanco', 'M', date(2013, 8, 5), False, False, '7000014', '1-Sec-A'),
            ('30000066', 'RUD2026066', 'Claudia', 'Rojas', 'Apaza', 'F', date(2013, 12, 12), False, False, '7000017', '1-Sec-A'),
            ('30000067', 'RUD2026067', 'Fernando', 'Choque', 'Mollo', 'M', date(2013, 2, 27), False, False, '7000023', '1-Sec-A'),

            # --- 2° SECUNDARIA A (10 estudiantes) ---
            ('30000003', 'RUD2026003', 'Sofia', 'Perez', 'Mamani', 'F', date(2012, 11, 20), False, False, '7000001', '2-Sec-A'),
            ('30000015', 'RUD2026015', 'Mariana', 'Zeballos', 'Cruz', 'F', date(2012, 8, 29), False, False, '7000007', '2-Sec-A'),
            ('30000023', 'RUD2026023', 'Nicolas', 'Colque', 'Blanco', 'M', date(2012, 3, 15), False, False, '7000014', '2-Sec-A'),
            ('30000032', 'RUD2026032', 'Natalia', 'Chura', 'Luna', 'F', date(2012, 5, 22), False, False, '7000019', '2-Sec-A'),
            ('30000040', 'RUD2026040', 'Florencia', 'Huarachi', 'Mollo', 'F', date(2012, 7, 10), False, False, '7000023', '2-Sec-A'),
            ('30000048', 'RUD2026048', 'Lucia', 'Suxo', 'Bautista', 'F', date(2012, 9, 14), False, False, '7000027', '2-Sec-A'),
            ('30000054', 'RUD2026054', 'Gustavo', 'Quispe', 'Herrera', 'M', date(2012, 10, 18), False, False, '7000030', '2-Sec-A'),
            ('30000060', 'RUD2026060', 'Rocio', 'Navarro', 'Salinas', 'F', date(2012, 1, 25), False, False, '7000033', '2-Sec-A'),
            ('30000068', 'RUD2026068', 'Marcelo', 'Castro', 'Miranda', 'M', date(2012, 4, 30), False, False, '7000028', '2-Sec-A'),
            ('30000069', 'RUD2026069', 'Viviana', 'Morales', 'Gomez', 'F', date(2012, 6, 21), False, False, '7000031', '2-Sec-A'),
        ]

        self.estudiantes_map = {}
        self.estudiantes_curso_map = {}

        for ci, rude, nom, ap1, ap2, gen, f_nac, disc, tea, tutor_ci, tag_curso in estudiantes_data:
            est, _ = Estudiantes.objects.get_or_create(
                ci=ci,
                defaults={
                    'rude': rude,
                    'nombres': nom,
                    'primer_apellido': ap1,
                    'segundo_apellido': ap2,
                    'genero': gen,
                    'fecha_nacimiento': f_nac,
                    'pais_nacimiento': 'Bolivia',
                    'tiene_discapacidad': disc,
                    'tiene_tea': tea,
                    'estado': 'activo',
                },
            )
            self.estudiantes_map[ci] = est
            self.estudiantes_curso_map[est.id] = tag_curso

            tutor_obj = tutores_objs.get(tutor_ci)
            if tutor_obj:
                EstudianteTutor.objects.get_or_create(
                    estudiante=est,
                    tutor=tutor_obj,
                    defaults={'es_principal': True, 'activo': True},
                )

        self.stdout.write(f'  Tutores ({len(tutores_objs)}) y Estudiantes ({len(self.estudiantes_map)}) creados con vínculos familiares')

    # -------------------------------------------------------------------------
    # 11. INSCRIPCIONES
    # -------------------------------------------------------------------------
    def _seed_inscripciones(self):
        c_1prim_a = Cursos.objects.get(grado__nombre='Primero de Primaria', paralelo__nombre='A', gestion=2026)
        c_2prim_a = Cursos.objects.get(grado__nombre='Segundo de Primaria', paralelo__nombre='A', gestion=2026)
        c_3prim_a = Cursos.objects.get(grado__nombre='Tercero de Primaria', paralelo__nombre='A', gestion=2026)
        c_4prim_a = Cursos.objects.get(grado__nombre='Cuarto de Primaria', paralelo__nombre='A', gestion=2026)
        c_1sec_a = Cursos.objects.get(grado__nombre='Primero de Secundaria', paralelo__nombre='A', gestion=2026)
        c_2sec_a = Cursos.objects.get(grado__nombre='Segundo de Secundaria', paralelo__nombre='A', gestion=2026)

        curso_lookup = {
            '1-Prim-A': c_1prim_a,
            '2-Prim-A': c_2prim_a,
            '3-Prim-A': c_3prim_a,
            '4-Prim-A': c_4prim_a,
            '1-Sec-A': c_1sec_a,
            '2-Sec-A': c_2sec_a,
        }

        # Inscripciones 2026
        for est_id, tag in self.estudiantes_curso_map.items():
            curso = curso_lookup.get(tag)
            if curso:
                est = Estudiantes.objects.get(id=est_id)
                Inscripciones.objects.get_or_create(
                    estudiante=est,
                    gestion=2026,
                    defaults={'curso': curso, 'estado': 'activo', 'activo': True},
                )

        # Inscripciones históricas 2025 para antecedentes
        c_1prim_2025 = Cursos.objects.get(grado__nombre='Primero de Primaria', paralelo__nombre='A', gestion=2025)
        est_val = self.estudiantes_map['30000004']
        Inscripciones.objects.get_or_create(
            estudiante=est_val,
            gestion=2025,
            defaults={'curso': c_1prim_2025, 'estado': 'activo', 'activo': True},
        )
        self.stdout.write('  Inscripciones OK (71 estudiantes matriculados en 6 cursos)')

    # -------------------------------------------------------------------------
    # 12. DOCENTE ASIGNACIONES (PRIMARIA Y SECUNDARIA)
    # -------------------------------------------------------------------------
    def _seed_docente_asignaciones(self):
        docentes = {
            'mat': Docentes.objects.get(usuario__email='docente1@feya.edu.bo'),
            'len': Docentes.objects.get(usuario__email='docente2@feya.edu.bo'),
            'soc': Docentes.objects.get(usuario__email='docente3@feya.edu.bo'),
            'nat': Docentes.objects.get(usuario__email='docente4@feya.edu.bo'),
            'art': Docentes.objects.get(usuario__email='docente5@feya.edu.bo'),
            'fis': Docentes.objects.get(usuario__email='docente6@feya.edu.bo'),
            'tec': Docentes.objects.get(usuario__email='docente7@feya.edu.bo'),
            'ing': Docentes.objects.get(usuario__email='docente8@feya.edu.bo'),
        }

        areas = {a.nombre: a for a in Areas.objects.all()}

        # Cursos 2026 en paralelo A
        cursos_activos = Cursos.objects.filter(gestion=2026, paralelo__nombre='A').select_related('grado__nivel')

        plan_primaria = [
            ('Matematicas', docentes['mat']),
            ('Lenguaje y Comunicacion', docentes['len']),
            ('Ciencias Sociales', docentes['soc']),
            ('Ciencias Naturales', docentes['nat']),
            ('Artes Plasticas', docentes['art']),
            ('Educacion Fisica', docentes['fis']),
            ('Tecnica Tecnologica', docentes['tec']),
            ('Ingles', docentes['ing']),
        ]

        plan_secundaria = [
            ('Matematicas', docentes['mat']),
            ('Lenguaje y Comunicacion', docentes['len']),
            ('Ciencias Sociales', docentes['soc']),
            ('Biologia - Geografia', docentes['nat']),
            ('Fisica - Quimica', docentes['mat']),
            ('Artes Plasticas', docentes['art']),
            ('Educacion Fisica', docentes['fis']),
            ('Ingles', docentes['ing']),
        ]

        self.asignaciones_creadas = []
        for curso in cursos_activos:
            es_primaria = curso.grado.nivel.nombre == 'Primario'
            plan = plan_primaria if es_primaria else plan_secundaria

            for area_nombre, doc in plan:
                area_obj = areas.get(area_nombre)
                if area_obj:
                    da, _ = DocenteAsignacion.objects.get_or_create(
                        curso=curso,
                        area=area_obj,
                        gestion=2026,
                        defaults={'docente': doc, 'activo': True},
                    )
                    self.asignaciones_creadas.append(da)

        self.stdout.write(f'  Asignaciones docentes OK ({len(self.asignaciones_creadas)} materias asignadas)')

    # -------------------------------------------------------------------------
    # 13. HORARIOS
    # -------------------------------------------------------------------------
    def _seed_horarios(self):
        dias_semana = [1, 2, 3, 4, 5]
        horas = [
            (time(8, 0), time(8, 45)),
            (time(8, 45), time(9, 30)),
            (time(9, 45), time(10, 30)),
            (time(10, 30), time(11, 15)),
            (time(11, 15), time(12, 0)),
        ]
        aulas = ['Aula 101', 'Aula 102', 'Aula 103', 'Aula 201', 'Aula 202', 'Laboratorio', 'Cancha Deportiva', 'Taller de Computación']

        horarios_count = 0
        for da in self.asignaciones_creadas:
            dia = choice(dias_semana)
            h_ini, h_fin = choice(horas)
            aula = choice(aulas)
            Horarios.objects.get_or_create(
                docente_asignacion=da,
                dia_semana=dia,
                hora_inicio=h_ini,
                defaults={'hora_fin': h_fin, 'aula': aula, 'activo': True},
            )
            horarios_count += 1
        self.stdout.write(f'  Horarios de clases OK ({horarios_count})')

    # -------------------------------------------------------------------------
    # 14. ACTIVIDADES Y NOTAS CALIFICADAS (TODOS LOS CURSOS Y ESTUDIANTES)
    # -------------------------------------------------------------------------
    def _seed_actividades_y_notas(self):
        director = Usuarios.objects.get(email='director@feya.edu.bo')
        dims = {d.nombre: d for d in DimensionesEvaluacion.objects.filter(gestion=2026)}

        p1 = Periodos.objects.get(numero=1, gestion=2026)
        p2 = Periodos.objects.get(numero=2, gestion=2026)

        actividades_data = [
            ('SER', 'Responsabilidad y Puntualidad', 'Evaluación de hábitos y valores en aula', Decimal('10.00')),
            ('SABER', 'Evaluación Escrita Conceptual', 'Prueba objetiva de contenidos', Decimal('45.00')),
            ('HACER', 'Trabajos Prácticos y Cuaderno', 'Revisión de actividades y proyectos en aula', Decimal('40.00')),
            ('AUTOEVALUACION', 'Autoevaluación del Estudiante', 'Reflexión individual del estudiante', Decimal('5.00')),
        ]

        # Evaluar todas las asignaciones activas de los 6 cursos 2026
        asignaciones_evaluables = list(DocenteAsignacion.objects.filter(
            gestion=2026,
            curso__paralelo__nombre='A',
        ).select_related('area', 'curso'))

        # Pre-cargar actividades existentes
        actividades_dict = {
            (act.docente_asignacion_id, act.periodo_id, act.dimension_id, act.nombre): act
            for act in Actividades.objects.filter(docente_asignacion__gestion=2026)
        }

        act_para_crear = []
        for da in asignaciones_evaluables:
            for periodo in (p1, p2):
                for dim_nombre, act_nom, act_desc, max_pts in actividades_data:
                    dim_obj = dims.get(dim_nombre)
                    if not dim_obj:
                        continue
                    nombre_act = f'{act_nom} ({da.area.nombre})'
                    key = (da.id, periodo.id, dim_obj.id, nombre_act)
                    if key not in actividades_dict:
                        act_para_crear.append(Actividades(
                            docente_asignacion=da,
                            periodo=periodo,
                            dimension=dim_obj,
                            nombre=nombre_act,
                            descripcion=f'{act_desc} para {da.area.nombre}',
                            puntaje_maximo=max_pts,
                            fecha_actividad=periodo.fecha_inicio + timedelta(days=20),
                            creado_por=director,
                            activo=True,
                        ))

        if act_para_crear:
            Actividades.objects.bulk_create(act_para_crear, batch_size=500)
            actividades_dict = {
                (act.docente_asignacion_id, act.periodo_id, act.dimension_id, act.nombre): act
                for act in Actividades.objects.filter(docente_asignacion__gestion=2026)
            }

        notas_para_crear = []
        for da in asignaciones_evaluables:
            estudiantes_curso = list(Estudiantes.objects.filter(
                inscripciones__curso=da.curso,
                inscripciones__gestion=2026,
                inscripciones__estado='activo',
            ))

            for periodo in (p1, p2):
                for dim_nombre, act_nom, _, max_pts in actividades_data:
                    dim_obj = dims.get(dim_nombre)
                    if not dim_obj:
                        continue
                    nombre_act = f'{act_nom} ({da.area.nombre})'
                    act = actividades_dict.get((da.id, periodo.id, dim_obj.id, nombre_act))
                    if not act:
                        continue

                    # Asignar notas a cada estudiante con curvas pedagógicas y casos de prueba
                    for est in estudiantes_curso:
                        # 1. Alumno Sobresaliente: Lucas Pérez (3° Primaria) -> 88 a 96 pts
                        if est.ci == '30000001':
                            factor = 0.90 + (random() * 0.07)
                        # 2. Alumno en Riesgo: Mateo Pérez (1° Primaria)
                        # Reprobado en Matemáticas (~46 pts) y Lenguaje (~48 pts), destacado en Artes/Ed.Física (~85 pts)
                        elif est.ci == '30000002':
                            if da.area.nombre == 'Matematicas':
                                factor = 0.44 + (random() * 0.05)  # ~45-48 pts (Reprobado)
                            elif da.area.nombre == 'Lenguaje y Comunicacion':
                                factor = 0.46 + (random() * 0.04)  # ~47-49 pts (Reprobado)
                            elif da.area.nombre in ('Artes Plasticas', 'Educacion Fisica'):
                                factor = 0.82 + (random() * 0.08)  # ~85-90 pts (Destacado)
                            else:
                                factor = 0.58 + (random() * 0.08)  # ~60 pts (Aprobado)
                        # 3. Alumno Sobresaliente: Gabriel Choque (1° Primaria) -> ~92 pts
                        elif est.ci == '30000006':
                            factor = 0.89 + (random() * 0.08)
                        # 4. Caso Secundaria en Riesgo: Rodrigo Quispe (1° Secundaria) -> Reprobado en Física-Química
                        elif est.ci == '30000017' and da.area.nombre == 'Fisica - Quimica':
                            factor = 0.45 + (random() * 0.05)
                        # 5. Caso Secundaria en Riesgo: Lucía Suxo (2° Secundaria) -> Reprobada en Matemáticas
                        elif est.ci == '30000048' and da.area.nombre == 'Matematicas':
                            factor = 0.44 + (random() * 0.06)
                        # 6. Estudiantes regulares con notas entre 54 y 88
                        else:
                            factor = 0.56 + (random() * 0.32)

                        nota_valor = round(Decimal(str(float(max_pts) * factor)), 2)
                        nota_valor = max(Decimal('1.00'), min(max_pts, nota_valor))

                        notas_para_crear.append(ActividadNotas(
                            actividad=act,
                            estudiante=est,
                            valor=nota_valor,
                            registrado_por=director,
                            activo=True,
                        ))

        ActividadNotas.objects.bulk_create(notas_para_crear, ignore_conflicts=True, batch_size=1000)
        self.stdout.write(f'  Actividades ({len(actividades_dict)}) y Calificaciones ({len(notas_para_crear)}) registradas en lote')

    # -------------------------------------------------------------------------
    # 15. OBSERVACIONES CUALITATIVAS DOCENTES (BOLETINES)
    # -------------------------------------------------------------------------
    def _seed_observaciones(self):
        director = Usuarios.objects.get(email='director@feya.edu.bo')
        p1 = Periodos.objects.get(numero=1, gestion=2026)
        p2 = Periodos.objects.get(numero=2, gestion=2026)

        asignaciones = list(DocenteAsignacion.objects.filter(
            gestion=2026,
            curso__paralelo__nombre='A',
        ).select_related('area', 'curso'))

        observaciones_catalogo = [
            ('EA', 'Demuestra excelente creatividad, comprensión y liderazgo colaborativo.'),
            ('A', 'Participa activamente en clases y cumple puntualmente con sus tareas.'),
            ('SA', 'Alcanzó los objetivos básicos de la materia; se sugiere reforzar la lectura comprensiva.'),
            ('PA', 'Requiere apoyo continuo en el hogar y seguimiento cercano en tareas de razonamiento.'),
        ]

        obs_para_crear = []
        for da in asignaciones:
            estudiantes = list(Estudiantes.objects.filter(
                inscripciones__curso=da.curso,
                inscripciones__gestion=2026,
            ))
            for est in estudiantes:
                if est.ci == '30000001':  # Lucas
                    indicador, obs_txt = observaciones_catalogo[0]
                elif est.ci == '30000002' and da.area.nombre in ('Matematicas', 'Lenguaje y Comunicacion'):  # Mateo en riesgo
                    indicador = 'PA'
                    obs_txt = f'Requiere apoyo urgente en el hogar en {da.area.nombre}. Dificultad para completar consignas.'
                elif est.ci == '30000002':
                    indicador, obs_txt = observaciones_catalogo[1]
                elif est.ci == '30000017' and da.area.nombre == 'Fisica - Quimica':
                    indicador = 'PA'
                    obs_txt = 'Presenta dificultades en la resolución de problemas numéricos de Física-Química.'
                elif est.ci == '30000048' and da.area.nombre == 'Matematicas':
                    indicador = 'PA'
                    obs_txt = 'Debe reforzar operaciones algebraicas y presentar prácticos pendientes.'
                else:
                    indicador, obs_txt = choice(observaciones_catalogo)

                for per in (p1, p2):
                    obs_para_crear.append(NotaObservaciones(
                        estudiante=est,
                        docente_asignacion=da,
                        periodo=per,
                        indicador=indicador,
                        observacion=obs_txt,
                        registrado_por=director,
                    ))

        NotaObservaciones.objects.bulk_create(obs_para_crear, ignore_conflicts=True, batch_size=1000)
        self.stdout.write(f'  Observaciones cualitativas de boletín OK ({len(obs_para_crear)}) en lote')

    # -------------------------------------------------------------------------
    # 16. ASISTENCIAS (TODOS LOS ESTUDIANTES Y CURSOS)
    # -------------------------------------------------------------------------
    def _seed_asistencias(self):
        regente = Usuarios.objects.get(email='regente@feya.edu.bo')

        # 30 días hábiles de asistencia
        dias = []
        cur_date = date(2026, 2, 2)
        while len(dias) < 30:
            if cur_date.weekday() < 5:
                dias.append(cur_date)
            cur_date += timedelta(days=1)

        cursos_2026 = Cursos.objects.filter(gestion=2026, paralelo__nombre='A')

        asistencias_batch = []
        for curso in cursos_2026:
            da_ref = DocenteAsignacion.objects.filter(curso=curso, gestion=2026).first()
            if not da_ref:
                continue

            estudiantes = list(Estudiantes.objects.filter(
                inscripciones__curso=curso,
                inscripciones__gestion=2026,
            ))

            for dia in dias:
                for est in estudiantes:
                    # Casos especiales de asistencia
                    if est.ci == '30000002':  # Mateo Pérez
                        if dia.day in (10, 18, 24):
                            est_val = 'ausente'
                        elif dia.day in (12, 13):
                            est_val = 'con_licencia'
                        else:
                            est_val = 'presente'
                    elif est.ci == '30000001':  # Lucas Pérez (asistencia perfecta)
                        est_val = 'presente'
                    elif est.ci == '30000004' and dia.day in (15, 16):  # Valentina Flores
                        est_val = 'con_licencia'
                    else:
                        est_val = 'presente' if random() > 0.07 else 'ausente'

                    asistencias_batch.append(Asistencias(
                        estudiante=est,
                        docente_asignacion=da_ref,
                        fecha=dia,
                        estado=est_val,
                        tipo='por_asignacion',
                        registrado_por=regente,
                        activo=True,
                    ))

        Asistencias.objects.bulk_create(asistencias_batch, ignore_conflicts=True, batch_size=1000)
        self.stdout.write(f'  Registros de asistencia OK ({len(asistencias_batch)}) para todos los cursos')

    # -------------------------------------------------------------------------
    # 17. LICENCIAS
    # -------------------------------------------------------------------------
    def _seed_licencias(self):
        regente = Usuarios.objects.get(email='regente@feya.edu.bo')
        director = Usuarios.objects.get(email='director@feya.edu.bo')

        mateo = self.estudiantes_map.get('30000002')
        tutor_perez = Tutores.objects.filter(ci='7000001').first()

        if mateo and tutor_perez:
            Licencias.objects.get_or_create(
                estudiante=mateo,
                fecha_inicio=date(2026, 2, 12),
                defaults={
                    'fecha_fin': date(2026, 2, 13),
                    'tutor_solicitante': tutor_perez,
                    'regente': regente,
                    'tipo': 'enfermedad',
                    'motivo': 'Infección estomacal aguda con reposo médico certificado.',
                    'requiere_respaldo': True,
                    'respaldo_presentado': True,
                    'adjunto_url': 'https://storage.feya.edu.bo/licencias/cert_medico_mateo_30000002.pdf',
                    'estado': 'aprobada',
                    'aprobado_por': director,
                    'aprobado_en': date(2026, 2, 12),
                    'observaciones': 'Certificado médico de la Caja Nacional de Salud verificado.',
                    'creado_por': regente,
                    'activo': True,
                },
            )

        # Licencia de Valentina Flores
        valentina = self.estudiantes_map.get('30000004')
        tutora_condori = Tutores.objects.filter(ci='7000002').first()
        if valentina and tutora_condori:
            Licencias.objects.get_or_create(
                estudiante=valentina,
                fecha_inicio=date(2026, 2, 15),
                defaults={
                    'fecha_fin': date(2026, 2, 16),
                    'tutor_solicitante': tutora_condori,
                    'regente': regente,
                    'tipo': 'personal',
                    'motivo': 'Viaje familiar urgente a Cochabamba.',
                    'requiere_respaldo': False,
                    'respaldo_presentado': False,
                    'estado': 'aprobada',
                    'aprobado_por': director,
                    'aprobado_en': date(2026, 2, 15),
                    'observaciones': 'Permiso justificado por la madre.',
                    'creado_por': regente,
                    'activo': True,
                },
            )

        self.stdout.write('  Licencias y justificaciones OK')

    # -------------------------------------------------------------------------
    # 18. NOTIFICACIONES
    # -------------------------------------------------------------------------
    def _seed_notificaciones(self):
        usr_tutor1 = Usuarios.objects.filter(ci='7000001').first()
        usr_doc1 = Usuarios.objects.filter(email='docente1@feya.edu.bo').first()

        notifs = []
        if usr_tutor1:
            notifs.extend([
                (usr_tutor1, '¡Bienvenido al Portal de Padres de Familia de la U.E. Fe y Alegría!', 'info'),
                (usr_tutor1, 'Alerta Académica: Tu hijo Mateo Pérez tiene calificaciones que requieren atención en Matemáticas y Lenguaje.', 'warning'),
            ])
        if usr_doc1:
            notifs.append((usr_doc1, 'El Primer Trimestre 2026 ha sido cerrado oficialmente por Dirección.', 'info'))

        for usr, msg, tipo in notifs:
            Notificacion.objects.get_or_create(
                usuario=usr,
                mensaje=msg,
                defaults={'tipo': tipo, 'leida': False},
            )
        self.stdout.write('  Notificaciones iniciales OK')

    # -------------------------------------------------------------------------
    # 19. RESUMEN FINAL Y CREDENCIALES DE PRUEBA
    # -------------------------------------------------------------------------
    def _imprimir_resumen(self):
        msg = """
========================================================================================
✨ SEED MASIVO Y UNIFICADO DE LA U.E. FE Y ALEGRÍA FINALIZADO CON ÉXITO ✨
========================================================================================

🔑 TODAS LAS CONTRASEÑAS POR DEFECTO: 123456

----------------------------------------------------------------------------------------
1. SISTEMA WEB - PERSONAL ADMINISTRATIVO Y DOCENTES (http://localhost:3000/login):
----------------------------------------------------------------------------------------
   • DIRECTOR:    director@feya.edu.bo   | CI: 1000001 | Clave: 123456
   • SECRETARÍA:  secretaria@feya.edu.bo | CI: 1000002 | Clave: 123456
   • REGENTE:     regente@feya.edu.bo    | CI: 1000003 | Clave: 123456

   • DOCENTES DE AULA:
     - Prof. Roberto Vargas (Matemáticas): docente1@feya.edu.bo | CI: 1000004
     - Lic. Carmen Flores (Lenguaje):       docente2@feya.edu.bo | CI: 1000005
     - Lic. Jorge Torrez (Sociales):        docente3@feya.edu.bo | CI: 1000006
     - Mgr. Ana Gutierrez (Naturales):      docente4@feya.edu.bo | CI: 1000007
     - Prof. Luis Paredes (Artes):          docente5@feya.edu.bo | CI: 1000008
     - Lic. Sandra Rojas (Ed. Física):      docente6@feya.edu.bo | CI: 1000009
     - Ing. Carlos Mendoza (Tecnología):    docente7@feya.edu.bo | CI: 1000010
     - Mgr. Mónica Huanca (Inglés):         docente8@feya.edu.bo | CI: 1000011

----------------------------------------------------------------------------------------
2. PORTAL MÓVIL PWA - PADRES DE FAMILIA (http://localhost:3000/padres/login):
   (Cualquiera de los 35 tutores puede ingresar con su CI y clave: 123456)
----------------------------------------------------------------------------------------
   ⭐ CASO 1 - MULTIHIJO COMPLETO (Primaria + Secundaria + Materias en Riesgo <51 pts):
      • Tutor: Juan Carlos Pérez Mamani
      • CI: 7000001 | Clave: 123456
      • Hijos (3):
        1. Lucas Pérez (3° Primaria A)    -> Alumno sobresaliente (88-95 pts)
        2. Mateo Pérez (1° Primaria A)    -> EN RIESGO: Matemáticas (46 pts), Lenguaje (48 pts) [<51 pts]
        3. Sofía Pérez (2° Secundaria A)  -> Rendimiento regular (72 pts)
      * Caso perfecto para probar: cambio de hijo, alertas rojas de boletín y Agente IA con Groq.

   ⭐ CASO 2 - MULTIHIJO EN PRIMARIA:
      • Tutora: Rosa María Condori Flores
      • CI: 7000002 | Clave: 123456
      • Hijas (2): Valentina Flores (2° Primaria A) y Camila Flores (4° Primaria A)

   ⭐ CASO 3 - HIJO ÚNICO SOBRESALIENTE:
      • Tutor: Luis Alberto Choque Vargas
      • CI: 7000003 | Clave: 123456
      • Hijo (1): Gabriel Choque (1° Primaria A, promedio 92 pts)

   ⭐ CASO 4 - INCLUSIÓN EDUCATIVA (Discapacidad):
      • Tutora: Elena Sofía Huanca Paco
      • CI: 7000004 | Clave: 123456
      • Hija: Daniela Huanca (1° Primaria A, estudiante con discapacidad)

   ⭐ CASO 5 - INCLUSIÓN EDUCATIVA (TEA + Hermano en Secundaria):
      • Tutor: Oscar René Tórrez Morales
      • CI: 7000005 | Clave: 123456
      • Hijos (2): Diego Tórrez (1° Primaria A, con TEA) y Carlos Tórrez (1° Secundaria A)

   ⭐ CASO 6 - MULTIHIJO EN SECUNDARIA:
      • Tutora: Patricia Rocío Colque Blanco
      • CI: 7000014 | Clave: 123456
      • Hijos (2): Victoria Colque (1° Primaria A) y Nicolás Colque (2° Secundaria A)

   • 29 TUTORES ADICIONALES TOTALMENTE FUNCIONALES:
     - CI: 7000006 al 7000035 (Todos con cuenta activa de Usuarios y clave 123456).
     - Cada uno con 1 a 2 hijos vinculados con calificaciones completas, asistencia y boletines.

----------------------------------------------------------------------------------------
3. GESTIÓN ADMINISTRATIVA DE TUTORES (DIRECTOR Y SECRETARÍA):
   - Módulo web en /tutores: Búsqueda de padres por CI o nombre, listado de hijos matriculados,
     y botón de "Restablecer Contraseña" que muestra la contraseña temporal en pantalla para
     entregar personalmente al padre de familia.
   - En /inscripcion: Si se matricula a un estudiante con un tutor nuevo, el sistema crea
     automáticamente la cuenta de usuario del tutor y entrega su CI y contraseña temporal (123456)
     en una tarjeta modal lista para copiar o imprimir.
========================================================================================
"""
        self.stdout.write(self.style.SUCCESS(msg))
