# standard library
import json
import sys

# third-party libraries
import requests
from annoying.functions import get_config

# Django
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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
        datos_recibidos = self._request_url(
            'POST', 'core_course_create_categories', self.geo_token, payload
        )
        return datos_recibidos[0]

    def crear_curso(self, datos_curso):
        """Crea nuevo curso en Moodle con los datos indicados.

        Devuelve una estructura como ésta:
        {'id': 181, 'shortname': '107_356_68500_99_2018'}
        """
        payload = {}
        for clave, valor in datos_curso.items():
            payload[f'courses[0][{clave}]'] = valor
        datos_recibidos = self._request_url(
            'POST', 'core_course_create_courses', self.geo_token, payload
        )
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
        respuesta = self._request_url(
            'POST', 'core_course_delete_courses', self.geo_token, payload
        )
        return respuesta

    def buscar_usuario_correo(self, usuario):
        """Busca en Moodle el usuarioCorreo correspondiente al usuario de Geoda indicado."""
        # Buscamos a un usuarioCorreo con ese NIP (idnumber) y dirección de correo.
        payload = {
            'criteria[0][key]': 'idnumber',
            'criteria[0][value]': usuario.username,
            'criteria[1][key]': 'email',
            'criteria[1][value]': usuario.email,
        }
        respuesta = self._request_url('POST', 'core_user_get_users', self.geo_token, payload)
        usuarios_moodle = respuesta['users']
        if usuarios_moodle:
            if not usuarios_moodle[0]['username'].isnumeric():
                usuario_moodle = usuarios_moodle[0]
            elif len(usuarios_moodle) > 1:
                usuario_moodle = usuarios_moodle[1]

            if usuario_moodle:
                return usuario_moodle

        # Si no se encuentra, cogemos al primer usuarioCorreo con ese NIP (idnumber),
        # aunque no coincida el correo en Moodle con el de Geoda.
        payload = {'criteria[0][key]': 'idnumber', 'criteria[0][value]': usuario.username}
        respuesta = self._request_url('POST', 'core_user_get_users', self.geo_token, payload)
        usuarios_moodle = respuesta['users']
        if usuarios_moodle:
            if not usuarios_moodle[0]['username'].isnumeric():
                usuario_moodle = usuarios_moodle[0]
            elif len(usuarios_moodle) > 1:
                usuario_moodle = usuarios_moodle[1]

            if usuario_moodle:
                return usuario_moodle

        # La tarea ETL `add_usuarios_y_matriculas` (Pentaho Spoon)
        # copia un fichero CSV con los usuarios al servidor
        # y una tarea cron los crea, por lo que no se debería llegar aquí nunca,
        # salvo que se trate de un profesor creado ese mismo día.
        raise Exception('Usuario no encontrado en Moodle.')

    def buscar_usuario_nip(self, usuario):
        """Busca en Moodle el usuarioNip correspondiente al usuario de Geoda indicado."""
        usuario_nip = self.buscar_usuario_nip_or_None(usuario.username)
        if not usuario_nip:
            raise Exception(f'Usuario {usuario.full_name} no encontrado en Moodle.')
        return usuario_nip

    def buscar_usuario_nip_or_None(self, nip):
        """Busca en Moodle el usuarioNip correspondiente al NIP indicado, o `None`."""
        payload = {
            'criteria[0][key]': 'username',
            'criteria[0][value]': nip,
        }
        respuesta = self._request_url('POST', 'core_user_get_users', self.geo_token, payload)
        usuarios_moodle = respuesta['users']
        if not usuarios_moodle:
            return None
        return usuarios_moodle[0]

    def buscar_usuarios_nip(self, nips):
        """Busca en Moodle los usuariosNip correspondientes a los NIPs indicados."""
        # Doc de `get_users_by_field`` en <sitio_moodle>/admin/webservice/documentation.php
        payload = {'field': 'username'}

        for i, nip in enumerate(nips):
            payload.update({f'values[{i}]': str(nip)})

        usuarios = self._request_url(
            'POST', 'core_user_get_users_by_field', self.geo_token, payload
        )
        return usuarios

    def desmatricular(self, usuario, curso):
        """Desmatricula a un usuario de un curso."""
        # Hasta el curso 2019-20 los profesores entraban en Moodle con su usuario de correo.
        if curso.anyo_academico < 2020:
            usuario_moodle = self.buscar_usuario_correo(usuario)
        else:
            usuario_moodle = self.buscar_usuario_nip(usuario)
        payload = {
            'usuario_id_nk': usuario_moodle['id'],
            'curso_id_nk': curso.id_nk,
        }
        ueids = self._request_url(
            'GET', 'local_geodaws_get_user_enrolments', self.geodaws_token, payload
        )

        respuestas = []
        for ueid in ueids:
            # Con `core_enrol_edit_user_enrolment` podríamos establecer una fecha de finalización,
            # pero esta función fue deprecated en la versión 3.6, por lo que dejará de funcionar en el futuro.
            # En su lugar se podría usar `core_enrol_submit_user_enrolment`,
            # pero todavía no existía en la versión 3.5 LTS que es la que usamos.
            respuesta = self._request_url(
                'POST', 'core_enrol_unenrol_user_enrolment', self.geo_token, {'ueid': ueid['id']}
            )
            respuestas.append(respuesta)

        return respuestas

    def matricular_profesor(self, usuario, curso):
        """Matricula a un usuario como profesor de un curso de Moodle."""
        try:
            usuario_moodle = self.buscar_usuario_nip(usuario)
        except Exception as ex:
            raise ex

        payload = {
            'enrolments[0][roleid]': 3,  # id del rol `editingteacher` en Moodle
            'enrolments[0][userid]': usuario_moodle['id'],
            'enrolments[0][courseid]': curso.id_nk,
            'enrolments[0][timestart]': int(timezone.now().timestamp()),
        }
        mensaje = self._request_url('POST', 'enrol_manual_enrol_users', self.geo_token, payload)
        return mensaje

    def matricular_alumnos(self, nips, curso):
        """Matricula una lista de usuarios como alumnos de un curso de Moodle."""
        if not nips:
            return 0

        usuarios_moodle = self.buscar_usuarios_nip(nips)
        if usuarios_moodle:
            # Preparamos payload con todos los usuarios de la lista de NIPs encontrados en Moodle
            payload = {}
            for i, usuario in enumerate(usuarios_moodle):
                payload.update(
                    {
                        f'enrolments[{i}][roleid]': 5,  # id del rol `Student` en Moodle
                        f'enrolments[{i}][userid]': usuario['id'],
                        f'enrolments[{i}][courseid]': curso.id_nk,
                        f'enrolments[{i}][timestart]': int(timezone.now().timestamp()),
                    }
                )
            # Matriculamos en el curso a los usuarios encontrados
            self._request_url('POST', 'enrol_manual_enrol_users', self.geo_token, payload)

        return len(usuarios_moodle)

    def _request_url(self, verb, wsfunction, token, data=None):  # noqa: C901
        """Envía una petición al Web Service."""
        try:
            if verb == 'POST':
                resp = requests.post(
                    f'{self.api_url}?wstoken={token}&wsfunction={wsfunction}'
                    '&moodlewsrestformat=json',
                    data=data,
                )
                resp.raise_for_status()

            elif verb == 'GET':
                resp = requests.get(
                    f'{self.api_url}?wstoken={token}&wsfunction={wsfunction}'
                    '&moodlewsrestformat=json',
                    params=data,
                )
                resp.raise_for_status()

            else:
                raise Exception('Método HTTP no soportado')

        except requests.exceptions.SSLError:
            raise requests.exceptions.SSLError(
                'No fue posible verificar el certificado SSL de Moodle'
            )
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.ConnectionError('No fue posible conectar con Moodle')
        except requests.exceptions.HTTPError:
            raise requests.exceptions.HTTPError('Moodle devolvió una respuesta HTTP no válida')
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout('Moodle no respondió')
        except requests.exceptions.TooManyRedirects:
            raise requests.exceptions.TooManyRedirects('Demasiadas redirecciones')
        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException(
                _('Problema desconocido al enviar la petición a Moodle (%(info)s)')
                % {'info': sys.exc_info()[0]}
            )

        try:
            received_data = json.loads(resp.content.decode('utf-8'))
        except json.JSONDecodeError:
            raise Exception(
                _('La respuesta del servidor Moodle no es un JSON válido: %(contenido)s')
                % {'contenido': resp.content.decode('utf-8')}
            )

        if isinstance(received_data, dict) and received_data.get('exception', None):
            raise Exception(received_data.get('message'))

        return received_data
