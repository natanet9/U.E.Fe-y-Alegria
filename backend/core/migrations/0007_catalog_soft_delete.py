from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_usuario_last_login'),
    ]

    operations = [
        migrations.AddField(
            model_name='niveles',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='grados',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='paralelos',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='cursos',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='areas',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='dimensionesevaluacion',
            name='activo',
            field=models.BooleanField(default=True),
        ),
    ]
