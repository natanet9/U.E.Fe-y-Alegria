"""
Comando: python manage.py seed_full

Puebla todas las tablas principales con 15-20 registros de datos de muestra
realistas para la U.E. Fe y Alegria.

Uso:
    python manage.py seed_full           # Agrega datos (no borra los existentes)
    python manage.py seed_full --flush   # Borra todo y vuelve a crear
"""
from datetime import date, timedelta
from decimal import Decimal
from random import choice, randint, seed as random_seed

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Actividades, ActividadNotas, Areas, Asistencias, Cursos,
    DimensionConfigPeriodo, DimensionesEvaluacion, DocenteAsignacion,
    Docentes, Estudiantes, EstudianteTutor, Grados, Horarios,
    Inscripciones, Licencias, Niveles, Paralelos,
    Periodos, Roles, Tutores, Usuarios,
)

PASSWORD_DEMO = make_password("Demo2026!")


class Command(BaseCommand):
    help = "Puebla todas las tablas con 15-20 datos demo realistas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Elimina todos los datos antes de sembrar",
        )

    def handle(self, *args, **options):
        random_seed(2026)
        if options["flush"]:
            self._flush()
        with transaction.atomic():
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
            self._seed_tutores()
            self._seed_estudiantes()
            self._seed_estudiante_tutor()
            self._seed_inscripciones()
            self._seed_docente_asignaciones()
            self._seed_actividades()
            self._seed_notas()
            self._seed_asistencias()
            self._seed_horarios()
            self._seed_licencias()
        self.stdout.write(self.style.SUCCESS("\n  seed_full completado exitosamente"))

    def _flush(self):
        from core.models import (
            ActividadNotas, Asistencias, Horarios, Actividades, Licencias,
            EstudianteTutor, Inscripciones, DocenteAsignacion,
            DimensionConfigPeriodo, Periodos, Docentes, Cursos, Grados,
            Estudiantes, Tutores, Niveles, Paralelos, Areas,
            DimensionesEvaluacion, Usuarios, Roles,
        )
        for m in [ActividadNotas, Asistencias, Horarios, Actividades, Licencias,
                  EstudianteTutor, Inscripciones, DocenteAsignacion,
                  DimensionConfigPeriodo, Periodos, Docentes, Cursos, Grados,
                  Estudiantes, Tutores, Niveles, Paralelos, Areas,
                  DimensionesEvaluacion, Usuarios, Roles]:
            m.objects.all().delete()
        self.stdout.write("  datos anteriores eliminados")

    def _seed_roles(self):
        for nombre, desc in [
            ("director",   "Director de la unidad educativa"),
            ("secretaria", "Personal administrativo"),
            ("docente",    "Maestro o maestra de area"),
            ("regente",    "Regente de disciplina"),
            ("tutor",      "Padre, madre o tutor legal"),
        ]:
            Roles.objects.get_or_create(nombre=nombre, defaults={"descripcion": desc})
        self.stdout.write("  roles OK")

    def _seed_niveles(self):
        for n in ("Inicial", "Primario", "Secundario"):
            Niveles.objects.get_or_create(nombre=n)
        self.stdout.write("  niveles OK")

    def _seed_grados(self):
        datos = [
            ("Inicial",    "Primero de Inicial",       1),
            ("Inicial",    "Segundo de Inicial",        2),
            ("Primario",   "Primero de Primaria",       1),
            ("Primario",   "Segundo de Primaria",       2),
            ("Primario",   "Tercero de Primaria",       3),
            ("Primario",   "Cuarto de Primaria",        4),
            ("Primario",   "Quinto de Primaria",        5),
            ("Primario",   "Sexto de Primaria",         6),
            ("Secundario", "Primero de Secundaria",     1),
            ("Secundario", "Segundo de Secundaria",     2),
            ("Secundario", "Tercero de Secundaria",     3),
            ("Secundario", "Cuarto de Secundaria",      4),
            ("Secundario", "Quinto de Secundaria",      5),
            ("Secundario", "Sexto de Secundaria",       6),
        ]
        for nivel_n, nombre, numero in datos:
            nivel = Niveles.objects.get(nombre=nivel_n)
            Grados.objects.get_or_create(nivel=nivel, numero=numero, defaults={"nombre": nombre})
        self.stdout.write("  grados OK (14)")

    def _seed_paralelos(self):
        for p in ("A", "B", "C", "D", "E"):
            Paralelos.objects.get_or_create(nombre=p)
        self.stdout.write("  paralelos OK")

    def _seed_areas(self):
        for nombre in [
            "Matematicas", "Lenguaje y Comunicacion", "Ciencias Sociales",
            "Ciencias Naturales", "Artes Plasticas", "Educacion Fisica",
            "Tecnica Tecnologica", "Educacion Musical",
            "Valores, Espiritualidad y Religiones", "Ingles",
        ]:
            Areas.objects.get_or_create(nombre=nombre)
        self.stdout.write("  areas OK (10)")

    def _seed_dimensiones(self):
        for gestion in (2025, 2026):
            for nombre, orden, pts in [
                ("SER", 1, Decimal("10.00")),
                ("SABER", 2, Decimal("45.00")),
                ("HACER", 3, Decimal("40.00")),
                ("AUTOEVALUACION", 4, Decimal("5.00")),
            ]:
                DimensionesEvaluacion.objects.get_or_create(
                    nombre=nombre, gestion=gestion,
                    defaults={"orden": orden, "puntaje_maximo": pts},
                )
        self.stdout.write("  dimensiones OK (8)")

    def _seed_usuarios(self):
        rol_map = {r.nombre: r for r in Roles.objects.all()}
        datos = [
            ("director@feya.edu.bo",       "Mario",    "Condori",    "Quispe",    "director"),
            ("secretaria@feya.edu.bo",     "Silvia",   "Mamani",     "Flores",    "secretaria"),
            ("regente@feya.edu.bo",        "Patricia", "Vargas",     "Huanca",    "regente"),
            ("doc.matematicas@feya.edu.bo","Roberto",  "Quispe",     "Choque",    "docente"),
            ("doc.lenguaje@feya.edu.bo",   "Carmen",   "Flores",     "Morales",   "docente"),
            ("doc.sociales@feya.edu.bo",   "Jorge",    "Torrez",     "Ramos",     "docente"),
            ("doc.naturales@feya.edu.bo",  "Ana",      "Gutierrez",  "Cruz",      "docente"),
            ("doc.artes@feya.edu.bo",      "Luis",     "Paredes",    "Mamani",    "docente"),
            ("doc.fisica@feya.edu.bo",     "Sandra",   "Rojas",      "Condori",   "docente"),
            ("doc.tecnica@feya.edu.bo",    "Carlos",   "Mendoza",    "Aguilar",   "docente"),
            ("doc.musica@feya.edu.bo",     "Elena",    "Cardenas",   "Loza",      "docente"),
            ("doc.valores@feya.edu.bo",    "Hector",   "Zeballos",   "Paco",      "docente"),
            ("doc.ingles@feya.edu.bo",     "Monica",   "Huanca",     "Vargas",    "docente"),
            ("director2@feya.edu.bo",      "Roberto",  "Salazar",    "Nina",      "director"),
            ("secretaria2@feya.edu.bo",    "Luisa",    "Ponce",      "Rios",      "secretaria"),
        ]
        for email, nombre, p_ap, s_ap, rol_n in datos:
            Usuarios.objects.get_or_create(
                email=email,
                defaults=dict(
                    nombre=nombre, primer_apellido=p_ap, segundo_apellido=s_ap,
                    password_hash=PASSWORD_DEMO, rol=rol_map[rol_n], activo=True,
                ),
            )
        self.stdout.write("  usuarios OK (15)")

    def _seed_cursos(self):
        combos = [
            ("Primario",   1, "A"), ("Primario",   1, "B"), ("Primario",   2, "A"),
            ("Primario",   3, "A"), ("Primario",   4, "A"), ("Primario",   5, "A"),
            ("Primario",   6, "A"), ("Secundario", 1, "A"), ("Secundario", 2, "A"),
            ("Secundario", 3, "A"), ("Secundario", 4, "A"), ("Secundario", 5, "A"),
            ("Secundario", 6, "A"), ("Inicial",    1, "A"), ("Inicial",    2, "A"),
        ]
        for nivel_n, grado_num, paralelo_n in combos:
            grado = Grados.objects.get(nivel__nombre=nivel_n, numero=grado_num)
            paralelo = Paralelos.objects.get(nombre=paralelo_n)
            Cursos.objects.get_or_create(grado=grado, paralelo=paralelo, gestion=2026)
        self.stdout.write("  cursos OK (15)")

    def _seed_docentes(self):
        pares = [
            ("doc.matematicas@feya.edu.bo", "Lic.", "Matematicas"),
            ("doc.lenguaje@feya.edu.bo",    "Prof.", "Lenguaje"),
            ("doc.sociales@feya.edu.bo",    "Lic.", "Ciencias Sociales"),
            ("doc.naturales@feya.edu.bo",   "Mgr.", "Ciencias Naturales"),
            ("doc.artes@feya.edu.bo",       "Prof.", "Artes Plasticas"),
            ("doc.fisica@feya.edu.bo",      "Lic.", "Educacion Fisica"),
            ("doc.tecnica@feya.edu.bo",     "Ing.", "Tecnica Tecnologica"),
            ("doc.musica@feya.edu.bo",      "Prof.", "Musica"),
            ("doc.valores@feya.edu.bo",     "Lic.", "Etica y Valores"),
            ("doc.ingles@feya.edu.bo",      "Mgr.", "Ingles"),
        ]
        for i, (email, titulo, esp) in enumerate(pares):
            u = Usuarios.objects.get(email=email)
            Docentes.objects.get_or_create(
                usuario=u,
                defaults=dict(
                    titulo_academico=titulo, especialidad=esp,
                    fecha_ingreso_institucion=date(2010 + i, (i % 11) + 1, 1),
                    anos_experiencia=5 + i * 2,
                ),
            )
        self.stdout.write("  docentes OK (10)")

    def _seed_periodos(self):
        director = Usuarios.objects.filter(email="director@feya.edu.bo").first()
        for gestion in (2025, 2026):
            trims = [
                (1, "Primer Trimestre",  date(gestion, 2, 1),  date(gestion, 4, 30), "cerrado"),
                (2, "Segundo Trimestre", date(gestion, 5, 1),  date(gestion, 8, 31), "activo"),
                (3, "Tercer Trimestre",  date(gestion, 9, 1),  date(gestion, 11, 30),"pendiente"),
            ]
            for numero, nombre, f_ini, f_fin, estado in trims:
                Periodos.objects.get_or_create(
                    numero=numero, gestion=gestion,
                    defaults=dict(
                        nombre=nombre, fecha_inicio=f_ini, fecha_fin=f_fin,
                        estado=estado,
                        habilitado_por=director if estado != "pendiente" else None,
                    ),
                )
        self.stdout.write("  periodos OK (6)")

    def _seed_dimension_config(self):
        puntajes = {"SER": 10, "SABER": 45, "HACER": 40, "AUTOEVALUACION": 5}
        for periodo in Periodos.objects.all():
            for dim_n, pts in puntajes.items():
                dim = DimensionesEvaluacion.objects.filter(nombre=dim_n, gestion=periodo.gestion).first()
                if dim:
                    DimensionConfigPeriodo.objects.get_or_create(
                        periodo=periodo, dimension=dim, defaults={"puntaje_maximo": pts},
                    )
        self.stdout.write("  dimension_config_periodo OK")

    def _seed_tutores(self):
        datos = [
            ("2001001","Juan Carlos","Quispe","Mamani","padre","71100001"),
            ("2001002","Rosa Maria","Condori","Flores","madre","71100002"),
            ("2001003","Luis Alberto","Choque","Vargas","padre","71100003"),
            ("2001004","Elena Sofia","Huanca","Paco","madre","71100004"),
            ("2001005","Oscar Rene","Torrez","Morales","padre","71100005"),
            ("2001006","Carla Patricia","Ramos","Gutierrez","madre","71100006"),
            ("2001007","Pedro Antonio","Zeballos","Cruz","padre","71100007"),
            ("2001008","Sonia Beatriz","Paredes","Rojas","madre","71100008"),
            ("2001009","Miguel Angel","Mendoza","Cardenas","padre","71100009"),
            ("2001010","Diana Carolina","Loza","Aguilar","madre","71100010"),
            ("2001011","Carlos Eduardo","Mamani","Quispe","padre","71100011"),
            ("2001012","Maria Isabel","Flores","Condori","madre","71100012"),
            ("2001013","Jorge Luis","Morales","Choque","padre","71100013"),
            ("2001014","Patricia Elena","Vargas","Huanca","madre","71100014"),
            ("2001015","Roberto Carlos","Gutierrez","Torrez","padre","71100015"),
            ("2001016","Silvia Roxana","Cruz","Zeballos","madre","71100016"),
            ("2001017","Fernando Jose","Aguilar","Paredes","padre","71100017"),
            ("2001018","Alejandra Ruth","Rojas","Mendoza","madre","71100018"),
        ]
        for ci, nombres, p_ap, s_ap, parentesco, celular in datos:
            Tutores.objects.get_or_create(
                ci=ci,
                defaults=dict(
                    nombres=nombres, primer_apellido=p_ap, segundo_apellido=s_ap,
                    parentesco=parentesco, celular=celular, idioma_frecuente="Espanol",
                    fecha_nacimiento=date(1978, 3, 15),
                ),
            )
        self.stdout.write("  tutores OK (18)")

    def _seed_estudiantes(self):
        apellidos = [
            "Quispe","Mamani","Flores","Condori","Choque","Huanca","Paco","Vargas",
            "Morales","Ramos","Gutierrez","Torrez","Zeballos","Cruz","Paredes",
            "Rojas","Mendoza","Cardenas","Loza","Aguilar",
        ]
        nombres_m = ["Juan","Carlos","Luis","Pedro","Miguel","Oscar","Jorge","Fernando",
                     "Roberto","Diego","Andres","Mateo","Sebastian","Nicolas","Alejandro",
                     "Gabriel","Samuel","Daniel","David","Marco"]
        nombres_f = ["Maria","Rosa","Elena","Ana","Carla","Sonia","Diana","Patricia",
                     "Silvia","Alejandra","Valeria","Sofia","Isabella","Emma","Lucia",
                     "Camila","Paula","Andrea","Valentina","Natalia"]
        for i in range(1, 21):
            genero = "M" if i % 2 == 1 else "F"
            ci = f"300{i:05d}"
            rude = f"RUD2026{i:04d}"
            nom = nombres_m[i - 1] if genero == "M" else nombres_f[i - 1]
            Estudiantes.objects.get_or_create(
                ci=ci,
                defaults=dict(
                    rude=rude, nombres=nom,
                    primer_apellido=apellidos[i - 1],
                    segundo_apellido=apellidos[(i + 5) % 20],
                    genero=genero,
                    fecha_nacimiento=date(2013 + (i % 4), (i % 11) + 1, (i % 28) + 1),
                    pais_nacimiento="Bolivia", estado="activo",
                    tiene_discapacidad=(i == 7), tiene_tea=(i == 13),
                ),
            )
        self.stdout.write("  estudiantes OK (20)")

    def _seed_estudiante_tutor(self):
        tutores = list(Tutores.objects.all())
        for i, est in enumerate(Estudiantes.objects.all()):
            tutor = tutores[i % len(tutores)]
            EstudianteTutor.objects.get_or_create(
                estudiante=est, tutor=tutor, defaults={"es_principal": True},
            )
            if i % 3 == 0 and len(tutores) > 1:
                tutor2 = tutores[(i + 1) % len(tutores)]
                if tutor2 != tutor:
                    EstudianteTutor.objects.get_or_create(
                        estudiante=est, tutor=tutor2, defaults={"es_principal": False},
                    )
        self.stdout.write("  estudiante_tutor OK")

    def _seed_inscripciones(self):
        curso = Cursos.objects.filter(
            grado__nivel__nombre="Primario", grado__numero=1,
            paralelo__nombre="A", gestion=2026,
        ).first()
        if not curso:
            return
        for est in Estudiantes.objects.all():
            Inscripciones.objects.get_or_create(
                estudiante=est, gestion=2026,
                defaults={"curso": curso, "estado": "activo"},
            )
        self.stdout.write("  inscripciones OK (20)")

    def _seed_docente_asignaciones(self):
        curso = Cursos.objects.filter(
            grado__nivel__nombre="Primario", grado__numero=1,
            paralelo__nombre="A", gestion=2026,
        ).first()
        if not curso:
            return
        pares = [
            ("doc.matematicas@feya.edu.bo", "Matematicas"),
            ("doc.lenguaje@feya.edu.bo",    "Lenguaje y Comunicacion"),
            ("doc.sociales@feya.edu.bo",    "Ciencias Sociales"),
            ("doc.naturales@feya.edu.bo",   "Ciencias Naturales"),
            ("doc.artes@feya.edu.bo",       "Artes Plasticas"),
            ("doc.fisica@feya.edu.bo",      "Educacion Fisica"),
            ("doc.tecnica@feya.edu.bo",     "Tecnica Tecnologica"),
            ("doc.musica@feya.edu.bo",      "Educacion Musical"),
            ("doc.valores@feya.edu.bo",     "Valores, Espiritualidad y Religiones"),
            ("doc.ingles@feya.edu.bo",      "Ingles"),
        ]
        for email, area_n in pares:
            docente = Docentes.objects.filter(usuario__email=email).first()
            area = Areas.objects.filter(nombre=area_n).first()
            if docente and area:
                DocenteAsignacion.objects.get_or_create(
                    curso=curso, area=area, gestion=2026, defaults={"docente": docente},
                )
        self.stdout.write("  docente_asignacion OK (10)")

    def _seed_actividades(self):
        periodo = Periodos.objects.filter(numero=2, gestion=2026).first()
        if not periodo:
            return
        dims = list(DimensionesEvaluacion.objects.filter(gestion=2026))
        plan = {
            "Matematicas":                          ["Suma y resta","Multiplicacion","Division","Fracciones"],
            "Lenguaje y Comunicacion":              ["Comprension lectora","Redaccion","Ortografia","Exposicion oral"],
            "Ciencias Sociales":                    ["Mapa politico","Historia Bolivia","Civismo"],
            "Ciencias Naturales":                   ["El cuerpo humano","Los seres vivos","Medio ambiente"],
            "Artes Plasticas":                      ["Dibujo libre","Pintura acuarela","Collage"],
            "Educacion Fisica":                     ["Calentamiento","Deporte colectivo","Coordinacion motora"],
            "Tecnica Tecnologica":                  ["Manualidades","Proyecto tecnologico"],
            "Educacion Musical":                    ["Ritmo y compas","Canciones folcloricas"],
            "Valores, Espiritualidad y Religiones": ["Valores en familia","Solidaridad"],
            "Ingles":                               ["Alphabet","Colors and numbers","Greetings"],
        }
        idx = 0
        for area_n, nombres in plan.items():
            da = DocenteAsignacion.objects.filter(area__nombre=area_n, gestion=2026).first()
            if not da:
                continue
            for nombre in nombres:
                dim = dims[idx % len(dims)]
                Actividades.objects.get_or_create(
                    docente_asignacion=da, periodo=periodo, nombre=nombre,
                    defaults=dict(
                        dimension=dim, descripcion=f"{nombre} - {area_n}",
                        puntaje_maximo=Decimal("20.00"),
                        fecha_actividad=date(2026, 5, 1 + (idx % 28)),
                    ),
                )
                idx += 1
        self.stdout.write(f"  actividades OK ({idx})")

    def _seed_notas(self):
        director = Usuarios.objects.filter(email="director@feya.edu.bo").first()
        actividades = list(Actividades.objects.all())
        estudiantes = list(Estudiantes.objects.all())
        notas = []
        for act in actividades:
            for est in estudiantes:
                if not ActividadNotas.objects.filter(actividad=act, estudiante=est).exists():
                    notas.append(ActividadNotas(
                        actividad=act, estudiante=est,
                        valor=Decimal(str(randint(8, 20))),
                        registrado_por=director,
                    ))
        ActividadNotas.objects.bulk_create(notas, ignore_conflicts=True)
        self.stdout.write(f"  notas OK ({len(notas)})")

    def _seed_asistencias(self):
        director = Usuarios.objects.filter(email="director@feya.edu.bo").first()
        asignaciones = list(DocenteAsignacion.objects.filter(gestion=2026))
        estudiantes = list(Estudiantes.objects.all())
        dias = []
        d = date(2026, 5, 4)
        while len(dias) < 5:
            if d.weekday() < 5:
                dias.append(d)
            d += timedelta(days=1)
        estados = ["presente"] * 7 + ["ausente", "con_licencia"]
        total = 0
        for da in asignaciones:
            for dia in dias:
                for est in estudiantes:
                    if not Asistencias.objects.filter(
                        estudiante=est, docente_asignacion=da, fecha=dia
                    ).exists():
                        Asistencias.objects.create(
                            estudiante=est, docente_asignacion=da, fecha=dia,
                            estado=choice(estados), tipo="por_asignacion",
                            registrado_por=director,
                        )
                        total += 1
        self.stdout.write(f"  asistencias OK ({total})")

    def _seed_horarios(self):
        schedule = [
            ("Matematicas",1,"07:30","08:15","Aula 101"),
            ("Matematicas",3,"07:30","08:15","Aula 101"),
            ("Lenguaje y Comunicacion",1,"08:15","09:00","Aula 102"),
            ("Lenguaje y Comunicacion",2,"07:30","08:15","Aula 102"),
            ("Ciencias Sociales",2,"08:15","09:00","Aula 103"),
            ("Ciencias Sociales",4,"07:30","08:15","Aula 103"),
            ("Ciencias Naturales",3,"08:15","09:00","Aula 104"),
            ("Ciencias Naturales",5,"07:30","08:15","Aula 104"),
            ("Artes Plasticas",4,"08:15","09:00","Aula 105"),
            ("Artes Plasticas",5,"09:00","09:45","Aula 105"),
            ("Educacion Fisica",1,"09:00","09:45","Cancha"),
            ("Educacion Fisica",3,"09:00","09:45","Cancha"),
            ("Tecnica Tecnologica",2,"09:00","09:45","Taller"),
            ("Tecnica Tecnologica",4,"09:00","09:45","Taller"),
            ("Educacion Musical",1,"10:00","10:45","Aula Musica"),
            ("Educacion Musical",5,"10:00","10:45","Aula Musica"),
            ("Valores, Espiritualidad y Religiones",2,"10:00","10:45","Aula 106"),
            ("Valores, Espiritualidad y Religiones",4,"10:45","11:30","Aula 106"),
            ("Ingles",3,"10:00","10:45","Lab Idiomas"),
            ("Ingles",5,"10:45","11:30","Lab Idiomas"),
        ]
        total = 0
        for area_n, dia, h_ini, h_fin, aula in schedule:
            da = DocenteAsignacion.objects.filter(area__nombre=area_n, gestion=2026).first()
            if da and not Horarios.objects.filter(
                docente_asignacion=da, dia_semana=dia, hora_inicio=h_ini
            ).exists():
                Horarios.objects.create(
                    docente_asignacion=da, dia_semana=dia,
                    hora_inicio=h_ini, hora_fin=h_fin, aula=aula,
                )
                total += 1
        self.stdout.write(f"  horarios OK ({total})")

    def _seed_licencias(self):
        regente  = Usuarios.objects.filter(email="regente@feya.edu.bo").first()
        director = Usuarios.objects.filter(email="director@feya.edu.bo").first()
        estudiantes = list(Estudiantes.objects.all())
        tutores     = list(Tutores.objects.all())
        tipos   = ["enfermedad","personal","viaje","duelo","institucional","otro"]
        estados = ["pendiente","aprobada","rechazada"]
        total = 0
        for i in range(15):
            est    = estudiantes[i % len(estudiantes)]
            tutor  = tutores[i % len(tutores)]
            tipo   = tipos[i % len(tipos)]
            estado = estados[i % len(estados)]
            f_ini  = date(2026, 5, 1 + i)
            f_fin  = f_ini + timedelta(days=randint(1, 3))
            from core.models import Licencias
            Licencias.objects.get_or_create(
                estudiante=est, fecha_inicio=f_ini,
                defaults=dict(
                    tutor_solicitante=tutor, regente=regente,
                    tipo=tipo, motivo=f"Licencia {tipo} #{i+1}",
                    fecha_fin=f_fin, estado=estado,
                    aprobado_por=director if estado == "aprobada" else None,
                    creado_por=regente,
                ),
            )
            total += 1
        self.stdout.write(f"  licencias OK ({total})")
