#!/usr/bin/env python
# Copyright (C) 2020 Enrique Matías Sánchez
# License: GNU General Public License v3.0 or later - <http://www.gnu.org/licenses/>
#
# Este script recorre la tabla de cursos mirando los usuarios profesores (que tienen su
# usuario de correo como `username`, y su NIP como `idnumber`) de cada curso del 2019-2020.
# Averigua cuál es el usuarioNip de cada profesor.
# Matricula al usuarioNip correspondiente como profesor del curso.
#
# Dependencias:
# * Oracle Instant Client
#   <https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html>

# standard library
import json
import time

# third-party libraries
import cx_Oracle  # <https://oracle.github.io/python-cx_Oracle/>
import pymysql  # <https://github.com/PyMySQL/PyMySQL/>
import requests  # <https://github.com/psf/requests>
import toml  # <https://github.com/uiri/toml>


def request_url(verb, api_url, wsfunction, token, data=None):
    """Envía una petición al Web Service."""
    if verb == 'POST':
        resp = requests.post(
            f'{api_url}?wstoken={token}&wsfunction={wsfunction}&moodlewsrestformat=json',
            data=data,
        )
    elif verb == 'GET':
        resp = requests.get(
            f'{api_url}?wstoken={token}&wsfunction={wsfunction}&moodlewsrestformat=json',
            params=data,
        )
    else:
        raise Exception('Método HTTP no soportado')

    if not resp.ok:  # resp.status_code 200
        resp.raise_for_status()

    received_data = json.loads(resp.content.decode('utf-8'))
    if isinstance(received_data, dict) and received_data.get('exception', None):
        raise Exception(received_data.get('message'))

    return received_data


def main():
    config = toml.load('config.toml')
    api_url = config['moodle']['api_url']
    geo_token = config['moodle']['geo_token']

    # Establece conexión con la base de datos de Moodle
    connection = pymysql.connect(
        host=config['moodle']['db_host'],
        user=config['moodle']['db_user'],
        password=config['moodle']['db_pass'],
        db=config['moodle']['db_name'],
        port=config['moodle']['db_port'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )

    # Establece conexión con la BD de Gestión de Identidades.
    gi_dsn = cx_Oracle.makedsn(
        config['gi']['db_host'], config['gi']['db_port'], config['gi']['db_sid'],
    )
    gi_conn = cx_Oracle.connect(config['gi']['db_user'], config['gi']['db_pass'], gi_dsn,)
    gi_cursor = gi_conn.cursor()
    # print('Database version:', gi_conn.version)

    try:
        with connection.cursor() as cursor:
            # Profesores de este curso académico (cat. 5010) que no tienen su NIP en el `idnumber`.
            cursor.execute(
                """
                SELECT DISTINCT u.id, u.username, u.email, u.idnumber, u.firstname, u.lastname
                  FROM mdl_course AS c
                  JOIN mdl_context AS ctx ON c.id = ctx.instanceid
                  JOIN mdl_role_assignments AS ra ON ra.contextid = ctx.id
                  JOIN mdl_user AS u ON u.id = ra.userid
                  JOIN mdl_course_categories AS cats ON c.category = cats.id
                  JOIN mdl_role AS r ON ra.roleid = r.id
                 WHERE u.username NOT REGEXP '^[0-9]*$'
                   AND u.idnumber NOT REGEXP '^[0-9]*$'
                   AND u.auth='ldap'
                   AND cats.path LIKE '/5010%' -- Curso 2019-2020
                   AND r.id IN (3, 4, 10);  -- editingteacher, teacher, noenrolingteacher;
                """
            )
            usuarios_sin_nip = cursor.fetchall()

            for usuario in usuarios_sin_nip:
                # Buscamos al usuario en Gestión de Identidades.
                gi_cursor.execute(
                    """
                    SELECT nip, nombre, apellido_1, apellido_2, correo_principal, correo_personal
                      FROM GESTIDEN.GI_V_IDENTIDAD
                     WHERE correo_principal = :email
                        OR correo_personal = :email
                    """,
                    email=usuario['email'],
                )
                gi_cursor.rowfactory = lambda *args: dict(
                    zip([d[0] for d in gi_cursor.description], args)
                )
                usuario_identificado = gi_cursor.fetchone()
                if not usuario_identificado:
                    print(f'Usuario no encontrado en Gestión de Identidades: {usuario["email"]}')
                    continue

                # Si encontramos al usuario en GI, actualizamos el `idnumber` en Moodle.
                # print(
                #    f'El usuario {usuario["id"]} ({usuario["email"]})'
                #    f' tiene el NIP {usuario_identificado["NIP"]}.'
                # )
                cursor.execute(
                    'UPDATE mdl_user SET idnumber = %(nip)s WHERE id = %(id)s',
                    {'nip': usuario_identificado['NIP'], 'id': usuario['id']},
                )

            # Usuarios cuyo email no está en I.D., pero he identificado por su nombre y apellidos.
            # usuarios_manuales = [('eddie.head@unizar.es', 666)]
            usuarios_manuales = []

            for email, nip in usuarios_manuales:
                cursor.execute(
                    'UPDATE mdl_user SET idnumber = %(nip)s WHERE email = %(email)s',
                    {'nip': nip, 'email': email},
                )

            connection.commit()

            # Asignaciones de profes de este curso académico que tienen su NIP en el `idnumber`.
            cursor.execute(
                """
                SELECT u.id, u.username, u.email, u.idnumber,
                       c.id AS course_id, c.fullname, r.id AS roleid
                  FROM mdl_course AS c
                  JOIN mdl_context AS ctx ON c.id = ctx.instanceid
                  JOIN mdl_role_assignments AS ra ON ra.contextid = ctx.id
                  JOIN mdl_user AS u ON u.id = ra.userid
                  JOIN mdl_course_categories AS cats ON c.category = cats.id
                  JOIN mdl_role AS r ON ra.roleid = r.id
                 WHERE u.username NOT REGEXP '^[0-9]*$'
                   AND u.idnumber REGEXP '^[0-9]*$'
                   AND u.auth='ldap'
                   AND cats.path LIKE '/5010%'  -- Curso 2019-2020
                   AND r.id IN (3, 4, 10);  -- editingteacher, teacher, noenrolingteacher
                """
            )
            asignaciones_usuarios_correo = cursor.fetchall()

            for asignacion in asignaciones_usuarios_correo:
                # Para cada asignacion de un usuarioCorreo, buscamos el usuarioNip correspondiente.
                cursor.execute(
                    """
                    SELECT id, username, email, idnumber, deleted
                      FROM mdl_user
                     WHERE username = %(nip)s
                    """,
                    {'nip': asignacion['idnumber']},
                )
                usuario_nip = cursor.fetchone()

                if not usuario_nip:
                    print(f'No se ha encontrado usuario con el username {asignacion["idnumber"]}')
                    continue

                if usuario_nip['deleted'] == 1:
                    print(f'El usuarioNip con ID {usuario_nip["id"]} está marcado como borrado.')
                    continue

                # Matriculamos como profesor del curso al usuarioNip
                payload = {
                    'enrolments[0][roleid]': asignacion['roleid'],
                    'enrolments[0][userid]': usuario_nip['id'],
                    'enrolments[0][courseid]': asignacion['course_id'],
                    'enrolments[0][timestart]': int(time.time()),
                }
                print(repr(payload))
                request_url('POST', api_url, 'enrol_manual_enrol_users', geo_token, payload)

    finally:
        # Desconecta del servidor
        connection.close()


if __name__ == '__main__':
    main()
