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

    # Matriculamos en el curso Moodle indicado los NIPs encontrados
    nips = [fila[0] for fila in filas]
    try:
        curso = Curso.objects.get(id_nk=courseid)
    except Exception:  # as ex:
        print(f'Curso #{courseid} no encontrado.')
        return 0

    cliente = WSClient()
    num_matriculados, _ = cliente.matricular_alumnos(nips, curso)

    print(f'Matriculados {num_matriculados} estudiantes en el curso Moodle #{courseid}.')
    print(
        f'Asignatura: {asignatura_id}  Grupo: {cod_grupo_asignatura}'
        f'  Centro: {centro_id}  Plan: {plan_id}'
    )

    return num_matriculados
