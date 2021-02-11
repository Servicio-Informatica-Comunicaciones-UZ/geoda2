import django_tables2 as tables
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Asignatura, Curso, Forano


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
                    reverse('curso_detail', args=[record.curso.id])
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
                reverse('as_crear_curso', args=[record.id])
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


class CursosTodosTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name='')

    def render_enlace(self, record):
        return mark_safe(
            """<a href={0} class='btn btn-info btn-sm' title='Ver ficha del curso'>
               <span class='far fa-eye' aria-hidden='true'></span>&nbsp;Ver&nbsp;ficha
            </a>""".format(
                reverse('curso_detail', args=[record.id])
            )
        )

    def render_profesores(self, record):
        asignaciones = record.profesorcurso_set.filter(
            Q(fecha_baja__gt=timezone.now()) | Q(fecha_baja=None)
        ).all()
        profes = [a.profesor.full_name for a in asignaciones]
        return ', '.join(profes)

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Curso
        fields = ('nombre', 'profesores', 'estado', 'enlace')
        empty_text = _("No hay ningún curso que satisfaga los criterios de búsqueda.")
        template_name = 'django_tables2/bootstrap4.html'


class CursosPendientesTable(tables.Table):
    profesores = tables.ManyToManyColumn(
        verbose_name='Solicitante', transform=lambda u: u.full_name
    )

    def render_nombre(self, record):
        return mark_safe(
            f'<a href={reverse("curso_detail", args=[record.id])}>{record.nombre}</a>'
        )

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
                reverse('curso_detail', args=[record.id])
            )
        )

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Curso
        fields = ('nombre', 'fecha_solicitud', 'fecha_autorizacion', 'estado', 'enlace')
        template_name = 'django_tables2/bootstrap4.html'


class ForanoTodosTable(tables.Table):

    enlace = tables.Column(empty_values=(), verbose_name='')

    def render_enlace(self, record):
        return mark_safe(
            f"""<a href={reverse('forano_detail', args=[record.id])} class='btn btn-info btn-sm' title='Ver'>
               <span class='far fa-eye' aria-hidden='true'></span>&nbsp;Ver
            </a>"""
        )

    class Meta:
        attrs = {'class': 'table table-striped table-hover cabecera-azul'}
        model = Forano
        fields = ('fecha_solicitud', 'solicitante__full_name', 'nip', 'enlace')  # 'estado',
        empty_text = _("No hay ningún usuario externo que satisfaga los criterios de búsqueda.")
        template_name = 'django_tables2/bootstrap4.html'
