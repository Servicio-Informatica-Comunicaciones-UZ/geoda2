# Generated by Django 2.2.2 on 2019-06-20 12:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="AsignaturaSigma",
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
                    "nombre_estudio",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Estudio"
                    ),
                ),
                (
                    "centro_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. centro"
                    ),
                ),
                (
                    "nombre_centro",
                    models.CharField(
                        blank=True, max_length=150, null=True, verbose_name="Centro"
                    ),
                ),
                (
                    "tipo_estudio_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. tipo estudio"
                    ),
                ),
                (
                    "nombre_tipo_estudio",
                    models.CharField(
                        blank=True,
                        max_length=30,
                        null=True,
                        verbose_name="Tipo de estudio",
                    ),
                ),
                (
                    "asignatura_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. asignatura"
                    ),
                ),
                (
                    "nombre_asignatura",
                    models.CharField(
                        blank=True, max_length=120, null=True, verbose_name="Asignatura"
                    ),
                ),
                ("prela_cu", models.CharField(blank=True, max_length=5, null=True)),
                (
                    "tipo_periodo",
                    models.CharField(
                        blank=True,
                        max_length=1,
                        null=True,
                        verbose_name="Tipo de periodo",
                    ),
                ),
                (
                    "valor_periodo",
                    models.CharField(
                        blank=True, max_length=2, null=True, verbose_name="Periodo"
                    ),
                ),
                (
                    "cod_grupo_asignatura",
                    models.IntegerField(blank=True, null=True, verbose_name="Grupo"),
                ),
                ("turno", models.CharField(blank=True, max_length=1, null=True)),
                (
                    "tipo_docencia",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Tipo de docencia"
                    ),
                ),
                (
                    "anyo_academico",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Año académico"
                    ),
                ),
                (
                    "edicion",
                    models.IntegerField(blank=True, null=True, verbose_name="Edición"),
                ),
            ],
            options={
                "verbose_name": "asignatura SIGM@",
                "verbose_name_plural": "asignaturas SIGM@",
                "db_table": "asignatura_sigma",
                "unique_together": {
                    (
                        "plan_id_nk",
                        "asignatura_id",
                        "cod_grupo_asignatura",
                        "centro_id",
                        "anyo_academico",
                    )
                },
            },
        ),
        migrations.CreateModel(
            name="Calendario",
            fields=[
                (
                    "id",
                    models.IntegerField(
                        primary_key=True, serialize=False, verbose_name="Año académico"
                    ),
                )
            ],
            options={"db_table": "calendario"},
        ),
        migrations.CreateModel(
            name="Categoria",
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
                    "plataforma_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. plataforma"
                    ),
                ),
                (
                    "id_nk",
                    models.CharField(
                        blank=True,
                        max_length=45,
                        null=True,
                        verbose_name="Cód. en plataforma",
                    ),
                ),
                ("nombre", models.CharField(blank=True, max_length=250, null=True)),
                (
                    "centro_id",
                    models.IntegerField(
                        blank=True, db_index=True, null=True, verbose_name="Cód. centro"
                    ),
                ),
                (
                    "plan_id_nk",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. plan"
                    ),
                ),
                (
                    "anyo_academico",
                    models.IntegerField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name="Año académico",
                    ),
                ),
                (
                    "supercategoria",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="geo.Categoria",
                        verbose_name="Categoría padre",
                    ),
                ),
            ],
            options={
                "verbose_name": "categoría",
                "db_table": "categoria",
                "unique_together": {("anyo_academico", "centro_id", "plan_id_nk")},
            },
        ),
        migrations.CreateModel(
            name="Curso",
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
                ("nombre", models.CharField(max_length=200)),
                (
                    "fecha_solicitud",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Fecha de solicitud"
                    ),
                ),
                (
                    "fecha_autorizacion",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Fecha de autorización"
                    ),
                ),
                (
                    "plataforma_id",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Cód. plataforma"
                    ),
                ),
                (
                    "id_nk",
                    models.CharField(
                        blank=True,
                        max_length=45,
                        null=True,
                        verbose_name="Código en plataforma",
                    ),
                ),
                (
                    "fecha_creacion",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "url",
                    models.CharField(
                        blank=True, max_length=200, null=True, verbose_name="URL"
                    ),
                ),
                (
                    "anyo_academico",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Año académico"
                    ),
                ),
                (
                    "motivo_solicitud",
                    models.TextField(
                        blank=True, null=True, verbose_name="Motivo de la solicitud"
                    ),
                ),
                (
                    "motivo_denegacion",
                    models.TextField(
                        blank=True, null=True, verbose_name="Motivo de la denegación"
                    ),
                ),
                (
                    "asignatura_sigma",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="geo.AsignaturaSigma",
                        unique=True,
                        verbose_name="Asignatura Sigma",
                    ),
                ),
                (
                    "autorizador",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "categoria",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="geo.Categoria",
                        verbose_name="Categoría",
                    ),
                ),
            ],
            options={"db_table": "curso"},
        ),
        migrations.CreateModel(
            name="Estado",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("nombre", models.CharField(blank=True, max_length=127, null=True)),
            ],
            options={"db_table": "estado"},
        ),
        migrations.CreateModel(
            name="ProfesorCurso",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "fecha_alta",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Fecha de alta"
                    ),
                ),
                (
                    "fecha_baja",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Fecha de baja"
                    ),
                ),
                (
                    "curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="geo.Curso"
                    ),
                ),
                (
                    "profesor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "profesor_curso"},
        ),
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
                        blank=True, max_length=10, null=True, verbose_name="NIP"
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
            options={"db_table": "pod", "index_together": {("nip", "anyo_academico")}},
        ),
        migrations.AddField(
            model_name="curso",
            name="estado",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="geo.Estado",
            ),
        ),
        migrations.AddField(
            model_name="curso",
            name="profesores",
            field=models.ManyToManyField(
                related_name="profesores",
                through="geo.ProfesorCurso",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
