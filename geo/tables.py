import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Curso, Pod


class PodTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name="")

    def render_enlace(self, record):
        asig = record.get_asignatura_sigma()
        curso = asig.get_curso_or_none()

        if curso:
            return mark_safe(
                """<a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
                <span class='far fa-eye' aria-hidden='true'></span>&nbsp;Ver&nbsp;ficha
                </a>""".format(
                    reverse("curso-detail", args=[curso.id])
                )
            )
        else:
            return mark_safe(
                """
                <a href={0}
                  class='btn btn-warning btn-sm'
                  title='Crear curso en la plataforma'
                >
                  <span class='fas fa-plus' aria-hidden='true'></span>Crear&nbsp;curso
                </a>""".format(
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
    estado = tables.Column(accessor="estado.nombre", verbose_name=_("Estado"))

    def render_enlace(self, record):
        return mark_safe(
            """<a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
               <span class='far fa-eye' aria-hidden='true'></span>&nbsp;Ver&nbsp;ficha
            </a>""".format(
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
