from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_schema_corrections'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS configuracion_escuela (
                id BIGSERIAL PRIMARY KEY,
                nombre TEXT NOT NULL DEFAULT 'Unidad Educativa',
                direccion TEXT NOT NULL DEFAULT '',
                telefono TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                ciudad TEXT NOT NULL DEFAULT '',
                gestion_actual INTEGER NULL,
                escala_aprobacion NUMERIC(5,2) NOT NULL DEFAULT 51.00,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS configuracion_escuela",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS unica_fila_configuracion ON configuracion_escuela ((1))",
            reverse_sql="DROP INDEX IF EXISTS unica_fila_configuracion",
        ),
    ]
