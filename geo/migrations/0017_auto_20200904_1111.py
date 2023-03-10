# Generated by Django 3.0.7 on 2020-09-04 09:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0016_auto_20200415_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='forano',
            name='nombre',
            field=models.CharField(
                default='---',
                help_text='Nombre y apellidos del usuario a vincular.',
                max_length=127,
                verbose_name='Nombre y apellidos',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='forano',
            name='motivo_solicitud',
            field=models.TextField(
                help_text='Quién es el usuario externo, motivos por los que solicita'
                ' su vinculación a Moodle, así como el curso en el que participaría'
                ' y con qué rol.',
                verbose_name='Motivación de la solicitud',
            ),
        ),
    ]
