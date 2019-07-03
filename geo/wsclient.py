import json

import requests
from annoying.functions import get_config


class WSClient:
    """
    Cliente para conectarse a los Web Services de Moodle usando el protocolo REST.

    Véase:

    - https://docs.moodle.org/37/en/Using_web_services
    - https://docs.moodle.org/dev/Creating_a_web_service_client
    - https://docs.moodle.org/dev/Web_service_API_functions
    """

    geo_token = get_config("GEO_TOKEN")
    api_url = get_config("API_URL")
    geodaws_token = get_config("GEODAWS_TOKEN")

    def crear_curso(self, datos_curso):
        """
        Crea nuevo curso en Moodle con los datos indicados.

        Devuelve una estructura como ésta:
        {'id': 181, 'shortname': '107_356_68500_99_2018'}
        """

        payload = {}
        for clave, valor in datos_curso.items():
            payload[f"courses[0][{clave}]"] = valor
        datos_recibidos = self._request_url(
            "POST", "core_course_create_courses", self.geo_token, payload
        )
        return datos_recibidos[0]

    def automatricular(self, asignatura, curso):
        """
        Crea un registro en la tabla `sigma` de Moodle para matricular automáticamente
        los estudiantes de un plan-centro-asignatura-grupo-año.
        """
        payload = {}
        payload["curso_id_nk"] = curso.id_nk
        payload["asignatura_id_nk"] = asignatura.asignatura_id
        payload["cod_grupo_asignatura"] = asignatura.cod_grupo_asignatura
        payload["plan_id_nk"] = asignatura.plan_id_nk
        payload["centro_id"] = asignatura.centro_id
        mensaje = self._request_url(
            "POST", "local_geodaws_matricula", self.geodaws_token, payload
        )
        return mensaje

    def _request_url(self, verb, wsfunction, token, data=None):
        """Envía una petición al Web Service."""

        if verb == "POST":
            resp = requests.post(
                f"{self.api_url}?wstoken={token}&wsfunction={wsfunction}"
                "&moodlewsrestformat=json",
                data=data,
            )
        elif verb == "GET":
            resp = requests.get(
                f"{self.api_url}?wstoken={token}&wsfunction={wsfunction}"
                "&moodlewsrestformat=json",
                params=data,
            )
        else:
            raise Exception("Método HTTP no soportado")

        if resp.ok:  # resp.status_code 200
            received_data = json.loads(resp.content.decode("utf-8"))
            if isinstance(received_data, dict) and received_data.get("exception", None):
                raise Exception(received_data.get("message"))

            return received_data
        else:
            resp.raise_for_status()
