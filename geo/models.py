# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AsignaturaSigma(models.Model):
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name="Cód. plan")
    nombre_estudio = models.CharField(
        max_length=254, blank=True, null=True, verbose_name="Estudio"
    )
    centro_id = models.IntegerField(blank=True, null=True, verbose_name="Cód. centro")
    nombre_centro = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Centro"
    )
    tipo_estudio_id = models.IntegerField(
        blank=True, null=True, verbose_name="Cód. tipo estudio"
    )
    nombre_tipo_estudio = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Tipo de estudio"
    )
    asignatura_id = models.IntegerField(
        blank=True, null=True, verbose_name="Cód. asignatura"
    )
    nombre_asignatura = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="Asignatura"
    )
    prela_cu = models.CharField(max_length=5, blank=True, null=True)
    tipo_periodo = models.CharField(
        max_length=1, blank=True, null=True, verbose_name="Tipo de periodo"
    )
    valor_periodo = models.CharField(
        max_length=2, blank=True, null=True, verbose_name="Periodo"
    )
    cod_grupo_asignatura = models.IntegerField(
        blank=True, null=True, verbose_name="Grupo"
    )
    turno = models.CharField(max_length=1, blank=True, null=True)
    tipo_docencia = models.IntegerField(
        blank=True, null=True, verbose_name="Tipo de docencia"
    )
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name="Año académico"
    )
    edicion = models.IntegerField(blank=True, null=True, verbose_name="Edición")

    class Meta:
        db_table = "asignatura_sigma"
        unique_together = (
            (
                "plan_id_nk",
                "asignatura_id",
                "cod_grupo_asignatura",
                "centro_id",
                "anyo_academico",
            ),
        )

    def get_curso_or_none(self):
        try:
            return Curso.objects.get(asignatura_sigma_id=self.id)
        except Curso.DoesNotExist:
            return None


class Pod(models.Model):
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name="Cód. plan")
    centro_id = models.IntegerField(blank=True, null=True, verbose_name="Cód. centro")
    asignatura_id = models.IntegerField(
        blank=True, null=True, verbose_name="Cód. asignatura"
    )
    cod_grupo_asignatura = models.IntegerField(
        blank=True, null=True, verbose_name="Grupo"
    )
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name="Año académico"
    )
    nip = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="NIP"
    )
    apellido1 = models.CharField(
        max_length=32, blank=True, null=True, verbose_name="Primer apellido"
    )
    apellido2 = models.CharField(
        max_length=32, blank=True, null=True, verbose_name="Segundo apellido"
    )
    nombre = models.CharField(
        max_length=32, blank=True, null=True, verbose_name="Nombre"
    )
    tipo_docencia = models.IntegerField()

    # Alternative: https://pypi.org/project/django-composite-foreignkey/
    def get_asignatura_sigma(self):
        asig = AsignaturaSigma.objects.get(
            anyo_academico=self.anyo_academico,
            centro_id=self.centro_id,
            plan_id_nk=self.plan_id_nk,
            asignatura_id=self.asignatura_id,
            cod_grupo_asignatura=self.cod_grupo_asignatura,
        )
        return asig

    def __str__(self):
        return "{0} {1} {2} {3}".format(
            self.anyo_academico, self.plan_id_nk, self.asignatura_id, self.nip
        )

    class Meta:
        db_table = "pod"
        index_together = ["nip", "anyo_academico"]


class Categoria(models.Model):
    plataforma_id = models.IntegerField(
        blank=True, null=True, verbose_name="Cód. plataforma"
    )
    id_nk = models.CharField(
        max_length=45, blank=True, null=True, verbose_name="Cód. en plataforma"
    )
    nombre = models.CharField(max_length=250, blank=True, null=True)
    supercategoria = models.ForeignKey(
        "self", models.DO_NOTHING, blank=True, null=True, verbose_name="Categoría padre"
    )
    centro_id = models.IntegerField(blank=True, null=True, verbose_name="Cód. centro")
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name="Cód. plan")
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name="Año académico"
    )

    class Meta:
        db_table = "categoria"
        unique_together = (("anyo_academico", "centro_id", "plan_id_nk"),)


class Estado(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=127, blank=True, null=True)

    class Meta:
        db_table = 'estado'


class Curso(models.Model):
    nombre = models.CharField(max_length=200, blank=True, null=True)
    fecha_solicitud = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de solicitud"
    )
    fecha_autorizacion = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de autorización"
    )
    autorizador = models.ForeignKey(
        "accounts.CustomUser", models.DO_NOTHING, blank=True, null=True
    )
    plataforma_id = models.IntegerField(
        blank=True, null=True, verbose_name="Cód. plataforma"
    )
    id_nk = models.CharField(
        max_length=45, blank=True, null=True, verbose_name="Código en plataforma"
    )
    fecha_creacion = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de creación"
    )
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name="URL")
    categoria = models.ForeignKey(
        Categoria, models.DO_NOTHING, blank=True, null=True, verbose_name="Categoría"
    )
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name="Año académico"
    )
    asignatura_sigma = models.ForeignKey(
        "AsignaturaSigma",
        models.DO_NOTHING,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Asignatura Sigma",
    )
    estado = models.ForeignKey('Estado', models.DO_NOTHING, blank=True, null=True)
    motivo_solicitud = models.TextField(
        blank=True, null=True, verbose_name="Motivo de la solicitud"
    )
    motivo_denegacion = models.TextField(
        blank=True, null=True, verbose_name="Motivo de la denegación"
    )
    profesores = models.ManyToManyField("accounts.CustomUser",related_name='profesores', through="ProfesorCurso")

    class Meta:
        db_table = "curso"

class ProfesorCurso(models.Model):

    id = models.IntegerField(primary_key=True)
    curso_id = models.ForeignKey(
        "Curso", models.DO_NOTHING
    )
    profesor_id = models.ForeignKey(
        "accounts.CustomUser", models.DO_NOTHING
    )
    fecha_alta = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de alta"
    )
    fecha_baja = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de baja"
    )

    class Meta:
        db_table = "profesor_curso"
