from django.contrib import admin

# Register your models here.
from .models import AsignaturaSigma, Categoria, Curso, Estado, Pod

admin.site.register(AsignaturaSigma)
admin.site.register(Categoria)
admin.site.register(Curso)
admin.site.register(Estado)
admin.site.register(Pod)
