# Generated by Django 3.0.4 on 2020-04-15 12:55

from django.contrib.auth.management import create_permissions
from django.db import migrations


def migrate_permissions(apps, schema_editor):
    """Create the pending permissions.

    Permissions are not actually created during or after an individual migration,
    but are triggered by a post-migrate signal which is sent after the
    `python manage.py migrate` command completes successfully.

    This is necessary so that we can add the permission to a group in this migration.
    """
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=2)
        app_config.models_module = None


def add_permission_to_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    gestores = Group.objects.get(name='Gestores')

    curso_historial = Permission.objects.get(codename='curso_historial')
    gestores.permissions.add(curso_historial)


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0015_auto_20200415_1227'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='curso',
            options={
                'ordering': ('anyo_academico', 'nombre'),
                'permissions': [
                    ('cursos_todos', 'Puede ver el listado de todos los cursos.'),
                    ('cursos_pendientes', 'Puede ver el listado de cursos por aprobar.'),
                    (
                        'curso_administrar',
                        'Puede acceder a la interfaz de administración de Curso.',
                    ),
                    ('curso_delete', 'Puede eliminar cursos.'),
                    ('curso_historial', 'Puede ver el histórico de profesores de un curso.'),
                ],
            },
        ),
        migrations.AlterModelOptions(
            name='profesorcurso',
            options={
                'ordering': ('curso_id', 'fecha_alta', 'fecha_baja'),
                'permissions': [
                    ('anyadir_profesorcurso', 'Puede añadir un profesor a un curso.'),
                    ('pc_anular', 'Puede dar de baja a un profesor de un curso.'),
                ],
                'verbose_name': 'asignación profesor-curso',
                'verbose_name_plural': 'asignaciones profesor-curso',
            },
        ),
        migrations.RunPython(migrate_permissions),
        migrations.RunPython(add_permission_to_group),
    ]
