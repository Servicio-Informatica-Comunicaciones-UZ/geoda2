# Generated by Django 2.2.2 on 2019-06-20 11:59

from django.db import migrations, models

import accounts.models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]

    operations = [
        migrations.AlterModelManagers(
            name='customuser', managers=[('objects', accounts.models.CustomUserManager())]
        ),
        migrations.AddField(
            model_name='customuser',
            name='centro_id_nks',
            field=models.CharField(
                blank=True, max_length=127, null=True, verbose_name='Cód. centros'
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='colectivos',
            field=models.CharField(blank=True, max_length=127, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='departamento_id_nks',
            field=models.CharField(
                blank=True, max_length=127, null=True, verbose_name='Cód. departamentos'
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_name_2',
            field=models.CharField(
                blank=True, max_length=150, null=True, verbose_name='segundo apellido'
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='nombre_oficial',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='numero_documento',
            field=models.CharField(
                blank=True,
                help_text='DNI, NIE o pasaporte.',
                max_length=16,
                null=True,
                verbose_name='número de documento',
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='sexo',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='sexo_oficial',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='tipo_documento',
            field=models.CharField(
                blank=True,
                help_text='DNI, NIE o pasaporte.',
                max_length=3,
                null=True,
                verbose_name='tipo de documento',
            ),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='first_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='first name'),
        ),
    ]
