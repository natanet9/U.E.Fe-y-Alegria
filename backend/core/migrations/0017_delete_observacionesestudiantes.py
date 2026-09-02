# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_rename_apellido_usuarios_primer_apellido_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ObservacionesEstudiantes',
        ),
    ]
