Gestión de la Enseñanza Online
==============================

Aplicación para crear cursos en Moodle 3, desarrollada en Python 3 y Django 2.

Descripción
-----------

En la instalaciónd de Moodle de la Universidad de Zaragoza sólo puede crear cursos
directamente la dirección del Campus Virtual.

Esta aplicación permite a los usuarios crear/solicitar cursos en Moodle.

Hay 2 tipos de cursos:

- correspondientes a asignaturas dadas de alta en Sigma - se crean inmediatamente
- no reglados - deben ser autorizados por la dirección del Campus Virtual

En la aplicación está cargado el Plan de Ordenación Docente.  Cuando un PDI inicia
sesión, se le muestran las asignaturas de las que es docente, para que pueda crear un
curso fácilmente.  No obstante, también puede crear un curso para otra asignatura.

Las tablas de asignaturas y POD se cargan mediante una tarea ETL (Pentaho Spoon).

### Autenticación

La autenticación de los usuarios es vía _Single Sign On_ (SAML), usando el NIP y la
contraseña administrativa.

### Autorización

Los usuarios autorizados a crear/solicitar cursos en Moodle son:

- el Personal Docente e Investigador de la Universidad de Zaragoza y sus centros adscritos
- el Personal de Administración y Servicios

Los colectivos a los que pertenece el usuario se obtienen de Gestión de Identidades.

Las solicitudes de cursos no reglados deben ser aprobadas o rechazadas por la dirección
del Campus Virtual, que tiene el rol «Gestor» en la aplicación.

### Categorías

Cada curso pertenece a una categoría. Las categorías se organizan jerárquicamente:
curso académico > centro o departamento > plan de estudios

En GEO (la versión anterior de esta aplicación), al empezar el año académico se creaban
todas las posibles categorías mediante unas órdenes SQL.  A continuación había que
crearlas en la plataforma, lanzando un comando de consola de Yii.
De esta manera, se creaban muchas categorías que no se usaban, y que ralentizaban la
plataforma.  Además había que repetir el proceso en varias ocasiones, porque la oferta
académica no solía estar completa en fecha.  Si la categoría de una asignatura no estaba
creada, el curso se creaba en la categoría «Miscelánea».

En Geoda, al crear un curso se crea también la categoría correspondiente a la asignatura
si no existía previamente, así como sus categorías superiores si fuera necesario.
También se crea la categoría en la plataforma, mediante un _Web Service_
(`core_course_create_categories`).

### Creación de cursos

Se crean en la plataforma por medio de un _Web Service_ (`core_course_create_courses`).

El servicio web devuelve el ID del curso creado, así como su URL.
Este ID, junto con el creador del curso, se guarda en la tabla `profesor_curso`, y se
se muestran también en la vista `MoodleProfesores`.

Moodle utiliza, en cada inicio de sesión, el tipo de matriculación «Base de Datos Externa»
(contra la vista `MoodleProfesores`) para determinar si el usuario es profesor de algún
curso, y en su caso matricularle.  Al creador del curso, al estar en esta BD, no se le
puede quitar de profesor del curso.

> TODO: Utilizar un WS para matricular al creador del curso y eliminar esta dependencia.

### Usuarios externos a la UZ

Una pasarela noctura crea en Moodle los usuarios para los PDI/PAS activos.

Para que un usuario ajeno a la universidad pueda participar en un curso:

1. El usuario debe autorregistrarse para obtener un Número de Identificación Personal (NIP).
2. Un PDI/PAS debe, desde esta aplicación, establecer una vinculación en Gestión de Identidades de ese usuario con Moodle.
3. El docente debe matricular al usuario en el curso, con el rol apropiado.

> TODO: Crear el usuario en Moodle mediante un WS, al hacer el paso 2.
> Que la pasarela nocturna actualice su nombre, apellidos y correo en caso de cambio.
> Que la pasarela nocturna desactive al usuario al finalizar la vinculación.
> Desactivar la creación de usuarios al vuelo al iniciar sesión por primera vez.

### Matriculación automática de alumnos

Al crear un curso en Moodle, se usa un Web Service (plugin GeodaWS) para insertar un
registro en la tabla `sigma`.

Un script PHP usa esta tabla para matricular automáticamente en los cursos Moodle a los
estudiantes matriculados en Sigm@.

> TODO: Crear un plugin de _enrolment_, con su propio tipo de matriculación.

Requisitos
----------

1. **Python 3.6 o superior**:

    ```bash
    sudo apt-get install python3 python3-dev
    ```

2. **Pip 3**, instalador de paquetes Python3:

    Se puede usar el script [`get-pip`](https://pip.pypa.io/en/stable/installing/) ó

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

    Para MariaDB/MySQL instalar el paquete `libmariadb-dev` o `libmysqlclient-dev`.
    Ejecutar `ln -s libmariadb.so.3 /usr/lib/x86_64-linux-gnu/libmariadbclient.so.18` si es necesario.

    La configuración deberá incluir, si es necesario:

    ```ini
    # innodb_file_per_table = On  # Default on MariaDB >= 5.5
    # innodb_file_format = Barracuda  # Deprecated in MariaDB 10.2
    # innodb_large_prefix  # Deprecated on MariaDB 10.2, Removed in MariaDB 10.3.1
    # innodb_default_row_format = dynamic  # Default on MariaDB >= 10.2.2
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
2. Configurar los datos para el correo, la URL del sitio, y las direcciones de los
   _Web services_ de Moodle y Gestión de Identidades.
3. Configurar los datos para el _Single Sign On_ (SAML).
4. Ejecutar

    ```bash
    pipenv shell
    ./manage.py migrate
    ./manage.py createsuperuser
    ```

5. Insertar el año académico actual en la tabla `calendario`.

    `INSERT INTO calendario(anyo, slug) VALUES (2018, 'actual');`
6. Añadir usuarios al grupo `Gestores` (incluyendo el superusuario).

Servidor web para desarrollo
----------------------------

```bash
pipenv shell
./manage.py runserver [<IP>:[:<puerto>]]
```
