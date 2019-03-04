from django import forms
from django.forms import ModelForm
from .models import Curso, Categoria
from .methods import *

class SolicitaForm(ModelForm):

    class Meta:
        model = Curso
        fields = ('nombre', 'categoria', 'motivo_solicitud')

    def __init__(self, **kwargs):
        super(SolicitaForm, self).__init__(**kwargs)

        self.campoNombre()
        self.campoCategoria()

        # Añade la clase Bootstrap pertinente
        self.fields['motivo_solicitud'].widget.attrs['class'] = 'form-control'

    def campoNombre(self):
        """ Define el campo nombre del formulario
        """ 
        self.fields['nombre'].label = 'Nombre del curso'
        self.fields['nombre'].widget.attrs['class'] = 'form-control'

    def campoCategoria(self):
        """ Define el campo categoria como un select entre 
        las distintas categorias de este año académico con
        la posibilidad de buscar entre las opciones.
        """
        self.fields['categoria'].queryset = Categoria.objects.filter(anyo_academico=devuelveAñoAcademicoActual()).values_list('nombre', flat=True).order_by('nombre')
        self.fields['categoria'].widget.attrs['class'] = 'selectpicker form-control'
        self.fields['categoria'].widget.attrs['data-live-search-placeholder'] = 'Buscar...'
        self.fields['categoria'].widget.attrs['data-live-search'] = 'true'
        self.fields['categoria'].widget.attrs['data-size'] = '5'

    def clean(self):
        formulario = super().clean()
        cc_nombre = formulario.get('nombre')
        cc_categoria = formulario.get('categoria')
        cc_motivo_solicitud = formulario.get('motivo_solicitud')

        if cc_nombre and cc_categoria and cc_motivo_solicitud:
            print("TODO OK")
        else:
            self.add_error('nombre', 'Especifique los datos.')
