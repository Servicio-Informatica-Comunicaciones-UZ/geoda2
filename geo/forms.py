from datetime import datetime

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Calendario, Categoria, Curso, Estado, ProfesorCurso


class SolicitaForm(forms.ModelForm):
    """
    Formulario para solicitar un curso no reglado.

    Incluye el nombre, la categoría y el motivo de la solicitud.
    """

    CATEGORIAS_NO_REGLADAS = (
        Categoria.objects.filter(centro_id=None)
        .filter(anyo_academico=Calendario.get_anyo_academico_actual())
        .exclude(supercategoria_id=None)
        .values_list("id", "nombre")
        .order_by("nombre")
        .all()
    )

    class Meta:
        model = Curso
        fields = ("nombre", "categoria", "motivo_solicitud")
        required = ("categoria", "motivo_solicitud")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(SolicitaForm, self).__init__(*args, **kwargs)

        for field in self.Meta.required:
            self.fields[field].required = True

        self.fields["nombre"].help_text = _(
            "Nombre del curso. No se podrá cambiar, "
            "así que debe ser descriptivo y diferenciable de otros."
        )
        self.fields["categoria"].widget.choices = self.CATEGORIAS_NO_REGLADAS
        self.fields["motivo_solicitud"].help_text = _(
            "Explique la razón de solicitarlo como no reglado, "
            "justificación de su creación y público al que va dirigido."
        )

    def save(self, commit=True):
        """Guarda la solicitud de curso, y añade al solicitante como profesor."""

        # Añade la fecha de solicitud y cambia el estado del curso a Solicitado.
        self.instance.fecha_solicitud = datetime.now()
        self.instance.estado = Estado(1)  # -> Solicitado
        self.instance.anyo_academico = Calendario.get_anyo_academico_actual()
        curso = super(SolicitaForm, self).save(commit=commit)

        # Añadimos por omisión al profesor que solicita el curso
        # a la lista de profesores del curso.
        profesor_curso = ProfesorCurso(
            curso=curso, profesor=self.user, fecha_alta=datetime.today()
        )
        profesor_curso.save()

        return curso
