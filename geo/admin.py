from django.contrib import admin

from .models import Asignatura, Categoria, Curso, Pod, ProfesorCurso


# Register your models here.

admin.site.register(Asignatura)
admin.site.register(Categoria)
admin.site.register(Curso)
admin.site.register(Pod)
admin.site.register(ProfesorCurso)
