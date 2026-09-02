import django.db.models.deletion
from django.db import migrations, models


def populate_docentes(apps, schema_editor):
    Usuarios = apps.get_model('core', 'Usuarios')
    Docentes = apps.get_model('core', 'Docentes')
    DocenteAsignacion = apps.get_model('core', 'DocenteAsignacion')

    user_ids = set(DocenteAsignacion.objects.values_list('usuario_id', flat=True))
    for uid in user_ids:
        try:
            user = Usuarios.objects.get(id=uid)
            Docentes.objects.get_or_create(usuario=user, defaults={'activo': True})
        except Usuarios.DoesNotExist:
            pass

    for da in DocenteAsignacion.objects.all():
        try:
            doc = Docentes.objects.get(usuario_id=da.usuario_id)
            da.docente_id = doc.id
            da.save(update_fields=['docente_id'])
        except Docentes.DoesNotExist:
            pass


def split_nombre_completo(apps, schema_editor):
    Usuarios = apps.get_model('core', 'Usuarios')
    for u in Usuarios.objects.all():
        if not u.nombre and not u.apellido and u.nombre_completo:
            parts = u.nombre_completo.strip().split(' ', 1)
            u.nombre = parts[0] if parts else u.nombre_completo
            u.apellido = parts[1] if len(parts) > 1 else ''
            u.save(update_fields=['nombre', 'apellido'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_soft_delete_remaining_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='Docentes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo_academico', models.TextField(blank=True, null=True)),
                ('especialidad', models.TextField(blank=True, null=True)),
                ('fecha_ingreso_institucion', models.DateField(blank=True, null=True)),
                ('anos_experiencia', models.IntegerField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='docente', to='core.usuarios')),
            ],
            options={
                'db_table': 'docentes',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='UsuarioRol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asignado_en', models.DateTimeField(auto_now_add=True)),
                ('activo', models.BooleanField(default=True)),
                ('asignado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='roles_asignados_por', to='core.usuarios')),
                ('rol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.roles')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles_usuario', to='core.usuarios')),
            ],
            options={
                'db_table': 'usuario_roles',
                'managed': True,
                'unique_together': {('usuario', 'rol')},
            },
        ),
        migrations.AddField(
            model_name='usuarios',
            name='ci',
            field=models.TextField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='usuarios',
            name='nombre',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuarios',
            name='apellido',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='estudiantes',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='estudiante_usuario', to='core.usuarios'),
        ),
        migrations.AddField(
            model_name='dimensionesevaluacion',
            name='puntaje_maximo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='dimensionesevaluacion',
            name='gestion',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='docenteasignacion',
            name='docente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.docentes'),
        ),
        migrations.RunPython(populate_docentes, migrations.RunPython.noop),
        migrations.RunPython(split_nombre_completo, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='docenteasignacion',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='docenteasignacion',
            name='usuario',
        ),
        migrations.AlterField(
            model_name='docenteasignacion',
            name='docente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.docentes'),
        ),
        migrations.AlterUniqueTogether(
            name='docenteasignacion',
            unique_together={('docente', 'curso', 'area', 'gestion')},
        ),
        migrations.AlterField(
            model_name='usuarios',
            name='nombre_completo',
            field=models.TextField(blank=True, null=True),
        ),
    ]
