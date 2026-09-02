from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # === CONSTRAINTS ===
        # Periodo: fecha_fin >= fecha_inicio
        migrations.RunSQL(
            "ALTER TABLE periodos ADD CONSTRAINT periodo_fecha_valida CHECK (fecha_fin >= fecha_inicio)",
            "ALTER TABLE periodos DROP CONSTRAINT IF EXISTS periodo_fecha_valida",
        ),
        # Periodo: un solo activo por gestion
        migrations.RunSQL(
            "CREATE UNIQUE INDEX un_periodo_activo_por_gestion ON periodos (gestion) WHERE estado = 'activo'",
            "DROP INDEX IF EXISTS un_periodo_activo_por_gestion",
        ),
        # Licencia: fecha_fin >= fecha_inicio
        migrations.RunSQL(
            "ALTER TABLE licencias ADD CONSTRAINT licencia_fecha_valida CHECK (fecha_fin >= fecha_inicio)",
            "ALTER TABLE licencias DROP CONSTRAINT IF EXISTS licencia_fecha_valida",
        ),
        # Licencia: aprobada requires aprobado_por
        migrations.RunSQL(
            "ALTER TABLE licencias ADD CONSTRAINT aprobacion_consistente CHECK (estado != 'aprobada' OR aprobado_por_id IS NOT NULL)",
            "ALTER TABLE licencias DROP CONSTRAINT IF EXISTS aprobacion_consistente",
        ),
        # === VISTAS SQL ===
        # v_notas_por_dimension: promedio de actividades escalado al puntaje de la dimension
        migrations.RunSQL("""
            CREATE VIEW v_notas_por_dimension AS
            SELECT
                an.estudiante_id,
                a.docente_asignacion_id,
                a.periodo_id,
                a.dimension_id,
                COUNT(an.id)                                    AS total_actividades,
                AVG(an.valor / a.puntaje_maximo * 100)          AS promedio_porcentual,
                dcp.puntaje_maximo                              AS puntaje_dimension,
                ROUND(
                    AVG(an.valor / a.puntaje_maximo * 100)
                    * dcp.puntaje_maximo / 100
                , 2)                                            AS nota_dimension
            FROM actividad_notas an
            JOIN actividades a ON a.id = an.actividad_id
            JOIN dimension_config_periodo dcp
                ON dcp.periodo_id = a.periodo_id
               AND dcp.dimension_id = a.dimension_id
            WHERE an.valor IS NOT NULL
            GROUP BY
                an.estudiante_id,
                a.docente_asignacion_id,
                a.periodo_id,
                a.dimension_id,
                dcp.puntaje_maximo
        """, "DROP VIEW IF EXISTS v_notas_por_dimension"),
        # v_nota_ser_asistencia: nota del SER calculada desde asistencia
        # NOTE: This view is replaced by migration 0012 with LATERAL join for PG 18 compatibility
        migrations.RunSQL("""
            CREATE VIEW v_nota_ser_asistencia AS
            SELECT
                a.estudiante_id,
                a.docente_asignacion_id,
                DATE_TRUNC('month', MIN(a.fecha))::DATE         AS mes,
                COUNT(*) FILTER (WHERE a.estado = 'presente')   AS clases_presente,
                COUNT(*) FILTER (WHERE a.estado != 'con_licencia') AS clases_evaluables,
                COUNT(*)                                         AS total_clases,
                0::NUMERIC                                       AS nota_ser
            FROM asistencias a
            WHERE a.tipo = 'por_asignacion'
            GROUP BY a.estudiante_id, a.docente_asignacion_id, DATE_TRUNC('month', a.fecha)::DATE
        """, "DROP VIEW IF EXISTS v_nota_ser_asistencia"),
        # v_notas_totales: suma de notas por dimension
        migrations.RunSQL("""
            CREATE VIEW v_notas_totales AS
            SELECT
                estudiante_id,
                docente_asignacion_id,
                periodo_id,
                SUM(nota_dimension)  AS nota_total,
                COUNT(dimension_id)  AS dimensiones_evaluadas
            FROM v_notas_por_dimension
            GROUP BY estudiante_id, docente_asignacion_id, periodo_id
        """, "DROP VIEW IF EXISTS v_notas_totales"),
        # === TRIGGERS ===
        # updated_at automatico para usuarios
        migrations.RunSQL("""
            CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """, "DROP FUNCTION IF EXISTS set_updated_at"),
        migrations.RunSQL("""
            CREATE TRIGGER trg_usuarios_updated_at
                BEFORE UPDATE ON usuarios
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """, "DROP TRIGGER IF EXISTS trg_usuarios_updated_at ON usuarios"),
        migrations.RunSQL("""
            CREATE TRIGGER trg_estudiantes_updated_at
                BEFORE UPDATE ON estudiantes
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """, "DROP TRIGGER IF EXISTS trg_estudiantes_updated_at ON estudiantes"),
        migrations.RunSQL("""
            CREATE TRIGGER trg_tutores_updated_at
                BEFORE UPDATE ON tutores
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """, "DROP TRIGGER IF EXISTS trg_tutores_updated_at ON tutores"),
        migrations.RunSQL("""
            CREATE TRIGGER trg_nota_obs_updated_at
                BEFORE UPDATE ON nota_observaciones
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """, "DROP TRIGGER IF EXISTS trg_nota_obs_updated_at ON nota_observaciones"),
        # === AUDIT TRIGGER FOR actividad_notas ===
        migrations.RunSQL("""
            CREATE OR REPLACE FUNCTION audit_actividad_notas()
            RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    INSERT INTO audit_log (tabla, registro_id, accion, datos_nuevo, usuario_id, fecha_cambio)
                    VALUES ('actividad_notas', NEW.id, 'INSERT', row_to_json(NEW)::jsonb,
                            current_setting('app.current_user_id', TRUE)::INTEGER, NOW());
                ELSIF TG_OP = 'UPDATE' THEN
                    INSERT INTO audit_log (tabla, registro_id, accion, datos_anterior, datos_nuevo, usuario_id, fecha_cambio)
                    VALUES ('actividad_notas', NEW.id, 'UPDATE',
                            row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb,
                            current_setting('app.current_user_id', TRUE)::INTEGER, NOW());
                ELSIF TG_OP = 'DELETE' THEN
                    INSERT INTO audit_log (tabla, registro_id, accion, datos_anterior, usuario_id, fecha_cambio)
                    VALUES ('actividad_notas', OLD.id, 'DELETE', row_to_json(OLD)::jsonb,
                            current_setting('app.current_user_id', TRUE)::INTEGER, NOW());
                END IF;
                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
        """, "DROP FUNCTION IF EXISTS audit_actividad_notas"),
        migrations.RunSQL("""
            CREATE TRIGGER trg_audit_actividad_notas
                AFTER INSERT OR UPDATE OR DELETE ON actividad_notas
                FOR EACH ROW EXECUTE FUNCTION audit_actividad_notas()
        """, "DROP TRIGGER IF EXISTS trg_audit_actividad_notas ON actividad_notas"),
    ]
