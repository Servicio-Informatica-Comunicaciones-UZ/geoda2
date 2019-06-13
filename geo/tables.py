import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Curso, Pod


class PodTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name="")

    def render_enlace(self, record):
        asig = record.get_asignatura_sigma()
        curso = asig.get_curso_or_none()

        if curso:
            return mark_safe(
                "<a href={0}>Ver&nbsp;ficha del&nbsp;curso</a>".format(
                    reverse("curso-detail", args=[curso.id])
                )
            )
        else:
            return mark_safe(
                "<a href={0}>Crear&nbsp;curso en la plataforma</a>".format(
                    reverse("as-crear-curso", args=[asig.id])
                )
            )

    nombre_estudio = tables.Column(empty_values=(), verbose_name="Estudio")

    def render_nombre_estudio(self, record):
        return record.get_asignatura_sigma().nombre_estudio

    nombre_centro = tables.Column(empty_values=(), verbose_name="Centro")

    def render_nombre_centro(self, record):
        return record.get_asignatura_sigma().nombre_centro

    nombre_asignatura = tables.Column(empty_values=(), verbose_name="Asignatura")

    def render_nombre_asignatura(self, record):
        return record.get_asignatura_sigma().nombre_asignatura

    class Meta:
        attrs = {"class": "table table-striped table-hover cabecera-azul"}
        model = Pod
        fields = (
            "nombre_estudio",
            "nombre_centro",
            "asignatura_id",
            "nombre_asignatura",
            "cod_grupo_asignatura",
            "enlace",
        )
        template_name = "django_tables2/bootstrap4.html"


class CursoTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name="")

    def render_estado(self, record):
        return record.estado.nombre

    def render_enlace(self, record):

        return mark_safe(
            "<a href={0}>Ver&nbsp;ficha del&nbsp;curso</a>".format(
                reverse("curso-detail", args=[record.id])
            )
        )

    class Meta:
        attrs = {"class": "table table-striped table-hover cabecera-azul"}
        model = Curso
        fields = (
            "nombre",
            "anyo_academico",
            "fecha_solicitud",
            "fecha_autorizacion",
            "estado",
            "enlace",
        )
        template_name = "django_tables2/bootstrap4.html"
