import django_filters
from .models import Asignatura


class AsignaturaListFilter(django_filters.FilterSet):
    """Filtro para buscar asignaturas según ciertos campos."""

    class Meta:
        model = Asignatura
        fields = {
            "nombre_estudio": ["icontains"],
            "nombre_centro": ["icontains"],
            "asignatura_id": ["exact"],
            "nombre_asignatura": ["icontains"],
            "cod_grupo_asignatura": ["exact"],
        }
        order_by = ["asignatura_id"]
