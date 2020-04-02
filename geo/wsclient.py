import json

import requests
from annoying.functions import get_config


class WSClient:
    """Cliente para conectarse a los Web Services de Moodle usando el protocolo REST.

    Véase:

    - <https://docs.moodle.org/37/en/Using_web_services>
    - <https://docs.moodle.org/dev/Creating_a_web_service_client>
    - <https://docs.moodle.org/dev/Web_service_API_functions>
    """

    geo_token = get_config('GEO_TOKEN')
    api_url = get_config('API_URL')
    geodaws_token = get_config('GEODAWS_TOKEN')

    def crear_categoria(self, datos_categoria):
        """Crea una nueva categoría en Moodle con los datos indicados.

        Consultar Administration → Site Administration → Plugins → Web Services →
                  API Documentation → core_course_create_categories
        """
        payload = {}
        for clave, valor in datos_categoria.items():
            payload[f'categories[0][{clave}]'] = valor
        datos_recibidos = self._request_url('POST', 'core_course_create_categories', self.geo_token, payload)
        return datos_recibidos[0]

    def crear_curso(self, datos_curso):
        """Crea nuevo curso en Moodle con los datos indicados.

        Devuelve una estructura como ésta:
        {'id': 181, 'shortname': '107_356_68500_99_2018'}
        """
        payload = {}
        for clave, valor in datos_curso.items():
            payload[f'courses[0][{clave}]'] = valor
        datos_recibidos = self._request_url('POST', 'core_course_create_courses', self.geo_token, payload)
        return datos_recibidos[0]

    def automatricular(self, asignatura, curso, active=0):
        """Crea un registro en la tabla `sigma` de la base de datos de Moodle.

        Esta tabla se usa para matricular automáticamente a los estudiantes
        de un plan-centro-asignatura-grupo-año.
        """
        payload = {}
        payload['curso_id_nk'] = curso.id_nk
        payload['asignatura_id_nk'] = asignatura.asignatura_id
        payload['cod_grupo_asignatura'] = asignatura.cod_grupo_asignatura
        payload['active'] = active
        payload['plan_id_nk'] = asignatura.plan_id_nk
        payload['centro_id'] = asignatura.centro_id
        mensaje = self._request_url('POST', 'local_geodaws_matricula', self.geodaws_token, payload)
        return mensaje

    def borrar_curso(self, curso):
        """Borra un curso en Moodle."""
        payload = {'courseids[0]': curso.id_nk}
        respuesta = self._request_url('POST', 'core_course_delete_courses', self.geo_token, payload)
        return respuesta

    def buscar_usuario(self, usuario):
        """Busca un usuario en Moodle."""
        # Buscamos a un usuario con ese NIP (idnumber) y dirección de correo.
        payload = {
            'criteria[0][key]': 'idnumber',
            'criteria[0][value]': usuario.username,
            'criteria[1][key]': 'email',
            'criteria[1][value]': usuario.email,
        }
        respuesta = self._request_url('POST', 'core_user_get_users', self.geo_token, payload)
        usuarios_moodle = respuesta['users']
        if usuarios_moodle:
            usuario_moodle = usuarios_moodle[0]
        else:
            # Si no se encuentra, cogemos al primer usuario con ese NIP (idnumber).
            payload = {'criteria[0][key]': 'idnumber', 'criteria[0][value]': usuario.username}
            respuesta = self._request_url('POST', 'core_user_get_users', self.geo_token, payload)
            usuarios_moodle = respuesta['users']
            if usuarios_moodle:
                usuario_moodle = usuarios_moodle[0]
            else:
                # La tarea ETL `add_usuarios_y_matriculas` (Pentaho Spoon)
                # copia un fichero CSV con los usuarios al servidor
                # y una tarea cron los crea, por lo que no se debería llegar aquí nunca,
                # salvo que se trate de un profesor creado ese mismo día.
                raise Exception('Usuario no encontrado en Moodle.')

        return usuario_moodle

    def matricular_profesor(self, usuario, curso):
        """Matricula a un usuario como profesor de un curso de Moodle"""
        usuario_moodle = self.buscar_usuario(usuario)
        payload = {
            'enrolments[0][roleid]': 3,  # id del rol `editingteacher` en Moodle
            'enrolments[0][userid]': usuario_moodle['id'],
            'enrolments[0][courseid]': curso.id_nk,
        }
        mensaje = self._request_url('POST', 'enrol_manual_enrol_users', self.geo_token, payload)
        return mensaje

    def _request_url(self, verb, wsfunction, token, data=None):
        """Envía una petición al Web Service."""
        if verb == 'POST':
            resp = requests.post(
                f'{self.api_url}?wstoken={token}&wsfunction={wsfunction}&moodlewsrestformat=json', data=data
            )
        elif verb == 'GET':
            resp = requests.get(
                f'{self.api_url}?wstoken={token}&wsfunction={wsfunction}&moodlewsrestformat=json', params=data
            )
        else:
            raise Exception('Método HTTP no soportado')

        if not resp.ok:  # resp.status_code 200
            resp.raise_for_status()

        received_data = json.loads(resp.content.decode('utf-8'))
        if isinstance(received_data, dict) and received_data.get('exception', None):
            raise Exception(received_data.get('message'))

        return received_data
