from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from .models import MatriculaAutomatica
from .schema import NotFoundSchema

api = NinjaAPI()


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
