from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Asignatura, Calendario, Categoria, Curso, Pod, ProfesorCurso

# Register your models here.

admin.site.register(Asignatura)
admin.site.register(Categoria)
admin.site.register(Pod)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'curso_academico', 'nombre', 'id_nk', 'estado')
    list_filter = ('anyo_academico', 'estado')
    fields = (
        'nombre',
        'categoria',
        'estado',
        'fecha_solicitud',
        'motivo_solicitud',
        'comentarios',
    )
    ordering = ('estado', 'nombre')
    readonly_fields = ('estado', 'fecha_solicitud', 'motivo_solicitud', 'comentarios')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'categoria':
            nombres = Categoria.NO_REGLADAS + ('Varios',)
            kwargs['queryset'] = Categoria.objects.filter(
                anyo_academico=Calendario.objects.get(slug='actual').anyo, nombre__in=nombres
            ).order_by('nombre')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ProfesorCurso)
class ProfesorCursoAdmin(admin.ModelAdmin):
    fields = ('profesor', 'curso', 'fecha_alta', 'fecha_baja')
    model = ProfesorCurso
    list_display = ('profesor', 'nombre_profesor', 'curso')
    # list_filter = ('profesor', 'curso')
    ordering = ('profesor', 'curso')
    readonly_fields = ('profesor', 'curso', 'fecha_alta')

    def nombre_profesor(self, obj):
        return obj.profesor.full_name


admin.site.site_header = _('Administración de Geoda')
admin.site.site_title = _('Administración de Geoda')
admin.site.index_title = _('Inicio')
