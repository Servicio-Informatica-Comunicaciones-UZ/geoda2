# Generated by Django 3.0.4 on 2020-03-30 08:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geo', '0010_rightssupport'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pod',
            options={
                'verbose_name': 'registro del Plan de Ordenación Docente',
                'verbose_name_plural': 'registros del Plan de Ordenación Docente',
            },
        ),
        migrations.AlterModelOptions(
            name='profesorcurso',
            options={
                'verbose_name': 'asignación profesor-curso',
                'verbose_name_plural': 'asignaciones profesor-curso',
            },
        ),
        migrations.AlterField(
            model_name='curso',
            name='motivo_solicitud',
            field=models.TextField(
                blank=True,
                help_text='Razón por la que se solicita el curso como no reglado,'
                ' justificación de su creación y público al que va dirigido.',
                null=True,
                verbose_name='Motivo de la solicitud',
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='nombre',
            field=models.CharField(
                help_text='Nombre del curso. No se puede cambiar,'
                ' así que debe ser descriptivo y diferenciable de otros.',
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name='pod',
            name='tipo_docencia',
            field=models.IntegerField(verbose_name='Tipo de docencia'),
        ),
        migrations.CreateModel(
            name='Forano',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'nip',
                    models.CharField(
                        help_text='Número de Identificación Personal del usuario a vincular.',
                        max_length=10,
                        verbose_name='NIP a vincular',
                    ),
                ),
                (
                    'fecha_solicitud',
                    models.DateTimeField(blank=True, null=True, verbose_name='Fecha de solicitud'),
                ),
                (
                    'fecha_autorizacion',
                    models.DateTimeField(
                        blank=True, null=True, verbose_name='Fecha de autorización'
                    ),
                ),
                (
                    'estado',
                    models.IntegerField(
                        choices=[(1, 'Solicitado'), (2, 'Denegado'), (3, 'Autorizado')],
                        verbose_name='Estado',
                    ),
                ),
                (
                    'motivo_solicitud',
                    models.TextField(
                        help_text='Quién es el usuario externo, motivos por los que solicita'
                        ' su vinculación a Moodle, así como el curso en el que participaría.',
                        verbose_name='Motivación de la solicitud',
                    ),
                ),
                (
                    'comentarios',
                    models.TextField(blank=True, null=True, verbose_name='Comentarios'),
                ),
                (
                    'autorizador',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='foranos_resueltos',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'solicitante',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='foranos_solicitados',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'forano',
                'ordering': ('fecha_solicitud',),
                'permissions': [
                    ('forano', 'Puede ver y resolver las solicitudes de vinculación.')
                ],
            },
        ),
    ]
