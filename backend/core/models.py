from django.db import models


class Roles(models.Model):
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class Usuarios(models.Model):
    ci = models.TextField(unique=True, blank=True, null=True)
    nombre = models.TextField(blank=True, null=True)
    primer_apellido = models.TextField(blank=True, null=True)
    segundo_apellido = models.TextField(blank=True, null=True)
    email = models.TextField(unique=True)
    password_hash = models.TextField()
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'usuarios'

    @property
    def nombre_completo(self):
        parts = [self.nombre or '', self.primer_apellido or '', self.segundo_apellido or '']
        return ' '.join(p for p in parts if p).strip() or self.email

    def __str__(self):
        return self.nombre_completo


class Docentes(models.Model):
    usuario = models.OneToOneField(Usuarios, on_delete=models.CASCADE, related_name='docente')
    titulo_academico = models.TextField(blank=True, null=True)
    especialidad = models.TextField(blank=True, null=True)
    fecha_ingreso_institucion = models.DateField(blank=True, null=True)
    anos_experiencia = models.IntegerField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'docentes'

    def __str__(self):
        return str(self.usuario)


class Niveles(models.Model):
    nombre = models.TextField(unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'niveles'

    def __str__(self):
        return self.nombre


class Grados(models.Model):
    nivel = models.ForeignKey(Niveles, on_delete=models.CASCADE)
    nombre = models.TextField()
    numero = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'grados'
        unique_together = (('nivel', 'numero'),)

    def __str__(self):
        return self.nombre


class Paralelos(models.Model):
    nombre = models.TextField(unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'paralelos'

    def __str__(self):
        return self.nombre


class Cursos(models.Model):
    grado = models.ForeignKey(Grados, on_delete=models.CASCADE)
    paralelo = models.ForeignKey(Paralelos, on_delete=models.CASCADE)
    gestion = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'cursos'
        unique_together = (('grado', 'paralelo', 'gestion'),)

    def __str__(self):
        return f'{self.grado} {self.paralelo} {self.gestion}'


class Areas(models.Model):
    nombre = models.TextField(unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'areas'

    def __str__(self):
        return self.nombre


class DimensionesEvaluacion(models.Model):
    nombre = models.TextField()
    orden = models.IntegerField()
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    gestion = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'dimensiones_evaluacion'
        unique_together = (('nombre', 'gestion'),)

    def __str__(self):
        return f'{self.nombre} {self.gestion}'


class Periodos(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('cerrado', 'Cerrado'),
    ]
    nombre = models.TextField()
    numero = models.IntegerField()
    gestion = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.TextField(choices=ESTADO_CHOICES, default='pendiente')
    activo = models.BooleanField(default=True)
    habilitado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='periodos_habilitados')
    habilitado_en = models.DateTimeField(blank=True, null=True)
    cerrado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='periodos_cerrados')
    cerrado_en = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Indicador manual para registrar que la secretaria marcó este periodo como enviado al ministerio
    marcado_como_enviado = models.BooleanField(default=False)
    enviado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='periodos_enviados')
    enviado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'periodos'
        unique_together = (('numero', 'gestion'),)

    def __str__(self):
        return f'{self.nombre} {self.gestion}'


class DimensionConfigPeriodo(models.Model):
    periodo = models.ForeignKey(Periodos, on_delete=models.CASCADE)
    dimension = models.ForeignKey(DimensionesEvaluacion, on_delete=models.CASCADE)
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = True
        db_table = 'dimension_config_periodo'
        unique_together = (('periodo', 'dimension'),)

    def __str__(self):
        return f'{self.periodo} - {self.dimension}: {self.puntaje_maximo}'


class Tutores(models.Model):
    ci = models.TextField(unique=True)
    tipo_documento = models.TextField(default='CI')
    primer_apellido = models.TextField()
    segundo_apellido = models.TextField(blank=True, null=True)
    nombres = models.TextField()
    parentesco = models.TextField(blank=True, null=True)
    celular = models.TextField(blank=True, null=True)
    idioma_frecuente = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'tutores'

    def __str__(self):
        return f'{self.nombres} {self.primer_apellido}'


class Estudiantes(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('Otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('retirado', 'Retirado'),
    ]
    rude = models.TextField(unique=True)
    ci = models.TextField(unique=True)
    primer_apellido = models.TextField()
    segundo_apellido = models.TextField(blank=True, null=True)
    nombres = models.TextField()
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.TextField(choices=GENERO_CHOICES, blank=True, null=True)
    pais_nacimiento = models.TextField(default='Bolivia')
    tiene_discapacidad = models.BooleanField(default=False)
    tipo_discapacidad = models.TextField(blank=True, null=True)
    tiene_tea = models.BooleanField(default=False)
    dificultad_aprendizaje = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='estudiante_usuario')
    estado = models.TextField(choices=ESTADO_CHOICES, default='activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'estudiantes'

    def __str__(self):
        return f'{self.nombres} {self.primer_apellido}'


class EstudianteTutor(models.Model):
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    tutor = models.ForeignKey(Tutores, on_delete=models.CASCADE)
    es_principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'estudiante_tutor'
        unique_together = (('estudiante', 'tutor'),)


class Inscripciones(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('retirado', 'Retirado'),
        ('transferido', 'Transferido'),
    ]
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE)
    gestion = models.IntegerField()
    fecha_inscripcion = models.DateField(auto_now_add=True)
    estado = models.TextField(choices=ESTADO_CHOICES, default='activo')
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'inscripciones'
        constraints = [
            models.UniqueConstraint(fields=['estudiante', 'gestion'], condition=models.Q(activo=True), name='un_inscripcion_activa'),
        ]
        indexes = [
            models.Index(fields=['estudiante', 'gestion'], name='idx_insc_est_gestion'),
        ]

    def __str__(self):
        return f'{self.estudiante} - {self.curso} {self.gestion}'


class DocenteAsignacion(models.Model):
    docente = models.ForeignKey('Docentes', on_delete=models.CASCADE)
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE)
    area = models.ForeignKey(Areas, on_delete=models.CASCADE)
    gestion = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'docente_asignacion'
        unique_together = (('curso', 'area', 'gestion'),)

    @property
    def usuario(self):
        return self.docente.usuario if self.docente_id else None

    def __str__(self):
        return f'{self.docente} - {self.area} - {self.curso}'


class Actividades(models.Model):
    docente_asignacion = models.ForeignKey(DocenteAsignacion, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodos, on_delete=models.CASCADE)
    dimension = models.ForeignKey(DimensionesEvaluacion, on_delete=models.CASCADE)
    nombre = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_actividad = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'actividades'

    def __str__(self):
        return f'{self.nombre} ({self.dimension})'


class ActividadNotas(models.Model):
    actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    registrado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'actividad_notas'
        unique_together = (('actividad', 'estudiante'),)
        indexes = [
            models.Index(fields=['estudiante'], name='idx_notas_estudiante'),
        ]


class NotaObservaciones(models.Model):
    INDICADOR_CHOICES = [
        ('PA', 'PA'),
        ('SA', 'SA'),
        ('A', 'A'),
        ('EA', 'EA'),
    ]
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    docente_asignacion = models.ForeignKey(DocenteAsignacion, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodos, on_delete=models.CASCADE)
    indicador = models.TextField(choices=INDICADOR_CHOICES, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'nota_observaciones'
        unique_together = (('estudiante', 'docente_asignacion', 'periodo'),)


class Asistencias(models.Model):
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('con_licencia', 'Con Licencia'),
    ]
    TIPO_CHOICES = [
        ('administrativa', 'Administrativa'),
        ('por_asignacion', 'Por Asignación'),
    ]
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    docente_asignacion = models.ForeignKey(DocenteAsignacion, on_delete=models.SET_NULL, blank=True, null=True)
    fecha = models.DateField()
    estado = models.TextField(choices=ESTADO_CHOICES, default='presente')
    tipo = models.TextField(choices=TIPO_CHOICES, default='administrativa')
    registrado_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'asistencias'
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante', 'docente_asignacion', 'fecha', 'tipo'],
                condition=models.Q(docente_asignacion__isnull=False),
                name='un_asistencia_por_asignacion',
            ),
            models.UniqueConstraint(
                fields=['estudiante', 'fecha', 'tipo'],
                condition=models.Q(docente_asignacion__isnull=True),
                name='un_asistencia_administrativa',
            ),
        ]

    def __str__(self):
        return f'{self.estudiante} - {self.fecha} - {self.estado}'


class Licencias(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    tutor_solicitante = models.ForeignKey(Tutores, on_delete=models.SET_NULL, blank=True, null=True)
    regente = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='licencias_regentadas')
    motivo = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    requiere_respaldo = models.BooleanField(default=False)
    respaldo_presentado = models.BooleanField(default=False)
    estado = models.TextField(choices=ESTADO_CHOICES, default='pendiente')
    activo = models.BooleanField(default=True)
    aprobado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='licencias_aprobadas')
    aprobado_en = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'licencias'

    def __str__(self):
        return f'Licencia {self.estudiante} ({self.fecha_inicio} - {self.fecha_fin})'


class PeriodoCierreDocente(models.Model):
    periodo = models.ForeignKey(Periodos, on_delete=models.CASCADE)
    docente_asignacion = models.ForeignKey(DocenteAsignacion, on_delete=models.CASCADE)
    cerrado_por = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name='cierres_realizados')
    cerrado_en = models.DateTimeField(auto_now_add=True)
    reabierto_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='cierres_reabiertos')
    reabierto_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'periodo_cierre_docente'
        unique_together = (('periodo', 'docente_asignacion'),)


class Horarios(models.Model):
    DIAS_CHOICES = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
    ]
    docente_asignacion = models.ForeignKey(DocenteAsignacion, on_delete=models.CASCADE)
    dia_semana = models.IntegerField(choices=DIAS_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    aula = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'horarios'

    def __str__(self):
        return f'{self.docente_asignacion} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}'


class AuditLog(models.Model):
    tabla = models.TextField()
    registro_id = models.BigIntegerField(null=True, blank=True)
    accion = models.TextField()
    datos_anterior = models.JSONField(blank=True, null=True)
    datos_nuevo = models.JSONField(blank=True, null=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'audit_log'
        indexes = [
            models.Index(fields=['tabla', 'registro_id']),
            models.Index(fields=['usuario']),
            models.Index(fields=['fecha_cambio']),
        ]

    def __str__(self):
        return f'{self.accion} en {self.tabla}#{self.registro_id}'


class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('info', 'Informativo'),
        ('warning', 'Advertencia'),
        ('alert', 'Alerta'),
    ]
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.TextField(choices=TIPO_CHOICES, default='info')
    leida = models.BooleanField(default=False)
    link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'notificaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.tipo}] {self.mensaje[:60]}'


class ExportEvent(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True)
    periodo = models.ForeignKey(Periodos, on_delete=models.SET_NULL, blank=True, null=True)
    docente_asignacion_id = models.BigIntegerField(blank=True, null=True)
    formato = models.TextField()  # 'xlsx' or 'docx'
    filtros = models.JSONField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'export_event'

    def __str__(self):
        return f'Export {self.formato} periodo={self.periodo} usuario={self.usuario}'


class ConfiguracionEscuela(models.Model):
    nombre = models.TextField(default='Unidad Educativa')
    direccion = models.TextField(blank=True, default='')
    telefono = models.TextField(blank=True, default='')
    email = models.TextField(blank=True, default='')
    ciudad = models.TextField(blank=True, default='')
    gestion_actual = models.IntegerField(blank=True, null=True)
    escala_aprobacion = models.DecimalField(max_digits=5, decimal_places=2, default=51.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'configuracion_escuela'

    def __str__(self):
        return self.nombre


class TokenBlacklist(models.Model):
    token = models.TextField(unique=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'token_blacklist'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expira_en']),
        ]

    def __str__(self):
        return f'Blacklisted token for {self.usuario}'


class AccessLog(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, blank=True, null=True)
    path = models.TextField()
    method = models.TextField()
    ip_address = models.TextField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    status_code = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'access_log'
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['path']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.usuario or "Anonymous"} - {self.method} {self.path} at {self.created_at}'
