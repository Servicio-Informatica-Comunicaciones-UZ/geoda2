from django import forms
from django.forms import ModelForm
from .models import Curso, Categoria


class SolicitaForm(ModelForm):

    class Meta:
        model = Curso
        fields = ('nombre', 'categoria', 'motivo_solicitud')
    def __init__(self, **kwargs):
        super(SolicitaForm, self).__init__(**kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(anyo_academico=2012).values_list('nombre', flat=True).order_by('nombre')