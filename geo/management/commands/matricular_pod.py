from annoying.functions import get_object_or_None
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

from geo.models import Curso


class Command(BaseCommand):
    help = 'Matricula en los cursos los NIPs que aparecen en el POD, si no lo estaban.'

    def handle(self, *args, **options):
        # Obtenemos los NIPs que figuran en el POD
        # pero que no están en la lista de profesores del curso en GEO.
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT c.id, p.nip
                FROM curso c
                JOIN asignatura a ON c.asignatura_id = a.id
                JOIN pod p ON a.anyo_academico = p.anyo_academico
                              AND a.asignatura_id = p.asignatura_id
                              AND a.cod_grupo_asignatura = p.cod_grupo_asignatura
                              AND a.centro_id = p.centro_id
                              AND a.plan_id_nk = p.plan_id_nk
                JOIN accounts_customuser ac ON ac.username = p.nip
                LEFT JOIN profesor_curso pc ON c.id = pc.curso_id AND ac.id=pc.profesor_id
                WHERE c.anyo_academico = p.anyo_academico AND c.asignatura_id IS NOT NULL
                   AND (profesor_id IS NULL OR fecha_baja < NOW())
                ORDER BY c.id, ac.username
                '''
            )
            rows = cursor.fetchall()

        User = get_user_model()
        for row in rows:
            curso_id, nip = row[0], row[1]
            curso = get_object_or_None(Curso, pk=curso_id)
            profesor = get_object_or_None(User, username=nip)
            if curso and profesor and profesor not in curso.profesores_activos:
                try:
                    # Añade al usuario a la lista de profesores del curso en GEO,
                    # y lo matricula en Moodle.
                    curso.anyadir_profesor(profesor)
                except Exception as ex:
                    print('ERROR: %s' % str(ex))
