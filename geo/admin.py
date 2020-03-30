from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Asignatura, Calendario, Categoria, Curso, Pod, ProfesorCurso


# Register your models here.

admin.site.register(Asignatura)
admin.site.register(Categoria)
admin.site.register(Pod)
admin.site.register(ProfesorCurso)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'anyo_academico', 'nombre', 'id_nk', 'estado')
    list_filter = ('anyo_academico', 'estado')
    fields = ('nombre', 'categoria')
    ordering = ('estado', 'nombre')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'categoria':
            kwargs['queryset'] = Categoria.objects.filter(
                anyo_academico=Calendario.objects.get(slug='actual').anyo, nombre__in=Categoria.NO_REGLADAS
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.site_header = _('Administración de Geoda')
admin.site.site_title = _('Administración de Geoda')
admin.site.index_title = _('Inicio')
