from django.db import migrations


def apply_custom_sql(apps, schema_editor):
    vendor = schema_editor.connection.vendor

    if vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            # 1. Constraints
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'periodo_fecha_valida') THEN
                        ALTER TABLE periodos ADD CONSTRAINT periodo_fecha_valida CHECK (fecha_fin >= fecha_inicio);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'licencia_fecha_valida') THEN
                        ALTER TABLE licencias ADD CONSTRAINT licencia_fecha_valida CHECK (fecha_fin >= fecha_inicio);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'aprobacion_consistente') THEN
                        ALTER TABLE licencias ADD CONSTRAINT aprobacion_consistente CHECK (estado != 'aprobada' OR aprobado_por_id IS NOT NULL);
                    END IF;
                END $$;
            """)

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS un_periodo_activo_por_gestion
                ON periodos (gestion) WHERE estado = 'activo';
            """)

            cursor.execute("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'configuracion_escuela') THEN
                        EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS unica_fila_configuracion ON configuracion_escuela ((1))';
                    END IF;
                END $$;
            """)

            # 2. Views
            cursor.execute("""
                CREATE OR REPLACE VIEW v_notas_por_dimension AS
                SELECT
                    an.estudiante_id,
                    a.docente_asignacion_id,
                    a.periodo_id,
                    a.dimension_id,
                    COUNT(an.id) AS total_actividades,
                    AVG(an.valor / a.puntaje_maximo * 100) AS promedio_porcentual,
                    COALESCE(dcp.puntaje_maximo, de.puntaje_maximo, 0) AS puntaje_dimension,
                    ROUND(
                        AVG(an.valor / a.puntaje_maximo * 100)
                        * COALESCE(dcp.puntaje_maximo, de.puntaje_maximo, 0) / 100
                    , 2) AS nota_dimension
                FROM actividad_notas an
                JOIN actividades a ON a.id = an.actividad_id
                JOIN dimensiones_evaluacion de ON de.id = a.dimension_id
                LEFT JOIN dimension_config_periodo dcp
                    ON dcp.periodo_id = a.periodo_id
                   AND dcp.dimension_id = a.dimension_id
                WHERE an.valor IS NOT NULL
                  AND an.activo = TRUE
                  AND a.activo = TRUE
                  AND a.puntaje_maximo > 0
                GROUP BY
                    an.estudiante_id,
                    a.docente_asignacion_id,
                    a.periodo_id,
                    a.dimension_id,
                    COALESCE(dcp.puntaje_maximo, de.puntaje_maximo, 0);
            """)

            cursor.execute("""
                CREATE OR REPLACE VIEW v_notas_totales AS
                SELECT
                    estudiante_id,
                    docente_asignacion_id,
                    periodo_id,
                    SUM(nota_dimension) AS nota_total,
                    COUNT(dimension_id) AS dimensiones_evaluadas
                FROM v_notas_por_dimension
                GROUP BY estudiante_id, docente_asignacion_id, periodo_id;
            """)

            cursor.execute("""
                CREATE OR REPLACE VIEW v_nota_ser_asistencia AS
                SELECT
                    sq.estudiante_id,
                    sq.docente_asignacion_id,
                    sq.mes,
                    sq.clases_presente,
                    sq.clases_evaluables,
                    sq.total_clases,
                    ROUND(
                        sq.clases_presente::NUMERIC
                        / NULLIF(sq.clases_evaluables, 0)
                        * COALESCE(dcp.puntaje_maximo, 0)
                    , 2) AS nota_ser
                FROM (
                    SELECT
                        a.estudiante_id,
                        a.docente_asignacion_id,
                        DATE_TRUNC('month', a.fecha)::DATE AS mes,
                        COUNT(*) FILTER (WHERE a.estado = 'presente') AS clases_presente,
                        COUNT(*) FILTER (WHERE a.estado != 'con_licencia') AS clases_evaluables,
                        COUNT(*) AS total_clases,
                        MIN(a.fecha) AS min_fecha
                    FROM asistencias a
                    WHERE a.tipo = 'por_asignacion'
                    GROUP BY a.estudiante_id, a.docente_asignacion_id, DATE_TRUNC('month', a.fecha)::DATE
                ) sq
                LEFT JOIN LATERAL (
                    SELECT dcp.puntaje_maximo
                    FROM dimension_config_periodo dcp
                    JOIN periodos p ON p.id = dcp.periodo_id
                    WHERE dcp.dimension_id = (
                        SELECT id FROM dimensiones_evaluacion
                        WHERE nombre = 'SER' AND gestion = EXTRACT(YEAR FROM sq.min_fecha)::int
                    )
                    AND sq.min_fecha BETWEEN p.fecha_inicio AND p.fecha_fin
                    LIMIT 1
                ) dcp ON true;
            """)

            # 3. Triggers
            cursor.execute("""
                CREATE OR REPLACE FUNCTION set_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)

            for tabla in ['usuarios', 'estudiantes', 'tutores', 'nota_observaciones']:
                cursor.execute(f"""
                    DROP TRIGGER IF EXISTS trg_{tabla}_updated_at ON {tabla};
                    CREATE TRIGGER trg_{tabla}_updated_at
                        BEFORE UPDATE ON {tabla}
                        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
                """)

            cursor.execute("""
                CREATE OR REPLACE FUNCTION audit_actividad_notas()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF TG_OP = 'INSERT' THEN
                        INSERT INTO audit_log (tabla, registro_id, accion, datos_nuevo, usuario_id, fecha_cambio)
                        VALUES ('actividad_notas', NEW.id, 'INSERT', row_to_json(NEW)::jsonb,
                                NULLIF(current_setting('app.current_user_id', TRUE), '')::BIGINT, NOW());
                    ELSIF TG_OP = 'UPDATE' THEN
                        INSERT INTO audit_log (tabla, registro_id, accion, datos_anterior, datos_nuevo, usuario_id, fecha_cambio)
                        VALUES ('actividad_notas', NEW.id, 'UPDATE',
                                row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb,
                                NULLIF(current_setting('app.current_user_id', TRUE), '')::BIGINT, NOW());
                    ELSIF TG_OP = 'DELETE' THEN
                        INSERT INTO audit_log (tabla, registro_id, accion, datos_anterior, usuario_id, fecha_cambio)
                        VALUES ('actividad_notas', OLD.id, 'DELETE', row_to_json(OLD)::jsonb,
                                NULLIF(current_setting('app.current_user_id', TRUE), '')::BIGINT, NOW());
                    END IF;
                    RETURN COALESCE(NEW, OLD);
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS trg_audit_actividad_notas ON actividad_notas;
                CREATE TRIGGER trg_audit_actividad_notas
                    AFTER INSERT OR UPDATE OR DELETE ON actividad_notas
                    FOR EACH ROW EXECUTE FUNCTION audit_actividad_notas();
            """)

    elif vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_notas_por_dimension AS
                SELECT
                    an.estudiante_id,
                    a.docente_asignacion_id,
                    a.periodo_id,
                    a.dimension_id,
                    COUNT(an.id) AS total_actividades,
                    AVG(an.valor * 1.0 / a.puntaje_maximo * 100) AS promedio_porcentual,
                    COALESCE(dcp.puntaje_maximo, de.puntaje_maximo, 0) AS puntaje_dimension,
                    ROUND(
                        AVG(an.valor * 1.0 / a.puntaje_maximo * 100)
                        * COALESCE(dcp.puntaje_maximo, de.puntaje_maximo, 0) / 100
                    , 2) AS nota_dimension
                FROM actividad_notas an
                JOIN actividades a ON a.id = an.actividad_id
                JOIN dimensiones_evaluacion de ON de.id = a.dimension_id
                LEFT JOIN dimension_config_periodo dcp
                    ON dcp.periodo_id = a.periodo_id
                   AND dcp.dimension_id = a.dimension_id
                WHERE an.valor IS NOT NULL
                  AND an.activo = 1
                  AND a.activo = 1
                  AND a.puntaje_maximo > 0
                GROUP BY
                    an.estudiante_id,
                    a.docente_asignacion_id,
                    a.periodo_id,
                    a.dimension_id,
                    COALESCE(dcp.puntaje_maximo, de.puntaje_maximo, 0);
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_notas_totales AS
                SELECT
                    estudiante_id,
                    docente_asignacion_id,
                    periodo_id,
                    SUM(nota_dimension) AS nota_total,
                    COUNT(dimension_id) AS dimensiones_evaluadas
                FROM v_notas_por_dimension
                GROUP BY estudiante_id, docente_asignacion_id, periodo_id;
            """)


def revert_custom_sql(apps, schema_editor):
    vendor = schema_editor.connection.vendor

    if vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP VIEW IF EXISTS v_notas_totales CASCADE;")
            cursor.execute("DROP VIEW IF EXISTS v_notas_por_dimension CASCADE;")
            cursor.execute("DROP VIEW IF EXISTS v_nota_ser_asistencia CASCADE;")
            cursor.execute("DROP TRIGGER IF EXISTS trg_audit_actividad_notas ON actividad_notas;")
            cursor.execute("DROP FUNCTION IF EXISTS audit_actividad_notas();")
            for tabla in ['usuarios', 'estudiantes', 'tutores', 'nota_observaciones']:
                cursor.execute(f"DROP TRIGGER IF EXISTS trg_{tabla}_updated_at ON {tabla};")
            cursor.execute("DROP FUNCTION IF EXISTS set_updated_at();")
            cursor.execute("DROP INDEX IF EXISTS unica_fila_configuracion;")
            cursor.execute("DROP INDEX IF EXISTS un_periodo_activo_por_gestion;")
            cursor.execute("ALTER TABLE periodos DROP CONSTRAINT IF EXISTS periodo_fecha_valida;")
            cursor.execute("ALTER TABLE licencias DROP CONSTRAINT IF EXISTS licencia_fecha_valida;")
            cursor.execute("ALTER TABLE licencias DROP CONSTRAINT IF EXISTS aprobacion_consistente;")
    elif vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP VIEW IF EXISTS v_notas_totales;")
            cursor.execute("DROP VIEW IF EXISTS v_notas_por_dimension;")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(apply_custom_sql, revert_custom_sql),
    ]
