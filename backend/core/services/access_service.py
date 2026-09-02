from ..models import DocenteAsignacion, EstudianteTutor, Inscripciones
from ..tracing import trace_service_class


@trace_service_class
class AccessControlService:
    """Centraliza todas las verificaciones de permisos por rol."""

    ROL_DIRECTOR = 'director'
    ROL_SECRETARIA = 'secretaria'
    ROL_DOCENTE = 'docente'
    ROL_REGENTE = 'regente'
    ROL_TUTOR = 'tutor'

    ROLES_ADMIN = {ROL_DIRECTOR, ROL_SECRETARIA}
    ROLES_LECTURA_TOTAL = {ROL_DIRECTOR, ROL_SECRETARIA, ROL_REGENTE}

    def get_role_name(self, usuario):
        if usuario is None:
            return None
        return usuario.rol.nombre if usuario.rol else None

    def es_director(self, usuario):
        return self.get_role_name(usuario) == self.ROL_DIRECTOR

    def es_secretaria(self, usuario):
        return self.get_role_name(usuario) == self.ROL_SECRETARIA

    def es_docente(self, usuario):
        return self.get_role_name(usuario) == self.ROL_DOCENTE

    def es_regente(self, usuario):
        return self.get_role_name(usuario) == self.ROL_REGENTE

    def es_tutor(self, usuario):
        return self.get_role_name(usuario) == self.ROL_TUTOR

    def es_admin(self, usuario):
        return self.get_role_name(usuario) in self.ROLES_ADMIN

    def puede_ver_todo(self, usuario):
        """Puede ver datos de cualquier curso/estudiante."""
        return self.get_role_name(usuario) in self.ROLES_LECTURA_TOTAL

    def puede_editar_notas(self, usuario, docente_asignacion_id=None):
        """Puede ver los datos del curso (lectura). Director/secretaria pueden ver."""
        if self.es_admin(usuario):
            return True
        if self.es_docente(usuario):
            if docente_asignacion_id is None:
                return True
            return self._es_docente_asignado(usuario, docente_asignacion_id)
        return False

    def puede_editar_notas_libremente(self, usuario, docente_asignacion_id=None):
        """Solo el docente asignado puede crear/editar actividades y asistencia."""
        if self.es_docente(usuario):
            if docente_asignacion_id is None:
                return True
            return self._es_docente_asignado(usuario, docente_asignacion_id)
        return False

    def puede_cerrar_periodo(self, usuario):
        return self.es_director(usuario) or self.es_secretaria(usuario)

    def puede_cerrar_propio_periodo(self, usuario, docente_asignacion_id):
        """El docente puede cerrar su propia asignacion si es el asignado."""
        if self.es_director(usuario) or self.es_secretaria(usuario):
            return True
        return self._es_docente_asignado(usuario, docente_asignacion_id)

    def puede_habilitar_periodo(self, usuario):
        return self.es_director(usuario)

    def puede_gestionar_usuarios(self, usuario):
        return self.es_admin(usuario)

    def puede_gestionar_inscripciones(self, usuario):
        return self.es_secretaria(usuario)

    def puede_gestionar_licencias(self, usuario):
        return self.es_regente(usuario) or self.es_secretaria(usuario)

    def puede_aprobar_licencia_directa(self, usuario, dias):
        """Licencias de 1-3 dias puede aprobarlas la regente sola."""
        if self.es_secretaria(usuario) or self.es_director(usuario):
            return True
        if self.es_regente(usuario):
            return dias <= 3
        return False

    def puede_ver_auditoria(self, usuario):
        return self.es_director(usuario) or self.es_secretaria(usuario)

    def puede_exportar(self, usuario):
        return self.es_admin(usuario) or self.es_docente(usuario)

    def puede_modificar_notas_con_motivo(self, usuario):
        return self.es_director(usuario)

    def _es_docente_asignado(self, usuario, docente_asignacion_id):
        return DocenteAsignacion.objects.filter(
            id=docente_asignacion_id,
            docente__usuario=usuario,
            activo=True,
        ).exists()

    def get_cursos_asignados(self, usuario):
        """IDs de cursos que tiene asignados un docente."""
        return list(
            DocenteAsignacion.objects
            .filter(docente__usuario=usuario, activo=True)
            .values_list('curso_id', flat=True)
            .distinct()
        )

    def get_asignaciones_docente(self, usuario):
        """QuerySet de DocenteAsignacion para un docente."""
        return DocenteAsignacion.objects.filter(docente__usuario=usuario, activo=True)

    def get_estudiantes_ids_por_asignacion(self, docente_asignacion_id):
        da = DocenteAsignacion.objects.get(id=docente_asignacion_id)
        return list(
            Inscripciones.objects
            .filter(curso=da.curso, gestion=da.gestion, estado='activo')
            .values_list('estudiante_id', flat=True)
        )

    def get_estudiantes_ids_docente(self, usuario):
        """Obtiene IDs de estudiantes que están en los cursos del docente."""
        asignaciones = self.get_asignaciones_docente(usuario)
        if not asignaciones:
            return []
        
        curso_ids = [da.curso_id for da in asignaciones]
        gestiones = [da.gestion for da in asignaciones]
        
        return list(
            Inscripciones.objects
            .filter(curso_id__in=curso_ids, gestion__in=gestiones, estado='activo')
            .values_list('estudiante_id', flat=True)
            .distinct()
        )

    def get_estudiantes_ids_tutor(self, usuario):
        """Obtiene IDs de estudiantes que son hijos del tutor."""
        # Primero buscamos si el usuario tiene un registro en Tutores
        from ..models import Tutores
        try:
            tutor = Tutores.objects.get(ci=usuario.ci, activo=True)
        except Tutores.DoesNotExist:
            return []
        
        return list(
            EstudianteTutor.objects
            .filter(tutor=tutor, activo=True)
            .values_list('estudiante_id', flat=True)
        )

    def get_estudiantes_autorizados(self, usuario):
        """Obtiene los IDs de estudiantes que el usuario está autorizado a ver."""
        if self.puede_ver_todo(usuario):
            return None  # None significa todos
        
        if self.es_docente(usuario):
            return self.get_estudiantes_ids_docente(usuario)
        
        if self.es_tutor(usuario):
            return self.get_estudiantes_ids_tutor(usuario)
        
        return []  # No autorizado a ver nada
