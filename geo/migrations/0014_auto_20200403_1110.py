# Generated by Django 3.0.4 on 2020-04-03 09:10

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

    anyadir_profesorcurso = Permission.objects.get(codename='anyadir_profesorcurso')
    gestores.permissions.add(anyadir_profesorcurso)


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0013_auto_20200402_0925'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profesorcurso',
            options={
                'permissions': [('anyadir_profesorcurso', 'Puede añadir un profesor a un curso.')],
                'verbose_name': 'asignación profesor-curso',
                'verbose_name_plural': 'asignaciones profesor-curso',
            },
        ),
        migrations.RunPython(migrate_permissions),
        migrations.RunPython(add_permission_to_group),
    ]
