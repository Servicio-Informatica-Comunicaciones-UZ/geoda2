from django.db import connection
from django_tables2 import SingleTableView

from geo.models import Curso
from geo.wsclient import WSClient


class PagedFilteredTableView(SingleTableView):
    filter_class = None
    formhelper_class = None
    context_filter_name = 'filter'

    def get_table_data(self):
        self.filter = self.filter_class(self.request.GET, queryset=super().get_table_data())
        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_filter_name] = self.filter
        return context


def matricular_grupo_sigma(
    courseid, asignatura_id, cod_grupo_asignatura, centro_id, plan_id
) -> int:
    """Matricula en un curso Moodle los NIPs matriculados en Sigma que cumplan los filtros."""

    print(
        f'Curso Moodle: {courseid}'
        f'  Asignatura: {asignatura_id}  Grupo: {cod_grupo_asignatura}'
        f'  Centro: {centro_id}  Plan: {plan_id}'
    )

    try:
        curso = Curso.objects.get(id_nk=courseid)
    except Exception:  # as ex:
        print(f'ERROR: Curso #{courseid} no encontrado en Moodle!')
        return 0

    # Buscamos los NIPs matriculados en Sigma que cumplan los filtros
    consulta = '''
    SELECT nip
    FROM matriculacion
    WHERE 1=1
    '''
    if asignatura_id:
        consulta += f' AND asignatura_id = {asignatura_id}'
    if cod_grupo_asignatura:
        consulta += f' AND cod_grupo_asignatura = {cod_grupo_asignatura}'
    if centro_id:
        consulta += f' AND centro_id = {centro_id}'
    if plan_id:
        # 107 (estudio 449): Movilidad para 1º y 2º ciclo y grado
        # 266 (estudio 634): Movilidad para máster
        consulta += f' AND plan_id IN ({plan_id}, 107, 266)'

    with connection.cursor() as cursor:
        cursor.execute(consulta)
        filas = cursor.fetchall()
    nips_en_sigma = [str(fila[0]) for fila in filas]

    if len(nips_en_sigma) == 0:
        print("No hay estudiantes en Sigma que cumplan los criterios indicados.")
        return 0

    cliente = WSClient()
    usuarios_ya_matriculados = cliente.buscar_alumnos(curso)
    nips_ya_matriculados = [u.get('username') for u in usuarios_ya_matriculados]
    nips_a_matricular = set(nips_en_sigma) - set(nips_ya_matriculados)

    # Matriculamos en el curso Moodle indicado los NIPs de Sigma que todavía no lo estén
    num_a_matricular = len(nips_a_matricular)
    if num_a_matricular == 0:
        print('Todos los alumnos de Sigma están ya matriculados en el curso Moodle.')
        return 0

    print(
        f'Se va a intentar matricular a {num_a_matricular} estudiantes'
        f' en el curso Moodle #{courseid}.'
    )

    try:
        num_matriculados, _ = cliente.matricular_alumnos(nips_a_matricular, curso)
        print(f'Matriculados {num_matriculados} estudiantes en el curso Moodle #{courseid}.')
        if num_a_matricular != num_matriculados:
            print('AVISO:', num_a_matricular - num_matriculados, 'estudiantes no matriculados!')
    except Exception:
        print("ERROR al intentar matricular estudiantes en el curso de Moodle #{courseid}.")
        return 0

    return num_matriculados
