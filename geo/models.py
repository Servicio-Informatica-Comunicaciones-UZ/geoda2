from django.db import models
from django.utils.translation import gettext_lazy as _


class AsignaturaSigma(models.Model):
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name=_("Cód. plan"))
    nombre_estudio = models.CharField(
        max_length=254, blank=True, null=True, verbose_name=_("Estudio")
    )
    centro_id = models.IntegerField(
        blank=True, null=True, verbose_name=_("Cód. centro")
    )
    nombre_centro = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_("Centro")
    )
    tipo_estudio_id = models.IntegerField(
        blank=True, null=True, verbose_name=_("Cód. tipo estudio")
    )
    nombre_tipo_estudio = models.CharField(
        max_length=30, blank=True, null=True, verbose_name=_("Tipo de estudio")
    )
    asignatura_id = models.IntegerField(
        blank=True, null=True, verbose_name=_("Cód. asignatura")
    )
    nombre_asignatura = models.CharField(
        max_length=120, blank=True, null=True, verbose_name=_("Asignatura")
    )
    prela_cu = models.CharField(max_length=5, blank=True, null=True)
    tipo_periodo = models.CharField(
        max_length=1, blank=True, null=True, verbose_name=_("Tipo de periodo")
    )
    valor_periodo = models.CharField(
        max_length=2, blank=True, null=True, verbose_name=_("Periodo")
    )
    cod_grupo_asignatura = models.IntegerField(
        blank=True, null=True, verbose_name=_("Grupo")
    )
    turno = models.CharField(max_length=1, blank=True, null=True)
    tipo_docencia = models.IntegerField(
        blank=True, null=True, verbose_name=_("Tipo de docencia")
    )
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name=_("Año académico")
    )
    edicion = models.IntegerField(blank=True, null=True, verbose_name=_("Edición"))

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


class Calendario(models.Model):
    """Este modelo almacena el año académico actual."""

    id = models.IntegerField(primary_key=True, verbose_name=_("Año académico"))

    @staticmethod
    def get_anyo_academico_actual():
        return Calendario.objects.first().id

    class Meta:
        db_table = "calendario"


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
    nip = models.CharField(max_length=10, blank=True, null=True, verbose_name="NIP")
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
        blank=True, null=True, verbose_name=_("Cód. plataforma")
    )
    id_nk = models.CharField(
        max_length=45, blank=True, null=True, verbose_name=_("Cód. en plataforma")
    )
    nombre = models.CharField(max_length=250, blank=True, null=True)
    supercategoria = models.ForeignKey(
        "self", models.PROTECT, blank=True, null=True, verbose_name=_("Categoría padre")
    )
    centro_id = models.IntegerField(
        blank=True, null=True, verbose_name=_("Cód. centro")
    )
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name=_("Cód. plan"))
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name=_("Año académico")
    )

    class Meta:
        db_table = "categoria"
        unique_together = (("anyo_academico", "centro_id", "plan_id_nk"),)


class Estado(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=127, blank=True, null=True)

    class Meta:
        db_table = "estado"


class Curso(models.Model):
    nombre = models.CharField(max_length=200, blank=True, null=True)
    fecha_solicitud = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Fecha de solicitud")
    )
    fecha_autorizacion = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Fecha de autorización")
    )
    autorizador = models.ForeignKey(
        "accounts.CustomUser", models.PROTECT, blank=True, null=True
    )
    plataforma_id = models.IntegerField(
        blank=True, null=True, verbose_name=_("Cód. plataforma")
    )
    id_nk = models.CharField(
        max_length=45, blank=True, null=True, verbose_name=_("Código en plataforma")
    )
    fecha_creacion = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Fecha de creación")
    )
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("URL"))
    categoria = models.ForeignKey(
        Categoria, models.PROTECT, blank=True, null=True, verbose_name=_("Categoría")
    )
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name=_("Año académico")
    )
    asignatura_sigma = models.ForeignKey(
        "AsignaturaSigma",
        models.PROTECT,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Asignatura Sigma",
    )
    estado = models.ForeignKey("Estado", models.PROTECT, blank=True, null=True)
    motivo_solicitud = models.TextField(
        blank=True, null=True, verbose_name=_("Motivo de la solicitud")
    )
    motivo_denegacion = models.TextField(
        blank=True, null=True, verbose_name=_("Motivo de la denegación")
    )
    profesores = models.ManyToManyField(
        "accounts.CustomUser", related_name="profesores", through="ProfesorCurso"
    )

    def get_absolute_url(self):
        return "/curso/%i/" % self.id

    class Meta:
        db_table = "curso"


class ProfesorCurso(models.Model):

    id = models.AutoField(primary_key=True)
    curso = models.ForeignKey("Curso", models.PROTECT)
    profesor = models.ForeignKey("accounts.CustomUser", models.PROTECT)
    fecha_alta = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Fecha de alta")
    )
    fecha_baja = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Fecha de baja")
    )

    class Meta:
        db_table = "profesor_curso"
