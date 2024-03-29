# Generated by Django 3.0.7 on 2020-11-03 09:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('geo', '0018_auto_20200918_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='forano',
            name='email',
            field=models.EmailField(
                help_text='Dirección de correo electrónico del usuario a vincular',
                max_length=254,
                null=True,
                verbose_name='correo electrónico',
            ),
        ),
    ]
