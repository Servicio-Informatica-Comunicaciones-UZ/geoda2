from django.core.management.base import BaseCommand
from django.db import connection

from geo.utils import matricular_grupo_sigma


class Command(BaseCommand):
    """
    Esta orden es lanzada por Ofelia (<https://github.com/taraspos/ofelia/>),
    según esté configurado en `docker-compose.yml`.
    Por ejemplo, cada día a las 06:45:00.
    """

    help = 'Matricula en los cursos Moodle los NIPs matriculados en Sigma que cumplan los filtros.'

    def handle(self, *args, **options):
        # Obtenemos todos los registros activos de matrícula automática.
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT courseid, asignatura_nk, cod_grupo_asignatura, centro_id, plan_id
                FROM matricula_automatica
                JOIN curso ON matricula_automatica.curso_id = curso.id
                JOIN calendario ON curso.anyo_academico = calendario.anyo
                WHERE matricula_automatica.active = 1
                  AND calendario.slug = 'actual'
                ORDER BY courseid, asignatura_nk;
                '''
            )
            registros = cursor.fetchall()

        # Para cada registro de matrícula automática
        for registro in registros:
            # Matricular en el curso Moodle los NIPs matriculados en Sigma que cumplan los filtros
            matricular_grupo_sigma(*registro)
