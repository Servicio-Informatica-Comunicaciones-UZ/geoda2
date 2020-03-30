import django_filters
from .models import Asignatura, Curso, Forano


class AsignaturaListFilter(django_filters.FilterSet):
    """Filtro para buscar asignaturas según ciertos campos."""

    class Meta:
        model = Asignatura
        fields = {
            'nombre_estudio': ['icontains'],
            'nombre_centro': ['icontains'],
            'plan_id_nk': ['exact'],
            'asignatura_id': ['exact'],
            'nombre_asignatura': ['icontains'],
            'cod_grupo_asignatura': ['exact'],
        }
        order_by = ['asignatura_id']


class CursoFilter(django_filters.FilterSet):
    """Filtro para buscar cursos por su nombre y/o estado."""

    class Meta:
        model = Curso
        fields = {'nombre': ['icontains'], 'estado': ['exact']}
        order_by = ['nombre']


class ForanoFilter(django_filters.FilterSet):
    """Filtro para buscar solicitudes de vinculación."""

    class Meta:
        model = Forano
        fields = {'nip': ['exact'], 'estado': ['exact']}
        order_by = ['fecha_solicitud']
