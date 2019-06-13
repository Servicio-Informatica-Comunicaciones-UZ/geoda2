Gestión de Enseñanza Online en Django 2
=======================================
# Instalación

**Python 3**:

```bash
sudo apt-get install python3
```

**Pip 3**, instalador de paquetes Python3:

```bash
sudo apt-get install -y python3-pip
```

**PipEnv** para virtualizar los paquetes Python y facilitar el trabajo:

```bash
sudo apt install software-properties-common python-software-properties
sudo add-apt-repository ppa:pypa/ppa
sudo apt update
sudo apt install pipenv
```

**Repositorio**:
```bash
git clone https://gitlab.unizar.es/680350/geoda2.git
```
Vamos dentro de la carpeta,
```bash
cd geoda2
```
Ejecutamos el *shell* de PipEnv, y arrancamos el servidor web:
```bash
pipenv shell
python3 manage.py runserver
```

**Resultado**:
```
...
...
March 15, 2019 - 13:17:52
Django version 2.1, using settings 'geoda_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```
