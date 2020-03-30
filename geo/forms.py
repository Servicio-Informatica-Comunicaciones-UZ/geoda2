# third-party
from crispy_forms.bootstrap import FormActions, InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit

# Django
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# local Django
from .models import Calendario, Categoria, Curso, ProfesorCurso


class AsignaturaFilterFormHelper(FormHelper):
    """
    Formulario para filtrar el listado de todas las asignaturas.

    Ver https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html
    """

    form_class = 'form form-inline'
    form_id = 'asignatura-search-form'
    form_method = 'GET'
    form_tag = True
    html5_required = True
    layout = Layout(
        Div(
            Fieldset(
                "<span class='fa fa-search'></span> " + str(_('Buscar asignatura')),
                Div(
                    InlineField('nombre_estudio__icontains', wrapper_class='col-4'),
                    InlineField('nombre_centro__icontains', wrapper_class='col-4'),
                    InlineField('plan_id_nk', wrapper_class='col-4'),
                    InlineField('asignatura_id', wrapper_class='col-4'),
                    InlineField('nombre_asignatura__icontains', wrapper_class='col-4'),
                    InlineField('cod_grupo_asignatura', wrapper_class='col-4'),
                    css_class='row',
                ),
                css_class='col-10 border p-3',
            ),
            FormActions(Submit('submit', _('Filtrar')), css_class='col-2 text-right align-self-center'),
            css_class='row',
        )
    )


class CursoFilterFormHelper(FormHelper):
    """
    Formulario para filtrar el listado de todos los cursos.

    Ver https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html
    """

    form_class = 'form form-inline'
    form_id = 'curso-search-form'
    form_method = 'GET'
    form_tag = True
    html5_required = True
    layout = Layout(
        Div(
            Fieldset(
                "<span class='fa fa-search'></span> " + str(_('Buscar curso')),
                Div(
                    InlineField('nombre__icontains', wrapper_class='col-6'),
                    InlineField('estado', wrapper_class='col-6'),
                    css_class='row',
                ),
                css_class='col-10 border p-3',
            ),
            FormActions(Submit('submit', _('Filtrar')), css_class='col-2 text-right align-self-center'),
            css_class='row',
        )
    )


class CursoSolicitarForm(forms.ModelForm):
    """
    Formulario para solicitar un curso no reglado.

    Incluye el nombre, la categoría y el motivo de la solicitud.
    """

    class Meta:
        model = Curso
        fields = ('nombre', 'categoria', 'motivo_solicitud')
        required = ('categoria', 'motivo_solicitud')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CursoSolicitarForm, self).__init__(*args, **kwargs)

        for field in self.Meta.required:
            self.fields[field].required = True

        anyo_academico = Calendario.objects.get(slug='actual').anyo
        cat_anyo = Categoria.objects.get(anyo_academico=anyo_academico, supercategoria_id__isnull=True)
        self.fields['categoria'].widget.choices = (
            Categoria.objects.filter(centro_id=None)
            .filter(anyo_academico=anyo_academico)
            .exclude(id=cat_anyo.id)
            .exclude(supercategoria_id=cat_anyo.id)
            .values_list('id', 'nombre')
            .order_by('nombre')
            .all()
        )

    def save(self, commit=True):
        """Guarda la solicitud de curso, y añade al solicitante como profesor."""

        # Añade la fecha de solicitud y cambia el estado del curso a Solicitado.
        self.instance.fecha_solicitud = timezone.now()
        self.instance.estado = Curso.Estado.SOLICITADO
        self.instance.anyo_academico = Calendario.objects.get(slug='actual').anyo
        self.instance.plataforma_id = 1
        curso = super(CursoSolicitarForm, self).save(commit=commit)

        # Añadimos por omisión al profesor que solicita el curso a la lista de profesores del curso.
        # Si el curso es autorizado, se le matriculará como profesor al crearse el curso en Moodle.
        profesor_curso = ProfesorCurso(curso=curso, profesor=self.user, fecha_alta=timezone.now())
        profesor_curso.save()

        return curso


class ForanoFilterFormHelper(FormHelper):
    """
    Formulario para filtrar el listado de todos los foranos.

    Ver https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html
    """

    form_class = 'form form-inline'
    form_id = 'forano-search-form'
    form_method = 'GET'
    form_tag = True
    html5_required = True
    layout = Layout(
        Div(
            Fieldset(
                "<span class='fa fa-search'></span> " + str(_('Buscar solicitud de vinculación')),
                Div(
                    InlineField('nip', wrapper_class='col-6'),
                    InlineField('estado', wrapper_class='col-6'),
                    css_class='row',
                ),
                css_class='col-10 border p-3',
            ),
            FormActions(Submit('submit', _('Filtrar')), css_class='col-2 text-right align-self-center'),
            css_class='row',
        )
    )
