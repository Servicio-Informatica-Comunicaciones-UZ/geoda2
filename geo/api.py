from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI

from .models import Asignatura, Calendario, MatriculaAutomatica
from .schema import AsignaturaSchema, NotFoundSchema
from .utils import matricular_grupo_sigma

api = NinjaAPI()


@api.get('/asignaturas/{asignatura_nk}', response=list[AsignaturaSchema])
def list_asignaturas(request, asignatura_nk: int):
    """Devuelve los registros de la tabla `asignatura` de un código de asignatura"""
    anyo_academico = Calendario.objects.get(slug='actual').anyo
    return Asignatura.objects.filter(asignatura_id=asignatura_nk, anyo_academico=anyo_academico)


@api.delete('/matricula-automatica/{registro_id}', response={204: None, 403: None})
def delete_matricula_automatica(request, registro_id: int):
    """Borra un registro de matrícula automática"""
    registro = get_object_or_404(MatriculaAutomatica, id=registro_id)
    profesores_del_curso = registro.curso.profesores_activos
    grupo_gestores = Group.objects.get(name='Gestores')
    gestores = grupo_gestores.user_set.all()
    if request.user not in profesores_del_curso and request.user not in gestores:
        return 403, None  # Forbidden

    registro.delete()
    return 204, None  # No content


@api.patch(
    '/matricula-automatica-toggle/{registro_id}',
    response={200: dict, 403: None, 404: NotFoundSchema},
)
def toggle_matricula_automatica(request, registro_id: int):
    """Activa o desactiva un registro"""
    try:
        ma = MatriculaAutomatica.objects.get(pk=registro_id)
    except MatriculaAutomatica.DoesNotExist:  # as e:
        return 404, {'message': 'No se encontró ese registro de matrícula automática.'}

    profesores_del_curso = ma.curso.profesores_activos
    grupo_gestores = Group.objects.get(name='Gestores')
    gestores = grupo_gestores.user_set.all()
    if request.user not in profesores_del_curso and request.user not in gestores:
        return 403, None  # Forbidden

    ma.active = not ma.active
    ma.save()

    num_matriculados = 0
    if ma.active:
        num_matriculados = matricular_grupo_sigma(
            ma.courseid, ma.asignatura_nk, ma.cod_grupo_asignatura, ma.centro_id, ma.plan_id
        )

    return 200, {
        'num_matriculados': num_matriculados,
        'queda_activado': ma.active,
    }  # OK
