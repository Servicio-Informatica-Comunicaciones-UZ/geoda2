# Third-party
from crispy_forms.bootstrap import InlineField, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Div, Fieldset, Layout, Submit

# Django
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Local Django
from .models import Calendario, Categoria, Curso, MatriculaAutomatica, ProfesorCurso


class AsignaturaFilterFormHelper(FormHelper):
    """
    Formulario para filtrar el listado de todas las asignaturas.

    Ver https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html
    """

    form_class = 'form row align-items-center'
    form_id = 'asignatura-search-form'
    form_method = 'GET'
    form_tag = True
    html5_required = True
    layout = Layout(
        Fieldset(
            "<span class='fa fa-search'></span> " + str(_('Buscar asignatura')),
            Div(
                InlineField('nombre_estudio__icontains', wrapper_class='col-4'),
                InlineField('nombre_centro__icontains', wrapper_class='col-4'),
                InlineField('plan_id_nk', wrapper_class='col-4'),
                css_class='row mb-3',
            ),
            Div(
                InlineField('asignatura_id', wrapper_class='col-4'),
                InlineField('nombre_asignatura__icontains', wrapper_class='col-4'),
                InlineField('cod_grupo_asignatura', wrapper_class='col-4'),
                css_class='row',
            ),
            css_class='col-10 border p-3',
        ),
        Div(
            ButtonHolder(
                Submit('submit', _('Filtrar')),
                # css_class='position-relative top-50 start-50 translate-middle text-center',
                css_class='text-center',
            ),
            css_class='col-2',
        ),
    )


class CursoFilterFormHelper(FormHelper):
    """
    Formulario para filtrar el listado de todos los cursos.

    Ver https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html
    """

    form_class = 'form row align-items-center'
    form_id = 'curso-search-form'
    form_method = 'GET'
    form_tag = True
    html5_required = True
    layout = Layout(
        Fieldset(
            "<span class='fa fa-search'></span> " + str(_('Buscar curso')),
            Div(
                InlineField('nombre__icontains', wrapper_class='col-8'),
                InlineField('estado', wrapper_class='col-4'),
                css_class='row mb-3',
            ),
            Div(
                InlineField('profesores__username', wrapper_class='col-4'),
                InlineField('profesores__first_name__icontains', wrapper_class='col-4'),
                InlineField('profesores__last_name__icontains', wrapper_class='col-4'),
                css_class='row',
            ),
            css_class='col-10 border p-3',
        ),
        Div(
            ButtonHolder(Submit('submit', _('Filtrar')), css_class='text-center'),
            css_class='col-2',
        ),
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
        super().__init__(*args, **kwargs)

        for field in self.Meta.required:
            self.fields[field].required = True

        anyo_academico = Calendario.objects.get(slug='actual').anyo

        self.fields['nombre'].widget.attrs['placeholder'] = self.fields['nombre'].help_text

        cat_anyo = Categoria.objects.get(
            anyo_academico=anyo_academico, supercategoria_id__isnull=True
        )
        self.fields['categoria'].widget.choices = (
            Categoria.objects.filter(centro_id=None)
            .filter(anyo_academico=anyo_academico)
            .exclude(id=cat_anyo.id)
            .exclude(supercategoria_id=cat_anyo.id)
            .values_list('id', 'nombre')
            .order_by('nombre')
            .all()
        )
        self.fields['motivo_solicitud'].widget.attrs['placeholder'] = self.fields[
            'motivo_solicitud'
        ].help_text

    def save(self, commit=True):
        """Guarda la solicitud de curso, y añade al solicitante como profesor."""

        # Añade la fecha de solicitud y cambia el estado del curso a Solicitado.
        self.instance.solicitante = self.user
        self.instance.fecha_solicitud = timezone.now()
        self.instance.estado = Curso.Estado.SOLICITADO
        self.instance.anyo_academico = Calendario.objects.get(slug='actual').anyo
        self.instance.plataforma_id = 1
        curso = super().save(commit=commit)

        # Añadimos por omisión al profesor que solicita el curso a la lista de profesores del curso
        # Si el curso es autorizado, se le matriculará como profesor al crearse el curso en Moodle.
        profesor_curso = ProfesorCurso(curso=curso, profesor=self.user, fecha_alta=timezone.now())
        profesor_curso.save()

        return curso


class ForanoFilterFormHelper(FormHelper):
    """
    Formulario para filtrar el listado de todos los foranos.

    Ver https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html
    """

    form_class = 'form row align-items-center'
    form_id = 'forano-search-form'
    form_method = 'GET'
    form_tag = True
    html5_required = True
    layout = Layout(
        Fieldset(
            "<span class='fa fa-search'></span> " + str(_('Buscar solicitud de vinculación')),
            Div(
                # TODO: Averiguar cómo hacer que aparezca "NIP del solicitante"
                # en vez del automático "Solicitante NIP"
                InlineField('solicitante__username', wrapper_class='col-6'),
                InlineField('nip', wrapper_class='col-6'),
                # InlineField('estado', wrapper_class='col-6'),
                css_class='row',
            ),
            css_class='col-10 border p-3',
        ),
        Div(
            ButtonHolder(Submit('submit', _('Filtrar')), css_class='text-center'),
            css_class='col-2',
        ),
    )


class MatriculaAutomaticaForm(forms.ModelForm):
    """Formulario para matricular en un curso a los matriculados en un grupo de asignatura Sigma"""

    class Meta:
        model = MatriculaAutomatica
        fields = ('asignatura_id', 'centro', 'plan', 'cod_grupo_asignatura')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.field_template = 'bootstrap5/layout/floating_field.html'
        self.helper.wrapper_class = 'form-floating'

        self.fields['centro'].empty_label = _('Todos')
        self.fields['plan'].empty_label = _('Todos')


"""
class MatricularPlanForm(forms.Form):
    # Formulario para matricular en un curso a todos los matriculados en un plan.

    curso_id = forms.IntegerField(widget=forms.HiddenInput())
    plan_id_nk = forms.IntegerField(
        help_text=_(
            'Puede consultar el código del plan'
            ' en la <a href="https://estudios.unizar.es" target="_blank">web de estudios</a>.'
        ),
        label=_('Código del plan'),
        min_value=0,
        max_value=9999,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_action = 'matricular_plan'
        self.helper.form_class = 'row align-items-center'
        self.helper.wrapper_class = 'col-4'
        self.helper.field_template = 'bootstrap5/layout/floating_field.html'
        self.helper.layout = Layout(
            'curso_id',  # hidden
            'plan_id_nk',
            Div(
                ButtonHolder(
                    StrictButton(
                        f"<span class='fas fa-user-graduate'></span> {_('Matricular')}",
                        title=_(
                            'Matricular en este curso a todos los alumnos'
                            ' de alguna de las asignaturas del plan'
                        ),
                        css_class='btn btn-warning',
                        type='submit',
                    ),
                    css_class='ms-1',
                ),
                css_class='col-2 mb-4',
            ),
        )
"""


class ProfesorCursoAddForm(forms.Form):
    """Formulario para añadir un profesor a un curso."""

    curso_id = forms.IntegerField(widget=forms.HiddenInput())
    nip = forms.IntegerField(
        help_text=_('Número de Identificación Personal del nuevo profesor'),
        label=_('NIP del nuevo profesor'),
        min_value=0,
        max_value=9999999,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_action = 'pc_anyadir'
        self.helper.form_class = 'row align-items-center'  # form-horizontal
        self.helper.wrapper_class = 'col-4'
        # self.helper.label_class = 'me-1'
        # self.helper.field_class = 'col-4'
        self.helper.field_template = 'bootstrap5/layout/floating_field.html'
        self.helper.layout = Layout(
            'curso_id',  # hidden
            # Field('nip', css_class='col-4', placeholder="NIP"),
            'nip',
            Div(
                ButtonHolder(
                    StrictButton(
                        f"<span class='fas fa-user-plus'></span> {_('Añadir')}",
                        css_class='btn btn-warning',
                        title=_('Añadir al titular de este NIP como profesor del curso'),
                        type='submit',
                    ),
                    css_class='margin-start-1',
                ),
                css_class='col-2 mb-4',
            ),
        )
