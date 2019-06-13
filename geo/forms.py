import datetime
from django.forms import ModelForm
from .models import Curso, Categoria, Estado, ProfesorCurso
from .methods import devuelveAñoAcademicoActual


class SolicitaForm(ModelForm):
    """ Formulario para solicitar un curso no reglado
    con el nombre, la categoría y el motivo de la solicitud.
    """

    class Meta:
        model = Curso
        fields = ("nombre", "categoria", "motivo_solicitud")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(SolicitaForm, self).__init__(*args, **kwargs)

        self.campoNombre()
        self.campoCategoria()

        # Añade la clase Bootstrap pertinente
        self.fields["motivo_solicitud"].required = True
        self.fields["motivo_solicitud"].widget.attrs["class"] = "form-control"

    def campoNombre(self):
        """ Define el campo nombre del formulario
        """
        self.fields["nombre"].required = True
        self.fields["nombre"].label = "Nombre del curso"
        self.fields["nombre"].widget.attrs["class"] = "form-control"

    def campoCategoria(self):
        """ Define el campo categoria como un select entre
        las distintas categorias de este año académico con
        la posibilidad de buscar entre las opciones.
        """
        self.fields["categoria"].required = True
        self.fields["categoria"].widget.choices = (
            Categoria.objects.filter(anyo_academico=devuelveAñoAcademicoActual())
            .values_list("id", "nombre")
            .order_by("nombre")
        )
        self.fields["categoria"].widget.attrs["class"] = "selectpicker form-control"
        self.fields["categoria"].widget.attrs[
            "data-live-search-placeholder"
        ] = "Buscar..."
        self.fields["categoria"].widget.attrs["data-live-search"] = "true"
        self.fields["categoria"].widget.attrs["data-size"] = "5"

    def clean(self):
        """ Valida el formulario antes de registrar la solicitud
        """
        formulario = super().clean()
        cc_nombre = formulario.get("nombre")
        cc_categoria = self.cleaned_data["categoria"]
        cc_motivo_solicitud = formulario.get("motivo_solicitud")

        if cc_nombre and cc_categoria and cc_motivo_solicitud:
            return self.cleaned_data
        else:
            if not cc_nombre:
                self.add_error("nombre", "Especifique un nombre para el curso.")
            if not cc_categoria:
                self.add_error("categoria", "Seleccione una categoría.")
            if not cc_motivo_solicitud:
                self.add_error(
                    "motivo_solicitud", "Desarrolle el motivo de su solicitud."
                )

    def save(self, commit=True):

        # Añade la fecha de solicitud y el estado del curso en solicitado
        self.instance.fecha_solicitud = datetime.now()
        self.instance.estado = Estado(1)  # -> Solicitado
        self.instance.anyo_academico = (
            devuelveAñoAcademicoActual()
        )  # Año académico en el que se hace la solicitud

        # Guardamos el curso
        curso = super(SolicitaForm, self).save(commit=commit)

        # Añadimos por defecto al profesor que solicita el curso
        # a la lista de profesores del curso
        profesor_curso = ProfesorCurso(
            curso=curso, profesor=self.user, fecha_alta=datetime.now()
        )
        profesor_curso.save()
