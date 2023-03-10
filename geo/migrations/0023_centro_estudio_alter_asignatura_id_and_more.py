# Generated by Django 4.0.3 on 2023-01-27 13:24

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_alter_customuser_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geo', '0022_auto_20211022_1117'),
    ]

    operations = [
        migrations.CreateModel(
            name='Centro',
            fields=[
                (
                    'id',
                    models.PositiveSmallIntegerField(
                        primary_key=True, serialize=False, verbose_name='cód. académico'
                    ),
                ),
                ('nombre', models.CharField(max_length=255)),
                ('municipio', models.CharField(blank=True, max_length=100, null=True)),
                ('esta_activo', models.BooleanField(default=False, verbose_name='¿Activo?')),
            ],
            options={
                'db_table': 'centro',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Estudio',
            fields=[
                (
                    'id',
                    models.PositiveSmallIntegerField(
                        primary_key=True, serialize=False, verbose_name='Cód. estudio'
                    ),
                ),
                ('nombre', models.CharField(max_length=255)),
                ('esta_activo', models.BooleanField(default=True, verbose_name='¿Activo?')),
            ],
            options={
                'db_table': 'estudio',
                'ordering': ['nombre'],
            },
        ),
        migrations.AlterField(
            model_name='asignatura',
            name='id',
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='calendario',
            name='id',
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='categoria',
            name='id',
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='asignatura',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='curso',
                to='geo.asignatura',
                verbose_name='Asignatura',
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='id',
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='nombre',
            field=models.CharField(
                help_text='El nombre del curso no se puede cambiar,'
                ' así que debe ser descriptivo y diferenciable de otros.',
                max_length=200,
                verbose_name='Nombre del curso',
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='profesores',
            field=models.ManyToManyField(
                related_name='cursos', through='geo.ProfesorCurso', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='forano',
            name='id',
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='pod',
            name='id',
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                (
                    'id',
                    models.PositiveSmallIntegerField(
                        primary_key=True, serialize=False, verbose_name='Cód. plan'
                    ),
                ),
                ('esta_activo', models.BooleanField(default=True, verbose_name='¿Activo?')),
                (
                    'centro',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='planes',
                        to='geo.centro',
                    ),
                ),
                (
                    'estudio',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='planes',
                        to='geo.estudio',
                    ),
                ),
            ],
            options={
                'db_table': 'plan',
            },
        ),
        migrations.CreateModel(
            name='Matriculacion',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('anyo_academico', models.IntegerField(verbose_name='Año académico')),
                (
                    'nip',
                    models.PositiveIntegerField(
                        help_text='Número de Identificación Personal del alumno matriculado.',
                        validators=[
                            django.core.validators.MinValueValidator(100001),
                            django.core.validators.MaxValueValidator(9999999),
                        ],
                        verbose_name='NIP del alumno',
                    ),
                ),
                (
                    'asignatura_id',
                    models.IntegerField(db_index=True, verbose_name='Cód. asignatura'),
                ),
                ('tipo_asignatura', models.CharField(max_length=15)),
                ('cod_grupo_asignatura', models.IntegerField(verbose_name='Grupo')),
                (
                    'centro',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='matriculaciones',
                        to='geo.centro',
                    ),
                ),
                (
                    'plan',
                    models.ForeignKey(
                        limit_choices_to={'esta_activo': True},
                        on_delete=django.db.models.deletion.PROTECT,
                        to='geo.plan',
                    ),
                ),
            ],
            options={
                'db_table': 'matriculacion',
            },
        ),
        migrations.CreateModel(
            name='MatriculaAutomatica',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('courseid', models.PositiveBigIntegerField()),
                ('sigmacourseid', models.CharField(max_length=10)),
                ('sigmagroupid', models.CharField(max_length=5)),
                ('active', models.BooleanField(verbose_name='¿Activo?')),
                ('sigmatitu', models.CharField(max_length=10)),
                ('sigmacentro', models.CharField(max_length=10)),
                ('fijo', models.BooleanField(verbose_name='¿Registro predefinido?')),
                (
                    'asignatura_id',
                    models.IntegerField(blank=True, null=True, verbose_name='Cód. asignatura'),
                ),
                (
                    'cod_grupo_asignatura',
                    models.IntegerField(blank=True, null=True, verbose_name='Grupo'),
                ),
                (
                    'centro',
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={'esta_activo': True},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='geo.centro',
                    ),
                ),
                (
                    'plan',
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={'esta_activo': True},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='geo.plan',
                    ),
                ),
            ],
            options={
                'db_table': 'matricula_automatica',
                'unique_together': {
                    ('asignatura_id', 'cod_grupo_asignatura', 'plan', 'courseid', 'centro'),
                    ('sigmacourseid', 'sigmagroupid', 'sigmatitu', 'courseid', 'sigmacentro'),
                },
            },
        ),
    ]
