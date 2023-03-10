# Generated by Django 4.1.6 on 2023-02-09 07:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0024_alter_asignatura_cod_grupo_asignatura_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matriculaautomatica',
            name='active',
            field=models.BooleanField(default=True, verbose_name='¿Activo?'),
        ),
        migrations.AlterField(
            model_name='matriculaautomatica',
            name='cod_grupo_asignatura',
            field=models.IntegerField(
                blank=True,
                help_text='Déjelo en blanco para seleccionar todos los grupos.',
                null=True,
                verbose_name='Cód. grupo de la asignatura',
            ),
        ),
    ]
