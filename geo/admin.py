from django.contrib import admin

from .models import Asignatura, Categoria, Curso, Estado, Pod


# Register your models here.

admin.site.register(Asignatura)
admin.site.register(Categoria)
admin.site.register(Curso)
admin.site.register(Estado)
admin.site.register(Pod)
