Gestión de la Enseñanza Online
==============================

Aplicación para crear cursos en Moodle 3, desarrollada en Python 3 y Django 3.

Descripción
-----------

En la instalación de Moodle de la Universidad de Zaragoza sólo puede crear cursos
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

- Cursos 2019-2020
  - Facultades y Departamentos, incluyendo «Escuela de Doctorado»
    - Grados, Másteres, Diplomas, etc
  - No reglada
    - Biblioteca, CUD, CULM, Curso P.A.S., etc
  - Varios

En GEO (la versión anterior de esta aplicación), al empezar el año académico se creaban
todas las posibles categorías mediante unas órdenes SQL.  A continuación había que
crearlas en la plataforma, lanzando un comando de consola de Yii (`creaTodasCategoriasAdd`).

De esta manera, se creaban muchas categorías que no se usaban, y que ralentizaban la
plataforma.  Además había que repetir el proceso en varias ocasiones, porque la oferta
académica no solía estar completa en fecha.  Si la categoría de una asignatura no estaba
creada, el curso se creaba en la categoría «Miscelánea».

En Geoda, al crear un curso se crea también la categoría correspondiente a la asignatura
si no existía previamente, así como sus categorías superiores si fuera necesario.
También se crea la categoría en la plataforma, mediante un _Web Service_
(función `core_course_create_categories`).

### Creación de cursos

Se crean en la plataforma por medio de un _Web Service_ (función `core_course_create_courses`).
En la tabla `mdl_course` el campo `shortname` sigue el patrón `centro_plan_asignatura_grupo_año`,
y el campo `idnumber` almacena el `id` en la tabla curso de Geoda. Para los no reglados
el nombre corto es `NR_{idnumber}`.
El servicio web devuelve el ID del curso creado, así como su URL, y se guardan en la tabla `curso`.

El creador del curso se guarda en la tabla `profesor_curso`.
Se utiliza la función `core_user_enrol_users` para matricular al usuario como profesor
del curso en Moodle.

Con GEO, Moodle utilizaba, en cada inicio de sesión, el tipo de matriculación «Base de Datos Externa»
(contra la vista `MoodleProfesores`) para determinar si el usuario era profesor de algún
curso, y en su caso matricularlo.  Al creador del curso, al estar en esta BD, no se le
podía quitar de profesor del curso.

Posteriormente, los gestores pueden añadir o quitar profesores, para lo que se usan las
funciones `enrol_manual_enrol_users` y `core_enrol_unenrol_user_enrolment`.

Todos los que sean profesores de algún curso son alumnos del curso 49 («Apoyo Docente al ADD»).
Para ello hay una vista (`ApoyoDocente`) de todos los que tienen algún rol profesor en algún
curso, que se usa con el tipo de matriculación «Base de Datos Externa».

### Usuarios

En Administración del Sitio → Extensiones → Identificación están habilitados 4 tipos de validación:

- Cuentas manuales (administrador, miembros de RAMU)
- LDAP (general)
- Usar una base de datos externa (con Geo para los usuarios invitados)
- Moodle Network (para que Mahara use los usuarios de Moodle)

Una pasarela nocturna copia al servidor un fichero CSV con los datos de los PDI/PAS activos.
Una tarea cron ejecuta el script en PHP `create_moodle_users` para crear los usuarios en Moodle.

> TODO: La pasasela no debería pasar todos los usuarios, sino solamente los que tengan derecho
> a usar el Moodle (PAS, PDI, ADS, EST matriculados, usuarios invitados, auditores externos).
> Comprobar si este proceso actualiza su nombre, apellidos y correo en caso de cambio.
> Hacer que este proceso compruebe las vinculaciones externas y desactive al usuario al finalizar la vinculación.

#### Usuarios externos a la UZ

Para que un usuario ajeno a la universidad pueda participar en un curso:

1. El usuario debe autorregistrarse en Gestión de Identidades para obtener un Número de Identificación Personal (NIP).
2. Un PDI/PAS debe, desde esta aplicación, establecer una vinculación en G.I. de ese usuario con Moodle.
3. El docente debe matricular al usuario en el curso, con el rol apropiado.

> TODO: Al hacer el paso 2, crear el usuario en Moodle mediante un WS, con el email de G.I.,
> y desactivar la creación de usuarios al vuelo al iniciar sesión por primera vez.
> TODO: Crear un código de vinculacion para el RAMU (¿sin caducidad?)

Con GEO, el PDI invitaba al usuario externo, creándose en GEO un usuario con el rol `forano`.
Los usuarios se creaban al vuelo cuando entraban por primera vez a Moodle, con autenticación contra una BD externa (la vista `MoodleUsers` de la BD de Geo).
No se podían matricular hasta que entraban en la plataforma.

### Matriculación automática de alumnos

Al crear un curso en Moodle, se usa un Web Service (plugin GeodaWS) para insertar un
registro en la tabla `sigma`.

Una tarea cron ejecuta cada noche un script PHP (`cargasigma`) que usa esta tabla
y el fichero `alumnos_asignaturas.dat` creado por una pasarela ETL (Pentaho Spoon) para
matricular automáticamente en los cursos Moodle a los estudiantes matriculados en Sigm@.

> TODO: Crear un plugin de _enrolment_, con su propio tipo de matriculación.

Instalación sobre contenedores Docker
-------------------------------------

El servidor Moodle debe tener instalado el plugin GeodaWS.
Además, en Site administration → Plugins → Web services → External Services debe haber
un servicio personalizado (geo) con las funciones necesarias (`core_course_create_categories`,
`core_course_create_courses`, `core_user_get_users`, `enrol_manual_enrol_users`,
`core_enrol_unenrol_user_enrolment`).

1. Copiar o renombrar los ficheros `env/common.env-sample` y `env/geoda2.env-sample`.
2. Configurar los ajustes de la base de datos, servidor de correo, la URL del sitio,
   _Single Sign On_ (SAML) y las direcciones de los _Web services_ de Moodle y de
   Gestión de Identidades en los ficheros `.env`.
3. Levantar los contenedores:
   `docker-compose up -d`
4. Crear el usuario administrador:

   ```bash
   docker-compose exec web ./manage.py createsuperuser
   ```

5. Insertar el año académico actual en la tabla `calendario`.

    ```bash
    docker-compose exec db bash -c 'echo "INSERT INTO calendario(anyo, slug) VALUES (2019, '\''actual'\'');" | mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}'
    ```

6. Entrar como administrador en la interfaz web, y añadir usuarios al grupo `Gestores` (incluyendo el superusuario).

7. Activar a los usuarios gestores el atributo `is_staff` para que puedan acceder
   a la interfaz de administración.

Instalación sobre hierro
------------------------

### Requisitos

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

### Instalación

```bash
git clone https://gitlab.unizar.es/add/geoda2.git
cd geoda2
pipenv [--python 3.7] install [--dev]
```

### Configuración inicial

1. Configurar las bases de datos.
2. Configurar los datos para el correo, la URL del sitio, y las direcciones de los
   _Web services_ de Moodle y Gestión de Identidades.
3. Configurar los datos para el _Single Sign On_ (SAML).
4. Ejecutar

    ```bash
    pipenv shell
    set -a; . env/common.env; ./env/geoda2.env; set +a
    ./manage.py migrate
    ./manage.py createsuperuser
    ```

5. Insertar el año académico actual en la tabla `calendario`.

    `INSERT INTO calendario(anyo, slug) VALUES (2019, 'actual');`
6. Añadir usuarios al grupo `Gestores` (incluyendo el superusuario).

7. Activar a los usuarios gestores el atributo `is_staff` para que puedan acceder
   a la interfaz de administración.

### Servidor web para desarrollo

```bash
pipenv shell
export DJANGO_SETTINGS_MODULE=geoda_project.settings-dev
./manage.py runserver [<IP>:[:<puerto>]]
```
