# Generated by Django 5.0.1 on 2024-01-24 09:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0032_remove_matriculaautomatica_sigmacentro_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forano',
            options={
                'ordering': ('-fecha_solicitud',),
                'permissions': [
                    ('forano', 'Puede ver y resolver las solicitudes de vinculación.')
                ],
            },
        ),
        migrations.AlterField(
            model_name='forano',
            name='estado',
            field=models.IntegerField(
                choices=[
                    (None, 'Cualquiera'),
                    (1, 'Solicitado'),
                    (2, 'Denegado'),
                    (3, 'Autorizado'),
                ],
                verbose_name='Estado',
            ),
        ),
    ]
