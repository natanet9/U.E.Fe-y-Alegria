import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_schema_alignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservacionesEstudiantes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.TextField(choices=[('positiva', 'Positiva'), ('negativa', 'Negativa'), ('neutra', 'Neutra')])),
                ('descripcion', models.TextField()),
                ('fecha', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('activo', models.BooleanField(default=True)),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.estudiantes')),
                ('registrado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.usuarios')),
            ],
            options={
                'db_table': 'observaciones_estudiantes',
                'managed': True,
            },
        ),
    ]
