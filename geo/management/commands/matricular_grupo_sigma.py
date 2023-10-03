from django.core.management.base import BaseCommand
from django.db import connection

from geo.utils import matricular_grupo_sigma


class Command(BaseCommand):
    help = 'Matricula en los cursos Moodle los NIPs matriculados en Sigma que cumplan los filtros.'

    def handle(self, *args, **options):
        # Obtenemos todos los registros activos de matrícula automática.
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT courseid, asignatura_id, cod_grupo_asignatura, centro_id, plan_id
                FROM matricula_automatica
                WHERE active = 1
                ORDER BY courseid, asignatura_id;
                '''
            )
            registros = cursor.fetchall()

        # Para cada registro de matrícula automática
        for registro in registros:
            # Matricular en el curso Moodle los NIPs matriculados en Sigma que cumplan los filtros
            matricular_grupo_sigma(*registro)
