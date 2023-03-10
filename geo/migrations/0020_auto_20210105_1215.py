# Generated by Django 3.0.7 on 2021-01-05 11:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geo', '0019_forano_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='solicitante',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cursos_solicitados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='curso',
            name='autorizador',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cursos_autorizados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
