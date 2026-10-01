import unicodedata

from django.db import models


def iniciales_usuario(nombres='', primer_apellido='', segundo_apellido=''):
    """Iniciales normalizadas (sin acentos ni simbolos) para el nombre de usuario.

    'Juan Perez Gomez' -> 'jpg'. Si no hay letras devuelve 'usr'.
    """
    letras = []
    for parte in (nombres or '', primer_apellido or '', segundo_apellido or ''):
        for caracter in unicodedata.normalize('NFKD', str(parte)):
            if caracter.isalpha() and caracter.isascii():
                letras.append(caracter.lower())
                break
    return ''.join(letras) or 'usr'


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
    OTP_METODO_CHOICES = [
        ('email', 'Codigo por correo electronico'),
        ('totp', 'Aplicacion autenticadora (TOTP)'),
    ]
    ci = models.TextField(unique=True, blank=True, null=True)
    nombre = models.TextField(blank=True, null=True)
    primer_apellido = models.TextField(blank=True, null=True)
    segundo_apellido = models.TextField(blank=True, null=True)
    email = models.TextField(unique=True)
    usuario = models.TextField(unique=True, blank=True, null=True)
    correo_personal = models.TextField(unique=True, blank=True, null=True)
    password_hash = models.TextField()
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)
    # ─ Ciclo de vida de la contrasena ───────────────────────────────────────
    # password_temporal=True -> la contrasena actual fue generada por el sistema
    # debe_cambiar_password=True -> el usuario esta obligado a cambiarla al entrar
    password_temporal = models.BooleanField(default=False)
    debe_cambiar_password = models.BooleanField(default=False)
    password_cambiada_en = models.DateTimeField(blank=True, null=True)
    # ── Autenticacion en dos pasos (2FA / OTP) ────────────────────────────────
    otp_habilitado = models.BooleanField(default=False)
    otp_metodo = models.TextField(choices=OTP_METODO_CHOICES, default='email')
    otp_secret = models.TextField(blank=True, null=True)
    otp_configurado_en = models.DateTimeField(blank=True, null=True)
    intentos_otp_fallidos = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'usuarios'

    @property
    def correo_notificaciones(self):
        """Correo al que se envian OTP, recuperacion y credenciales (personal primero)."""
        return (self.correo_personal or self.email or '').strip()

    @classmethod
    def generar_usuario_unico(cls, nombres='', primer_apellido='', segundo_apellido='', excluir_id=None):
        """Nombre de usuario unico con el patron iniciales + numero (jpg1, jpg2...)."""
        base = iniciales_usuario(nombres, primer_apellido, segundo_apellido)
        correlativo = 1
        while True:
            candidato = f'{base}{correlativo}'
            existentes = cls.objects.filter(usuario=candidato)
            if excluir_id:
                existentes = existentes.exclude(id=excluir_id)
            if not existentes.exists():
                return candidato
            correlativo += 1

    def completar_datos_acceso(self):
        """Rellena el usuario y el correo personal cuando no fueron enviados.

        Devuelve la lista de campos completados (para conservarlos si el guardado
        usa `update_fields`).
        """
        completados = []
        if not (self.usuario or '').strip():
            self.usuario = self.generar_usuario_unico(
                self.nombre, self.primer_apellido, self.segundo_apellido, excluir_id=self.pk,
            )
            completados.append('usuario')
        if not (self.correo_personal or '').strip():
            self.correo_personal = (self.email or '').strip().lower() or None
            if self.correo_personal:
                completados.append('correo_personal')
        return completados

    def save(self, *args, **kwargs):
        completados = self.completar_datos_acceso()
        update_fields = kwargs.get('update_fields')
        if completados and update_fields is not None:
            kwargs['update_fields'] = list(dict.fromkeys([*update_fields, *completados]))
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        parts = [self.nombre or '', self.primer_apellido or '', self.segundo_apellido or '']
        return ' '.join(p for p in parts if p).strip() or self.email

    def __str__(self):
        return self.nombre_completo


class CodigoVerificacion(models.Model):
    """Codigos OTP de un solo uso (login 2FA, recuperacion, activacion 2FA)."""
    PROPOSITO_CHOICES = [
        ('login', 'Inicio de sesion (2FA)'),
        ('recuperacion', 'Recuperacion de contrasena'),
        ('activar_otp', 'Activar segundo factor'),
        ('desactivar_otp', 'Desactivar segundo factor'),
        ('credenciales', 'Entrega de credenciales'),
    ]
    METODO_CHOICES = [
        ('email', 'Correo electronico'),
        ('totp', 'Aplicacion autenticadora'),
    ]
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name='codigos_verificacion')
    proposito = models.TextField(choices=PROPOSITO_CHOICES)
    metodo = models.TextField(choices=METODO_CHOICES, default='email')
    codigo_hash = models.TextField()
    enviado_a = models.TextField(blank=True, null=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    usado_en = models.DateTimeField(blank=True, null=True)
    intentos = models.IntegerField(default=0)
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'codigos_verificacion'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['usuario', 'proposito'], name='idx_codigo_usuario_prop'),
            models.Index(fields=['expira_en'], name='idx_codigo_expira'),
        ]

    @property
    def vigente(self):
        from django.utils import timezone
        return (not self.usado) and self.expira_en >= timezone.now()

    def __str__(self):
        return f'{self.get_proposito_display()} - {self.usuario_id} - {"usado" if self.usado else "vigente"}'


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
    # Cuenta de acceso del tutor. Se crea con contrasena temporal y cambio obligatorio.
    usuario = models.OneToOneField(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='tutor')
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

    @property
    def nombre_completo(self):
        parts = [self.nombres or '', self.primer_apellido or '', self.segundo_apellido or '']
        return ' '.join(p for p in parts if p).strip()

    @property
    def tiene_usuario(self):
        return self.usuario_id is not None

    @property
    def estudiantes_ids(self):
        """IDs de los estudiantes que tiene asignados este tutor."""
        try:
            return list(
                self.estudiantetutor_set.filter(activo=True).values_list('estudiante_id', flat=True)
            )
        except Exception:
            return []

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
    estado = models.TextField(choices=ESTADO_CHOICES, default='activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'estudiantes'

    @property
    def tiene_tutor(self):
        """Indica si el estudiante ya tiene al menos un tutor asignado."""
        try:
            return self.estudiantetutor_set.filter(activo=True).exists()
        except Exception:
            return False

    @property
    def tutor_principal(self):
        """Tutor principal del estudiante (o el primero activo si no hay principal)."""
        try:
            relacion = (
                self.estudiantetutor_set
                .filter(activo=True, es_principal=True)
                .select_related('tutor')
                .first()
            )
            if relacion is None:
                relacion = (
                    self.estudiantetutor_set
                    .filter(activo=True)
                    .select_related('tutor')
                    .first()
                )
        except Exception:
            return None
        return relacion.tutor if relacion else None

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
    # Usuario que registro la actividad (auditoria de notas)
    creado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='actividades_creadas')
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
    # Usuario que capturo el ultimo cambio de la nota y justificacion opcional
    registrado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='notas_registradas')
    motivo_modificacion = models.TextField(blank=True, null=True)
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
    registrado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='observaciones_registradas')
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
    TIPO_CHOICES = [
        ('enfermedad', 'Enfermedad'),
        ('personal', 'Motivo personal'),
        ('viaje', 'Viaje'),
        ('duelo', 'Duelo'),
        ('institucional', 'Actividad institucional'),
        ('otro', 'Otro'),
    ]
    estudiante = models.ForeignKey(Estudiantes, on_delete=models.CASCADE)
    tutor_solicitante = models.ForeignKey(Tutores, on_delete=models.SET_NULL, blank=True, null=True)
    regente = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='licencias_regentadas')
    tipo = models.TextField(choices=TIPO_CHOICES, default='enfermedad')
    motivo = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    requiere_respaldo = models.BooleanField(default=False)
    respaldo_presentado = models.BooleanField(default=False)
    # URL o descripcion del respaldo fisico/digital presentado
    adjunto_url = models.TextField(blank=True, null=True)
    estado = models.TextField(choices=ESTADO_CHOICES, default='pendiente')
    activo = models.BooleanField(default=True)
    aprobado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='licencias_aprobadas')
    aprobado_en = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    # Usuario que registro la solicitud de licencia
    creado_por = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, blank=True, null=True, related_name='licencias_creadas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'licencias'
        indexes = [
            models.Index(fields=['estudiante', 'estado'], name='idx_licencia_estado'),
        ]

    @property
    def dias(self):
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return 0

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
