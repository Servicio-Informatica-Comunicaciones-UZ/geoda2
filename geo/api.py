from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from .models import Asignatura, Calendario, MatriculaAutomatica
from .schema import AsignaturaSchema, NotFoundSchema

api = NinjaAPI()


@api.get('/asignaturas/{asignatura_id}', response=list[AsignaturaSchema])
def list_asignaturas(request, asignatura_id: int):
    """Devuelve los registros de la tabla `asignatura` de un código de asignatura"""
    anyo_academico = Calendario.objects.get(slug='actual').anyo
    return Asignatura.objects.filter(asignatura_id=asignatura_id, anyo_academico=anyo_academico)


@api.delete('/matricula-automatica/{registro_id}', response={204: None})
def delete_matricula_automatica(request, registro_id: int):
    """Borra un registro de matrícula automática"""
    registro = get_object_or_404(MatriculaAutomatica, id=registro_id)
    registro.delete()
    return 204, None  # No content


@api.patch('/matricula-automatica-toggle/{registro_id}', response={200: None, 404: NotFoundSchema})
def toggle_matricula_automatica(request, registro_id: int):
    """Activa o desactiva un registro"""
    try:
        registro = MatriculaAutomatica.objects.get(pk=registro_id)
        registro.active = not registro.active
        registro.save()
        return 200  # OK
    except registro.DoesNotExist:  # as e:
        return 404, {'message': 'No se encontró ese registro de matrícula automática.'}
