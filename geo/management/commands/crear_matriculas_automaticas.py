from annoying.functions import get_object_or_None
from django.core.management.base import BaseCommand

from geo.models import Calendario, Curso, MatriculaAutomatica


class Command(BaseCommand):
    help = 'Crea los registros de matrícula automática por omisión que falten.'

    def handle(self, *args, **options):
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        cursos_reglados = Curso.objects.filter(
            anyo_academico=anyo_academico, asignatura_id__isnull=False
        ).order_by('id')

        for curso in cursos_reglados:
            ma_por_omision = get_object_or_None(
                MatriculaAutomatica,
                curso_id=curso.id,
                asignatura_nk=curso.asignatura.asignatura_id,  # Cód. Sigma de la asignatura
                centro_id=curso.asignatura.centro_id,
                plan_id=curso.asignatura.plan_id_nk,
                cod_grupo_asignatura=curso.asignatura.cod_grupo_asignatura,
            )

            if not ma_por_omision:
                print(f'Creando registro de matrícula automática para el curso {curso.id}...\n')
                # Crear registro desactivado en la tabla `matricula_automatica` local
                try:
                    ma = MatriculaAutomatica(
                        courseid=curso.id_nk,
                        asignatura_nk=curso.asignatura.asignatura_id,  # Cód. Sigma de asignatura
                        cod_grupo_asignatura=curso.asignatura.cod_grupo_asignatura,
                        centro_id=curso.asignatura.centro_id,
                        plan_id=curso.asignatura.plan_id_nk,
                        active=False,
                        fijo=True,
                        curso_id=curso.id,
                    )
                    ma.save()
                except Exception as ex:
                    print(
                        f'AVISO: No fue posible crear el registro de matrícula automática. {ex}\n'
                    )
            # else:
            #    print(f'El curso {curso.id} ya tiene la matrícula automática predefinida.\n')
