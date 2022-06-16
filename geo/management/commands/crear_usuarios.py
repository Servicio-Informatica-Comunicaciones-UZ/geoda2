from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crea usuarios locales para los NIPs que aparecen en el POD'

    def handle(self, *args, **options):
        # Obtenemos los NIPs que figuran en el POD pero que no tienen usuario en Geoda
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT DISTINCT nip
                FROM pod
                LEFT JOIN accounts_customuser ON nip = username
                WHERE username IS NULL
                ORDER BY nip
                '''
            )
            rows = cursor.fetchall()
        nips = (row[0] for row in rows)

        # Creamos un usuario en Geoda para cada uno de esos NIPs
        User = get_user_model()
        for nip in nips:
            User.crear_usuario(None, nip)
