"""Registro de todas las tablas del sistema en el panel de administracion Django.

Permite listar, buscar, filtrar, crear, editar y eliminar registros de cada
modelo de la app `core` desde `/admin/`, sin pasar por la API.

Nota: el admin usa la autenticacion de Django (`django.contrib.auth`), por lo
que requiere un superusuario creado con `python manage.py createsuperuser`.
Las contrasenas de los usuarios del sistema (`Usuarios.password_hash`) se
cifran con PBKDF2 al guardarlas desde este panel.
"""
from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from .models import (
    AccessLog,
    ActividadNotas,
    Actividades,
    Asistencias,
    Areas,
    AuditLog,
    CodigoVerificacion,
    ConfiguracionEscuela,
    Cursos,
    DimensionConfigPeriodo,
    DimensionesEvaluacion,
    DocenteAsignacion,
    Docentes,
    Estudiantes,
    EstudianteTutor,
    ExportEvent,
    Grados,
    Horarios,
    Inscripciones,
    Licencias,
    Niveles,
    NotaObservaciones,
    Notificacion,
    Paralelos,
    PeriodoCierreDocente,
    Periodos,
    Roles,
    TokenBlacklist,
    Tutores,
    Usuarios,
)

# ── Identidad del panel ───────────────────────────────────────────────────────
admin.site.site_header = 'U.E. Fe y Alegria - Administracion'
admin.site.site_title = 'U.E. Fe y Alegria'
admin.site.index_title = 'Tablas del sistema'
admin.site.empty_value_display = '—'


class BaseModelAdmin(admin.ModelAdmin):
    """Configuracion comun a todos los administradores del sistema.

    Marca como solo lectura los campos que maneja la base de datos o el sistema
    (created_at, updated_at, fecha_cambio, etc.) para no romper la trazabilidad.
    """
    campos_automaticos = ('created_at', 'updated_at')
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        nombres = {campo.name for campo in self.model._meta.fields}
        for campo in self.campos_automaticos:
            if campo in nombres and campo not in readonly:
                readonly.append(campo)
        return readonly


# ── Inlines ───────────────────────────────────────────────────────────────────

class EstudianteTutorInline(admin.TabularInline):
    """Tutores asignados a un estudiante (desde la ficha del estudiante)."""
    model = EstudianteTutor
    extra = 1
    autocomplete_fields = ('tutor',)
    fields = ('tutor', 'es_principal', 'activo')


class TutorEstudianteInline(admin.TabularInline):
    """Estudiantes a cargo de un tutor (desde la ficha del tutor)."""
    model = EstudianteTutor
    fk_name = 'tutor'
    extra = 1
    autocomplete_fields = ('estudiante',)
    fields = ('estudiante', 'es_principal', 'activo')


class DimensionConfigPeriodoInline(admin.TabularInline):
    """Puntaje maximo de cada dimension dentro de un periodo."""
    model = DimensionConfigPeriodo
    extra = 1
    autocomplete_fields = ('dimension',)
    fields = ('dimension', 'puntaje_maximo')


class ActividadNotasInline(admin.TabularInline):
    """Notas capturadas para una actividad."""
    model = ActividadNotas
    extra = 1
    autocomplete_fields = ('estudiante', 'registrado_por')
    fields = ('estudiante', 'valor', 'registrado_por', 'motivo_modificacion', 'activo')


class HorariosInline(admin.TabularInline):
    """Bloques de horario de una asignacion docente."""
    model = Horarios
    extra = 1
    fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'aula', 'activo')


# ── Usuarios, roles y seguridad ───────────────────────────────────────────────

class UsuarioAdminForm(forms.ModelForm):
    """Formulario de `Usuarios` que recibe la contrasena en texto plano.

    La API guarda `password_hash` con `make_password` (PBKDF2); este formulario
    hace lo mismo para que las credenciales creadas/actualizadas desde el admin
    sigan funcionando en el login del sistema.
    """
    password_plano = forms.CharField(
        label='Contrasena',
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Se almacena cifrada (PBKDF2). Obligatoria al crear el usuario; '
                  'dejar vacia al editar para conservar la contrasena actual.',
    )

    class Meta:
        model = Usuarios
        exclude = ('password_hash',)

    def clean_password_plano(self):
        valor = (self.cleaned_data.get('password_plano') or '').strip()
        if valor and len(valor) < 6:
            raise forms.ValidationError('La contrasena debe tener al menos 6 caracteres.')
        return valor

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk is None and not cleaned.get('password_plano'):
            self.add_error('password_plano', 'Debes definir una contrasena para el nuevo usuario.')
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password_plano = (self.cleaned_data.get('password_plano') or '').strip()
        if password_plano:
            usuario.password_hash = make_password(password_plano)
            usuario.password_cambiada_en = timezone.now()
        if commit:
            usuario.save()
            self.save_m2m()
        return usuario


@admin.register(Usuarios)
class UsuariosAdmin(BaseModelAdmin):
    form = UsuarioAdminForm
    list_display = ('id', 'usuario', 'email', 'correo_personal', 'nombre_completo', 'rol',
                    'activo', 'otp_habilitado', 'last_login')
    list_display_links = ('id', 'usuario', 'email')
    list_editable = ('activo',)
    list_filter = ('activo', 'rol', 'otp_habilitado', 'otp_metodo', 'password_temporal', 'debe_cambiar_password')
    search_fields = ('usuario', 'email', 'correo_personal', 'nombre', 'primer_apellido',
                     'segundo_apellido', 'ci')
    autocomplete_fields = ('rol',)
    list_select_related = ('rol',)
    date_hierarchy = 'created_at'
    ordering = ('email',)
    readonly_fields = ('password_cambiada_en', 'last_login', 'created_at', 'updated_at')
    fieldsets = (
        ('Datos personales', {
            'fields': ('ci', 'nombre', 'primer_apellido', 'segundo_apellido'),
        }),
        ('Identificadores de acceso', {
            'fields': ('usuario', 'email', 'correo_personal'),
            'description': 'El correo personal es obligatorio y no se puede repetir: ahi se envian '
                           'las credenciales, los codigos de verificacion (2FA) y la recuperacion de '
                           'contrasena. Si dejas el usuario vacio se genera con las iniciales '
                           'y un numero (jpg1, jpg2...).',
        }),
        ('Acceso y contrasena', {
            'fields': ('password_plano', 'rol', 'activo', 'password_temporal', 'debe_cambiar_password'),
            'description': 'La contrasena se cifra con PBKDF2, igual que en la API. '
                           'Marca "debe cambiar password" para forzar el cambio en el primer ingreso.',
        }),
        ('Autenticacion en dos pasos (2FA)', {
            'fields': ('otp_habilitado', 'otp_metodo', 'otp_secret', 'otp_configurado_en', 'intentos_otp_fallidos'),
            'classes': ('collapse',),
        }),
        ('Auditoria', {
            'fields': ('password_cambiada_en', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Roles)
class RolesAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'nombre', 'descripcion', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(CodigoVerificacion)
class CodigoVerificacionAdmin(BaseModelAdmin):
    campos_automaticos = ('created_at',)
    list_display = ('id', 'usuario', 'proposito', 'metodo', 'enviado_a', 'usado', 'intentos', 'expira_en', 'created_at')
    list_filter = ('proposito', 'metodo', 'usado')
    search_fields = ('usuario__email', 'enviado_a', 'ip_address', 'codigo_hash')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('codigo_hash', 'created_at')

    def has_add_permission(self, request):
        # Los codigos OTP los genera y cifra la API; aqui solo se consultan o limpian.
        return False


@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(BaseModelAdmin):
    campos_automaticos = ('creado_en',)
    list_display = ('id', 'usuario', 'creado_en', 'expira_en')
    list_filter = ('creado_en', 'expira_en')
    search_fields = ('usuario__email', 'token')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)
    readonly_fields = ('token', 'creado_en')

    def has_add_permission(self, request):
        # El token lo escribe la API al cerrar sesion; aqui solo se consulta o purga.
        return False


@admin.register(AccessLog)
class AccessLogAdmin(BaseModelAdmin):
    campos_automaticos = ('created_at',)
    list_display = ('id', 'usuario', 'method', 'path', 'status_code', 'ip_address', 'created_at')
    list_filter = ('method', 'status_code')
    search_fields = ('usuario__email', 'path', 'ip_address', 'user_agent')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


# ── Docentes, niveles y cursos ────────────────────────────────────────────────

@admin.register(Docentes)
class DocentesAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'usuario', 'titulo_academico', 'especialidad', 'anos_experiencia', 'activo')
    list_editable = ('activo',)
    list_filter = ('activo', 'especialidad')
    search_fields = ('usuario__email', 'usuario__nombre', 'usuario__primer_apellido', 'titulo_academico', 'especialidad')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)


# ── Catalogos academicos (niveles, grados, paralelos, cursos, areas) ──────────

@admin.register(Niveles)
class NivelesAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'nombre', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    list_filter = ('activo',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Grados)
class GradosAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'nombre', 'numero', 'nivel', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    list_filter = ('nivel', 'activo')
    search_fields = ('nombre', 'nivel__nombre')
    autocomplete_fields = ('nivel',)
    list_select_related = ('nivel',)
    ordering = ('nivel__nombre', 'numero')


@admin.register(Paralelos)
class ParalelosAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'nombre', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    list_filter = ('activo',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Cursos)
class CursosAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'grado', 'paralelo', 'gestion', 'activo')
    list_display_links = ('id', 'grado')
    list_editable = ('activo',)
    list_filter = ('gestion', 'grado__nivel', 'paralelo', 'activo')
    search_fields = ('grado__nombre', 'paralelo__nombre', 'gestion')
    autocomplete_fields = ('grado', 'paralelo')
    list_select_related = ('grado', 'paralelo')
    ordering = ('-gestion', 'grado__numero', 'paralelo__nombre')


@admin.register(Areas)
class AreasAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'nombre', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    list_filter = ('activo',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(DimensionesEvaluacion)
class DimensionesEvaluacionAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'nombre', 'orden', 'puntaje_maximo', 'gestion', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('orden', 'activo')
    list_filter = ('gestion', 'activo')
    search_fields = ('nombre',)
    ordering = ('-gestion', 'orden')


# ── Periodos y configuracion de dimensiones ───────────────────────────────────

@admin.register(Periodos)
class PeriodosAdmin(BaseModelAdmin):
    campos_automaticos = ('created_at',)
    list_display = ('id', 'nombre', 'numero', 'gestion', 'estado', 'fecha_inicio', 'fecha_fin',
                    'activo', 'marcado_como_enviado')
    list_display_links = ('id', 'nombre')
    list_editable = ('estado', 'activo', 'marcado_como_enviado')
    list_filter = ('estado', 'gestion', 'activo', 'marcado_como_enviado')
    search_fields = ('nombre', 'gestion')
    autocomplete_fields = ('habilitado_por', 'cerrado_por', 'enviado_por')
    date_hierarchy = 'fecha_inicio'
    ordering = ('-gestion', 'numero')
    inlines = (DimensionConfigPeriodoInline,)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Datos del periodo', {
            'fields': ('nombre', 'numero', 'gestion', 'fecha_inicio', 'fecha_fin', 'estado', 'activo'),
        }),
        ('Trazabilidad', {
            'fields': ('habilitado_por', 'habilitado_en', 'cerrado_por', 'cerrado_en',
                       'marcado_como_enviado', 'enviado_por', 'enviado_en', 'created_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(DimensionConfigPeriodo)
class DimensionConfigPeriodoAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'periodo', 'dimension', 'puntaje_maximo')
    list_display_links = ('id', 'periodo')
    list_editable = ('puntaje_maximo',)
    list_filter = ('periodo', 'dimension')
    search_fields = ('periodo__nombre', 'dimension__nombre')
    autocomplete_fields = ('periodo', 'dimension')
    list_select_related = ('periodo', 'dimension')
    ordering = ('-periodo__gestion', 'dimension__orden')


# ── Tutores y estudiantes ─────────────────────────────────────────────────────

@admin.register(Tutores)
class TutoresAdmin(BaseModelAdmin):
    list_display = ('id', 'ci', 'nombre_completo', 'parentesco', 'celular', 'usuario', 'activo')
    list_display_links = ('id', 'ci')
    list_editable = ('activo',)
    list_filter = ('activo', 'parentesco', 'tipo_documento')
    search_fields = ('ci', 'nombres', 'primer_apellido', 'segundo_apellido', 'celular', 'usuario__email')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    inlines = (TutorEstudianteInline,)
    ordering = ('primer_apellido', 'nombres')


@admin.register(Estudiantes)
class EstudiantesAdmin(BaseModelAdmin):
    list_display = ('id', 'rude', 'ci', 'nombre_completo_estudiante', 'genero', 'estado')
    list_display_links = ('id', 'rude')
    list_filter = ('estado', 'genero', 'tiene_discapacidad', 'tiene_tea', 'pais_nacimiento')
    search_fields = ('rude', 'ci', 'nombres', 'primer_apellido', 'segundo_apellido')
    inlines = (EstudianteTutorInline,)
    ordering = ('primer_apellido', 'nombres')
    fieldsets = (
        ('Identificacion', {
            'fields': ('rude', 'ci', 'nombres', 'primer_apellido', 'segundo_apellido',
                       'fecha_nacimiento', 'genero', 'pais_nacimiento', 'estado'),
        }),
        ('Necesidades educativas', {
            'fields': ('tiene_discapacidad', 'tipo_discapacidad', 'tiene_tea', 'dificultad_aprendizaje'),
            'classes': ('collapse',),
        }),
        ('Auditoria', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Nombre completo', ordering='primer_apellido')
    def nombre_completo_estudiante(self, obj):
        return f'{obj.nombres} {obj.primer_apellido}'


@admin.register(EstudianteTutor)
class EstudianteTutorAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'estudiante', 'tutor', 'es_principal', 'activo')
    list_display_links = ('id', 'estudiante')
    list_editable = ('es_principal', 'activo')
    list_filter = ('activo', 'es_principal')
    search_fields = ('estudiante__nombres', 'estudiante__primer_apellido', 'estudiante__rude',
                     'tutor__nombres', 'tutor__primer_apellido', 'tutor__ci')
    autocomplete_fields = ('estudiante', 'tutor')
    list_select_related = ('estudiante', 'tutor')


# ── Inscripciones, asignaciones y horarios ────────────────────────────────────

@admin.register(Inscripciones)
class InscripcionesAdmin(BaseModelAdmin):
    campos_automaticos = ('fecha_inscripcion',)
    list_display = ('id', 'estudiante', 'curso', 'gestion', 'estado', 'fecha_inscripcion', 'activo')
    list_display_links = ('id', 'estudiante')
    list_editable = ('estado', 'activo')
    list_filter = ('estado', 'gestion', 'activo')
    search_fields = ('estudiante__nombres', 'estudiante__primer_apellido', 'estudiante__rude', 'curso__grado__nombre')
    autocomplete_fields = ('estudiante', 'curso')
    list_select_related = ('estudiante', 'curso')
    date_hierarchy = 'fecha_inscripcion'
    ordering = ('-gestion', 'estudiante__primer_apellido')
    readonly_fields = ('fecha_inscripcion',)


@admin.register(DocenteAsignacion)
class DocenteAsignacionAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'docente', 'area', 'curso', 'gestion', 'activo')
    list_display_links = ('id', 'docente')
    list_editable = ('activo',)
    list_filter = ('gestion', 'area', 'curso__grado__nivel', 'activo')
    search_fields = ('docente__usuario__email', 'docente__usuario__nombre', 'area__nombre',
                     'curso__grado__nombre', 'curso__paralelo__nombre')
    autocomplete_fields = ('docente', 'curso', 'area')
    list_select_related = ('docente', 'curso', 'area')
    inlines = (HorariosInline,)
    ordering = ('-gestion', 'curso__grado__numero')


@admin.register(Horarios)
class HorariosAdmin(BaseModelAdmin):
    campos_automaticos = ()
    list_display = ('id', 'docente_asignacion', 'dia_semana', 'hora_inicio', 'hora_fin', 'aula', 'activo')
    list_display_links = ('id', 'docente_asignacion')
    list_editable = ('activo',)
    list_filter = ('dia_semana', 'activo')
    search_fields = ('docente_asignacion__docente__usuario__email', 'aula')
    autocomplete_fields = ('docente_asignacion',)
    list_select_related = ('docente_asignacion',)
    ordering = ('dia_semana', 'hora_inicio')


# ── Actividades, notas y observaciones ────────────────────────────────────────

@admin.register(Actividades)
class ActividadesAdmin(BaseModelAdmin):
    campos_automaticos = ('created_at',)
    list_display = ('id', 'nombre', 'docente_asignacion', 'periodo', 'dimension',
                    'puntaje_maximo', 'fecha_actividad', 'creado_por', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    list_filter = ('periodo', 'dimension', 'fecha_actividad', 'activo')
    search_fields = ('nombre', 'descripcion', 'docente_asignacion__docente__usuario__email')
    autocomplete_fields = ('docente_asignacion', 'periodo', 'dimension', 'creado_por')
    list_select_related = ('docente_asignacion', 'periodo', 'dimension', 'creado_por')
    date_hierarchy = 'fecha_actividad'
    ordering = ('-fecha_actividad', 'nombre')
    inlines = (ActividadNotasInline,)
    readonly_fields = ('created_at',)


@admin.register(ActividadNotas)
class ActividadNotasAdmin(BaseModelAdmin):
    campos_automaticos = ('registrado_en', 'modificado_en')
    list_display = ('id', 'actividad', 'estudiante', 'valor', 'registrado_por', 'modificado_en', 'activo')
    list_display_links = ('id', 'actividad')
    list_editable = ('valor', 'activo')
    list_filter = ('activo', 'actividad__periodo', 'actividad__dimension')
    search_fields = ('estudiante__nombres', 'estudiante__primer_apellido', 'estudiante__rude',
                     'actividad__nombre', 'motivo_modificacion')
    autocomplete_fields = ('actividad', 'estudiante', 'registrado_por')
    list_select_related = ('actividad', 'estudiante', 'registrado_por')
    date_hierarchy = 'registrado_en'
    ordering = ('-registrado_en',)
    readonly_fields = ('registrado_en', 'modificado_en')


@admin.register(NotaObservaciones)
class NotaObservacionesAdmin(BaseModelAdmin):
    list_display = ('id', 'estudiante', 'docente_asignacion', 'periodo', 'indicador',
                    'registrado_por', 'updated_at')
    list_display_links = ('id', 'estudiante')
    list_filter = ('periodo', 'indicador')
    search_fields = ('estudiante__nombres', 'estudiante__primer_apellido', 'estudiante__rude',
                     'observacion', 'docente_asignacion__area__nombre')
    autocomplete_fields = ('estudiante', 'docente_asignacion', 'periodo', 'registrado_por')
    list_select_related = ('estudiante', 'docente_asignacion', 'periodo', 'registrado_por')
    ordering = ('-updated_at',)


# ── Asistencias, licencias y cierres ──────────────────────────────────────────

@admin.register(Asistencias)
class AsistenciasAdmin(BaseModelAdmin):
    campos_automaticos = ('created_at',)
    list_display = ('id', 'estudiante', 'fecha', 'estado', 'tipo', 'docente_asignacion',
                    'registrado_por', 'activo')
    list_display_links = ('id', 'estudiante')
    list_editable = ('estado', 'activo')
    list_filter = ('estado', 'tipo', 'fecha', 'activo')
    search_fields = ('estudiante__nombres', 'estudiante__primer_apellido', 'estudiante__rude')
    autocomplete_fields = ('estudiante', 'docente_asignacion', 'registrado_por')
    list_select_related = ('estudiante', 'docente_asignacion', 'registrado_por')
    date_hierarchy = 'fecha'
    ordering = ('-fecha', 'estudiante__primer_apellido')
    readonly_fields = ('created_at',)


@admin.register(Licencias)
class LicenciasAdmin(BaseModelAdmin):
    list_display = ('id', 'estudiante', 'tipo', 'fecha_inicio', 'fecha_fin', 'dias',
                    'estado', 'tutor_solicitante', 'aprobado_por', 'activo')
    list_display_links = ('id', 'estudiante')
    list_editable = ('estado', 'activo')
    list_filter = ('estado', 'tipo', 'activo', 'requiere_respaldo', 'respaldo_presentado')
    search_fields = ('estudiante__nombres', 'estudiante__primer_apellido', 'estudiante__rude',
                     'motivo', 'tutor_solicitante__ci')
    autocomplete_fields = ('estudiante', 'tutor_solicitante', 'regente', 'aprobado_por', 'creado_por')
    list_select_related = ('estudiante', 'tutor_solicitante', 'aprobado_por')
    date_hierarchy = 'fecha_inicio'
    ordering = ('-fecha_inicio',)
    fieldsets = (
        ('Solicitud', {
            'fields': ('estudiante', 'tutor_solicitante', 'tipo', 'motivo',
                       'fecha_inicio', 'fecha_fin', 'requiere_respaldo', 'respaldo_presentado',
                       'adjunto_url', 'creado_por'),
        }),
        ('Resolucion', {
            'fields': ('estado', 'regente', 'aprobado_por', 'aprobado_en', 'observaciones', 'activo'),
        }),
        ('Auditoria', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Dias', ordering='fecha_inicio')
    def dias(self, obj):
        return obj.dias


@admin.register(PeriodoCierreDocente)
class PeriodoCierreDocenteAdmin(BaseModelAdmin):
    campos_automaticos = ('cerrado_en',)
    list_display = ('id', 'periodo', 'docente_asignacion', 'cerrado_por', 'cerrado_en',
                    'reabierto_por', 'reabierto_en')
    list_display_links = ('id', 'periodo')
    list_filter = ('periodo', 'cerrado_en', 'reabierto_en')
    search_fields = ('periodo__nombre', 'docente_asignacion__docente__usuario__email')
    autocomplete_fields = ('periodo', 'docente_asignacion', 'cerrado_por', 'reabierto_por')
    list_select_related = ('periodo', 'docente_asignacion', 'cerrado_por', 'reabierto_por')
    date_hierarchy = 'cerrado_en'
    ordering = ('-cerrado_en',)
    readonly_fields = ('cerrado_en',)


# ── Auditoria, notificaciones y sistema ───────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(BaseModelAdmin):
    campos_automaticos = ('fecha_cambio',)
    list_display = ('id', 'tabla', 'registro_id', 'accion', 'usuario', 'fecha_cambio')
    list_filter = ('tabla', 'accion', 'fecha_cambio')
    search_fields = ('tabla', 'accion', 'usuario__email')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    date_hierarchy = 'fecha_cambio'
    ordering = ('-fecha_cambio',)
    readonly_fields = ('fecha_cambio',)


@admin.register(Notificacion)
class NotificacionAdmin(BaseModelAdmin):
    campos_automaticos = ('created_at',)
    list_display = ('id', 'usuario', 'tipo', 'leida', 'mensaje_corto', 'link', 'created_at')
    list_display_links = ('id', 'usuario')
    list_editable = ('leida',)
    list_filter = ('tipo', 'leida', 'created_at')
    search_fields = ('usuario__email', 'mensaje', 'link')
    autocomplete_fields = ('usuario',)
    list_select_related = ('usuario',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    @admin.display(description='Mensaje')
    def mensaje_corto(self, obj):
        texto = obj.mensaje or ''
        return texto if len(texto) <= 60 else f'{texto[:60]}...'


@admin.register(ExportEvent)
class ExportEventAdmin(BaseModelAdmin):
    campos_automaticos = ('creado_en',)
    list_display = ('id', 'usuario', 'periodo', 'formato', 'docente_asignacion_id', 'creado_en')
    list_display_links = ('id', 'usuario')
    list_filter = ('formato', 'creado_en')
    search_fields = ('usuario__email', 'formato')
    autocomplete_fields = ('usuario', 'periodo')
    list_select_related = ('usuario', 'periodo')
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)
    readonly_fields = ('creado_en',)


@admin.register(ConfiguracionEscuela)
class ConfiguracionEscuelaAdmin(BaseModelAdmin):
    list_display = ('id', 'nombre', 'ciudad', 'telefono', 'email', 'gestion_actual',
                    'escala_aprobacion', 'updated_at')
    list_display_links = ('id', 'nombre')
    list_filter = ('gestion_actual',)
    search_fields = ('nombre', 'ciudad', 'email')
    ordering = ('id',)

    def has_add_permission(self, request):
        # El servicio (`ConfigService.obtener`) trabaja siempre con el registro id=1,
        # por lo que solo se permite un unico registro de configuracion.
        return not ConfiguracionEscuela.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
