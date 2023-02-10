from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from .models import Asignatura, Calendario, MatriculaAutomatica
from .schema import AsignaturaSchema, NotFoundSchema
from .utils import matricular_grupo_sigma

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
        ma = MatriculaAutomatica.objects.get(pk=registro_id)
        ma.active = not ma.active
        ma.save()

        if ma.active:
            matricular_grupo_sigma(
                ma.courseid, ma.asignatura_id, ma.cod_grupo_asignatura, ma.centro_id, ma.plan_id
            )

        return 200  # OK
    except ma.DoesNotExist:  # as e:
        return 404, {'message': 'No se encontró ese registro de matrícula automática.'}
