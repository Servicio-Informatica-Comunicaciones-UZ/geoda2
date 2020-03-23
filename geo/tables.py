import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Asignatura, Curso, Pod


class AsignaturasTable(tables.Table):
    enlace = tables.Column(empty_values=(), verbose_name=_('Acción'))

    def render_enlace(self, record):
        if hasattr(record, 'curso'):
            return mark_safe(
                """
                <a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
                  <span class='far fa-eye' aria-hidden='true' style='display: inline;'
                  ></span>&nbsp;&nbsp;Ver&nbsp;ficha
                </a>""".format(
                    reverse('curso-detail', args=[record.curso.id])
                )
            )

        return mark_safe(
            """
            <a href={0}
                class='btn btn-warning btn-sm'
                title='Crear curso en la plataforma'
            >
                <span class='fas fa-plus' aria-hidden='true' style='display: inline;'
                ></span>&nbsp;Crear&nbsp;curso
            </a>""".format(
                reverse('as-crear-curso', args=[record.id])
            )
        )

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Asignatura
        fields = (
            'nombre_estudio',
            'nombre_centro',
            'plan_id_nk',
            'asignatura_id',
            'nombre_asignatura',
            'cod_grupo_asignatura',
            'enlace',
        )
        empty_text = _('No hay ninguna asignatura que satisfaga los criterios de búsqueda.')
        template_name = 'django_tables2/bootstrap4.html'
        per_page = 20


class PodTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name='')

    def render_enlace(self, record):
        asig = record.get_asignatura()

        if hasattr(asig, 'curso'):
            return mark_safe(
                """
                <a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
                  <span class='far fa-eye' aria-hidden='true' style='display: inline;'
                  ></span>&nbsp;&nbsp;Ver&nbsp;ficha
                </a>""".format(
                    reverse('curso-detail', args=[asig.curso.id])
                )
            )

        return mark_safe(
            """
            <a href={0}
                class='btn btn-warning btn-sm'
                title='Crear curso en la plataforma'
            >
                <span class='fas fa-plus' aria-hidden='true' style='display: inline;'
                ></span>&nbsp;Crear&nbsp;curso
            </a>""".format(
                reverse('as-crear-curso', args=[asig.id])
            )
        )

    nombre_estudio = tables.Column(empty_values=(), verbose_name='Estudio')

    def render_nombre_estudio(self, record):
        return record.get_asignatura().nombre_estudio

    nombre_centro = tables.Column(empty_values=(), verbose_name='Centro')

    def render_nombre_centro(self, record):
        return record.get_asignatura().nombre_centro

    nombre_asignatura = tables.Column(empty_values=(), verbose_name='Asignatura')

    def render_nombre_asignatura(self, record):
        return record.get_asignatura().nombre_asignatura

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Pod
        fields = (
            'nombre_estudio',
            'nombre_centro',
            'asignatura_id',
            'nombre_asignatura',
            'cod_grupo_asignatura',
            'enlace',
        )
        template_name = 'django_tables2/bootstrap4.html'


class CursosCreadosTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name='')
    profesores = tables.ManyToManyColumn(transform=lambda u: u.full_name)

    def render_enlace(self, record):
        return mark_safe(
            """<a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
               <span class='far fa-eye' aria-hidden='true'></span>&nbsp;Ver&nbsp;ficha
            </a>""".format(
                reverse('curso-detail', args=[record.id])
            )
        )

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Curso
        fields = ('nombre', 'profesores', 'enlace')
        template_name = 'django_tables2/bootstrap4.html'


class CursosPendientesTable(tables.Table):
    profesores = tables.ManyToManyColumn(verbose_name='Solicitante', transform=lambda u: u.full_name)

    def render_nombre(self, record):
        return mark_safe(f'<a href={reverse("curso-detail", args=[record.id])}>{record.nombre}</a>')

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Curso
        fields = ('fecha_solicitud', 'nombre', 'profesores')
        template_name = 'django_tables2/bootstrap4.html'


class CursoTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name='')

    def render_enlace(self, record):
        return mark_safe(
            """<a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
               <span class='far fa-eye' aria-hidden='true'></span>&nbsp;Ver&nbsp;ficha
            </a>""".format(
                reverse('curso-detail', args=[record.id])
            )
        )

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Curso
        fields = ('nombre', 'fecha_solicitud', 'fecha_autorizacion', 'estado', 'enlace')
        template_name = 'django_tables2/bootstrap4.html'
