# Análisis de Soft Delete

## Modelos que YA tienen soft delete
| Modelo | Campo | Valores |
|--------|-------|---------|
| Estudiantes | estado | activo, inactivo, retirado |
| Inscripciones | estado | activo, retirado, transferido |
| Usuarios | activo | True/False (BooleanField) |
| DocenteAsignacion | activo | True/False (BooleanField) |
| Periodos | estado | pendiente, activo, cerrado |
| Licencias | estado | pendiente, aprobada, rechazada |

## Modelos que NECESITAN soft delete
| Modelo | Razón | Propuesta |
|--------|-------|-----------|
| Actividades | Notas referencian actividades via FK; hard delete perderia historial de notas | agregar `activo = BooleanField(default=True)` |
| Tutores | Tutores historicos vinculados a estudiantes via EstudianteTutor | agregar `activo = BooleanField(default=True)` |
| Asistencias | Registros de asistencia historicos | agregar `activo = BooleanField(default=True)` |

## Modelos que NO necesitan soft delete
| Modelo | Razón |
|--------|-------|
| AuditLog | Registro de auditoria inmutable, no se elimina |
| ActividadNotas | Cascade con Actividades; protegido si Actividades tiene soft delete |
| NotaObservaciones | Cascade con Estudiante/DocenteAsignacion; protegido si esos tienen soft delete |
| EstudianteTutor | Tabla puente; protegida si Estudiante/Tutor tienen soft delete |
| DimensionConfigPeriodo | Configuracion, cascade con Periodo |
| Horarios | Programaticos, se regeneran por asignacion |
| PeriodoCierreDocente | Registro de cierre inmutable |
| Roles | Datos de catalogo, rara vez eliminados |
| Niveles, Grados, Paralelos, Cursos, Areas, DimensionesEvaluacion | Datos de catalogo/referencia |

## Observaciones importantes
1. **Usuarios** ya tiene campo `activo = BooleanField(default=True)` — no requiere cambios.
2. **DocenteAsignacion** ya tiene `activo = BooleanField(default=True)` — no requiere cambios.
3. **Licencias** usa `estado` para flujo de aprobacion (pendiente/aprobada/rechazada). Si se necesita archivar licencias, puede agregarse un estado `anulada` adicional.
4. **Periodos** usa `estado` para ciclo de vida (pendiente/activo/cerrado). Un periodo cerrado no deberia eliminarse jamas.

## Recomendacion
1. Agregar campo `activo = BooleanField(default=True)` a: Actividades, Tutores, Asistencias
2. Crear endpoint `/api/restore/students/<id>/` para restaurar estudiantes
3. Los endpoints de DELETE deben hacer soft delete (set activo=False o estado='inactivo'), no hard delete
4. Los listados deben filtrar por activo=True / estado='activo' por defecto
5. Agregar query param `?incluir_inactivos=true` para administradores
6. Para Usuarios, considerar si `activo=False` debe impedir el login (revisar logica de autenticacion)
