from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from crispy_forms.bootstrap import FormActions, InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit

from .models import Calendario, Categoria, Curso, Estado, ProfesorCurso


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


class SolicitaForm(forms.ModelForm):
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
        super(SolicitaForm, self).__init__(*args, **kwargs)

        for field in self.Meta.required:
            self.fields[field].required = True

        self.fields['nombre'].help_text = _(
            'Nombre del curso. No se podrá cambiar, ' 'así que debe ser descriptivo y diferenciable de otros.'
        )
        self.fields['categoria'].widget.choices = (
            Categoria.objects.filter(centro_id=None)
            .filter(anyo_academico=Calendario.objects.get(slug='actual').anyo)
            .exclude(supercategoria_id=None)
            .values_list('id', 'nombre')
            .order_by('nombre')
            .all()
        )
        self.fields['motivo_solicitud'].help_text = _(
            'Explique la razón de solicitarlo como no reglado, '
            'justificación de su creación y público al que va dirigido.'
        )

    def save(self, commit=True):
        """Guarda la solicitud de curso, y añade al solicitante como profesor."""

        # Añade la fecha de solicitud y cambia el estado del curso a Solicitado.
        self.instance.fecha_solicitud = timezone.now()
        self.instance.estado = Estado(1)  # -> Solicitado
        self.instance.anyo_academico = Calendario.objects.get(slug='actual').anyo
        self.instance.plataforma_id = 1
        curso = super(SolicitaForm, self).save(commit=commit)

        # Añadimos por omisión al profesor que solicita el curso a la lista de profesores del curso.
        # Si el curso es autorizado, se le matriculará como profesor al crearse el curso en Moodle.
        profesor_curso = ProfesorCurso(curso=curso, profesor=self.user, fecha_alta=timezone.now())
        profesor_curso.save()

        return curso
