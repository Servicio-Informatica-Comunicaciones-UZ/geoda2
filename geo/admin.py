from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Asignatura, Categoria, Curso, Pod, ProfesorCurso


# Register your models here.

admin.site.register(Asignatura)
admin.site.register(Categoria)
admin.site.register(Curso)
admin.site.register(Pod)
admin.site.register(ProfesorCurso)

admin.site.site_header = _('Administración de Geoda')
admin.site.site_title = _('Administración de Geoda')
admin.site.index_title = _('Página principal')
