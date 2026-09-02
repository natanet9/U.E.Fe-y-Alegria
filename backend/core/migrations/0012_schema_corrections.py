from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_accesslog'),
    ]

    operations = [
        # 1. Remove usuario_roles table (dead code)
        migrations.DeleteModel(
            name='UsuarioRol',
        ),
        # 2. Fix AuditLog.registro_id: int4 -> int8
        migrations.AlterField(
            model_name='auditlog',
            name='registro_id',
            field=models.BigIntegerField(),
        ),
        # 3. Fix ExportEvent.docente_asignacion_id: int4 -> int8 (no FK, audit table)
        migrations.AlterField(
            model_name='exportevent',
            name='docente_asignacion_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        # 4. Inscripciones: replace unique_together (estudiante, gestion) with
        #    partial unique index WHERE activo = true
        migrations.AlterUniqueTogether(
            name='inscripciones',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='inscripciones',
            constraint=models.UniqueConstraint(
                fields=['estudiante', 'gestion'],
                condition=models.Q(('activo', True)),
                name='un_inscripcion_activa',
            ),
        ),
        # 5. Cursos: add gestion field, update unique_together
        migrations.AddField(
            model_name='cursos',
            name='gestion',
            field=models.IntegerField(default=2026),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='cursos',
            unique_together={('grado', 'paralelo', 'gestion')},
        ),
        # 6. DimensionesEvaluacion: unique_together(nombre, gestion) instead of unique nombre
        #    First fill any NULL gestion with the current year
        migrations.RunSQL(
            sql="UPDATE dimensiones_evaluacion SET gestion = EXTRACT(YEAR FROM NOW())::int WHERE gestion IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='dimensionesevaluacion',
            name='nombre',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='dimensionesevaluacion',
            name='gestion',
            field=models.IntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='dimensionesevaluacion',
            unique_together={('nombre', 'gestion')},
        ),
        # 7. Periodos: add numero field, unique_together(numero, gestion)
        #    First add as nullable so existing rows get NULL
        migrations.AddField(
            model_name='periodos',
            name='numero',
            field=models.IntegerField(null=True, blank=True),
        ),
        #    Assign sequential numbers per gestion (ordered by fecha_inicio)
        migrations.RunSQL(
            sql="""
            UPDATE periodos
            SET numero = sub.rn
            FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY gestion ORDER BY fecha_inicio) AS rn
                FROM periodos
            ) sub
            WHERE periodos.id = sub.id
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        #    Now make numero NOT NULL
        migrations.AlterField(
            model_name='periodos',
            name='numero',
            field=models.IntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='periodos',
            unique_together={('numero', 'gestion')},
        ),
        # 8. Asistencias: replace unique_together with partial unique indexes (fix NULL issue)
        migrations.AlterUniqueTogether(
            name='asistencias',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='asistencias',
            constraint=models.UniqueConstraint(
                fields=['estudiante', 'docente_asignacion', 'fecha', 'tipo'],
                condition=models.Q(('docente_asignacion__isnull', False)),
                name='un_asistencia_por_asignacion',
            ),
        ),
        migrations.AddConstraint(
            model_name='asistencias',
            constraint=models.UniqueConstraint(
                fields=['estudiante', 'fecha', 'tipo'],
                condition=models.Q(('docente_asignacion__isnull', True)),
                name='un_asistencia_administrativa',
            ),
        ),
        # 9. ConfiguracionEscuela: singleton constraint (unique index on constant expression)
        #    Table may have been dropped. Only apply if it exists.
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'configuracion_escuela') THEN
                    EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS unica_fila_configuracion ON configuracion_escuela ((1))';
                END IF;
            END;
            $$;
            """,
            reverse_sql="DROP INDEX IF EXISTS unica_fila_configuracion",
        ),
        # 10. Horarios: overlap exclusion constraint (requires btree_gist extension)
        #     date + time arithmetic is IMMUTABLE in PostgreSQL
        migrations.RunSQL(
            sql="""
            CREATE EXTENSION IF NOT EXISTS btree_gist;
            ALTER TABLE horarios ADD CONSTRAINT horarios_sin_solapamiento
            EXCLUDE USING gist (
                docente_asignacion_id WITH =,
                dia_semana WITH =,
                tsrange(
                    ('2000-01-01'::date + hora_inicio),
                    ('2000-01-01'::date + hora_fin),
                    '[)'
                ) WITH &&
            ) WHERE (activo = true)
            """,
            reverse_sql="ALTER TABLE horarios DROP CONSTRAINT IF EXISTS horarios_sin_solapamiento",
        ),
        # 11. Recreate v_nota_ser_asistencia with correct period filtering
        #     Use LATERAL join to avoid PG 18's strict GROUP BY in correlated subqueries
        migrations.RunSQL(
            sql="""
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
            ) dcp ON true
            """,
            reverse_sql="DROP VIEW IF EXISTS v_nota_ser_asistencia",
        ),
    ]
