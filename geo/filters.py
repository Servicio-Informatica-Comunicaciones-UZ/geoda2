import django_filters
from .models import AsignaturaSigma


class AsignaturaSigmaListFilter(django_filters.FilterSet):
    """Filtro para buscar asignaturas según ciertos campos."""

    class Meta:
        model = AsignaturaSigma
        fields = {
            "nombre_estudio": ["icontains"],
            "nombre_centro": ["icontains"],
            "asignatura_id": ["exact"],
            "nombre_asignatura": ["icontains"],
            "cod_grupo_asignatura": ["exact"],
        }
        order_by = ["asignatura_id"]
