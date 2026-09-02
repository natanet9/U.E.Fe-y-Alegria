from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_audit_log_registro_id_nullable'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='inscripciones',
            index=models.Index(fields=['estudiante', 'gestion'], name='idx_insc_est_gestion'),
        ),
    ]
