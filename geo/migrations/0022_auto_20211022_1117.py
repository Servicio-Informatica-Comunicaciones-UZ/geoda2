# Generated by Django 3.2.8 on 2021-10-22 09:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0021_alter_rightssupport_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asignatura',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='calendario',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='categoria',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='forano',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
        migrations.AlterField(
            model_name='pod',
            name='id',
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
            ),
        ),
    ]
