# Generated by Django 4.2.4 on 2023-09-07 10:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0029_alter_matriculaautomatica_cod_grupo_asignatura'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asignatura',
            name='asignatura_id',
            field=models.IntegerField(
                blank=True, db_index=True, null=True, verbose_name='Cód. asignatura'
            ),
        ),
        migrations.AlterField(
            model_name='asignatura',
            name='nombre_asignatura',
            field=models.CharField(
                blank=True, db_index=True, max_length=120, null=True, verbose_name='Asignatura'
            ),
        ),
        migrations.AlterField(
            model_name='matriculaautomatica',
            name='asignatura_id',
            field=models.IntegerField(
                blank=True,
                db_index=True,
                help_text='Puede consultar el código de una asignatura en la <a href="https://estudios.unizar.es" target="_blank">web de estudios</a> <span class="fas fa-link"></span>.',
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(10001),
                    django.core.validators.MaxValueValidator(999999),
                ],
                verbose_name='Cód. asignatura',
            ),
        ),
        migrations.AlterField(
            model_name='matriculaautomatica',
            name='courseid',
            field=models.PositiveBigIntegerField(db_index=True),
        ),
    ]
