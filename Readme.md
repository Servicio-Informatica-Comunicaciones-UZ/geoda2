Gestión de la Enseñanza Online
==============================

Aplicación para crear cursos en Moodle 3, desarrollada en Python 3 y Django 2.

Requisitos
----------

1. **Python 3.6 o superior**:

    ```bash
    sudo apt-get install python3
    ```

2. **Pip 3**, instalador de paquetes Python3:

    Se puede usar el script [get-pip](https://pip.pypa.io/en/stable/installing/) ó

    ```bash
    sudo apt-get install -y python3-pip
    ```

3. **PipEnv** para virtualizar los paquetes Python y facilitar el trabajo:

    Se puede instalar con `sudo -H pip3 install pipenv` ó

    ```bash
    sudo apt install software-properties-common python-software-properties
    sudo add-apt-repository ppa:pypa/ppa
    sudo apt update
    sudo apt install pipenv
    ```

4. Paquetes `libxmlsec1-dev` y `pkg-config`
5. **Servidor de bases de datos** aceptado por Django (vg PostgreSQL o MariaDB).

    Para MariaDB/MySQL instalar el paquete `libmariadbclient-dev` o `libmysqlclient-dev`. La configuración deberá incluir:

    ```ini
    innodb_file_per_table
    innodb_file_format = Barracuda
    innodb_large_prefix
    innodb_default_row_format = dynamic
    ```

Instalación
-----------

```bash
git clone https://gitlab.unizar.es/add/geoda2.git
cd geoda2
pipenv [--python 3.7] install [--dev]
```

Configuración inicial
---------------------

1. Configurar las bases de datos en el fichero `.env` y la sección `DATABASES` de `geoda_project/settings.py`.
2. Configurar los datos para el correo, y la URL del sitio.
3. Configurar los datos para el _Single Sign On_ (SAML).
4. Ejecutar

    ```bash
    pipenv shell
    ./manage.py migrate
    ./manage.py createsuperuser
    ```

Servidor web para desarrollo
----------------------------

```bash
pipenv shell
./manage.py runserver [<IP>:[:<puerto>]]
```
