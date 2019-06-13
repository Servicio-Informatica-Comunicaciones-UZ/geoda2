# Generated by Django 2.1 on 2019-01-03 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Pod",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "plan_id_nk",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. plan"
                    ),
                ),
                (
                    "centro_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. centro"
                    ),
                ),
                (
                    "asignatura_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. asignatura"
                    ),
                ),
                (
                    "cod_grupo_asignatura",
                    models.IntegerField(blank=True, null=True, verbose_name="Grupo"),
                ),
                (
                    "anyo_academico",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Año académico"
                    ),
                ),
                (
                    "nip",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=10,
                        null=True,
                        verbose_name="NIP",
                    ),
                ),
                (
                    "apellido1",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        null=True,
                        verbose_name="Primer apellido",
                    ),
                ),
                (
                    "apellido2",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        null=True,
                        verbose_name="Segundo apellido",
                    ),
                ),
                (
                    "nombre",
                    models.CharField(
                        blank=True, max_length=32, null=True, verbose_name="Nombre"
                    ),
                ),
                ("tipo_docencia", models.IntegerField()),
            ],
            options={"db_table": "pod"},
        )
    ]