# standard library
from time import time

# third-party
from annoying.functions import get_config, get_object_or_None

# Django
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# local Django
from .wsclient import WSClient


class Asignatura(models.Model):
    """Este modelo representa una asignatura Sigma, de un estudio reglado.

    La tabla se carga mediante una tarea ETL (Pentaho Spoon).
    """

    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plan'))
    nombre_estudio = models.CharField(max_length=254, blank=True, null=True, verbose_name=_('Estudio'))
    centro_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. centro'))
    nombre_centro = models.CharField(max_length=150, blank=True, null=True, verbose_name=_('Centro'))
    tipo_estudio_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. tipo estudio'))
    nombre_tipo_estudio = models.CharField(max_length=30, blank=True, null=True, verbose_name=_('Tipo de estudio'))
    asignatura_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. asignatura'))
    nombre_asignatura = models.CharField(max_length=120, blank=True, null=True, verbose_name=_('Asignatura'))
    prela_cu = models.CharField(max_length=5, blank=True, null=True)
    tipo_periodo = models.CharField(max_length=1, blank=True, null=True, verbose_name=_('Tipo de periodo'))
    valor_periodo = models.CharField(max_length=2, blank=True, null=True, verbose_name=_('Periodo'))
    cod_grupo_asignatura = models.IntegerField(blank=True, null=True, verbose_name=_('Grupo'))
    turno = models.CharField(max_length=1, blank=True, null=True)
    tipo_docencia = models.IntegerField(blank=True, null=True, verbose_name=_('Tipo de docencia'))
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name=_('Año académico'))
    edicion = models.IntegerField(blank=True, null=True, verbose_name=_('Edición'))

    class Meta:
        db_table = 'asignatura'
        unique_together = (('plan_id_nk', 'asignatura_id', 'cod_grupo_asignatura', 'centro_id', 'anyo_academico'),)
        verbose_name = _('asignatura SIGM@')
        verbose_name_plural = _('asignaturas SIGM@')

    def get_categoria(self):
        """Devuelve la categoría correspondiente a esta asignatura.

        Si no existe previamente, se crea la categoría (y sus categorías superiores).
        """
        categoria = get_object_or_None(
            Categoria, plan_id_nk=self.plan_id_nk, centro_id=self.centro_id, anyo_academico=self.anyo_academico
        )
        if not categoria:
            categoria = Categoria.crear_desde_asignatura(self)
        return categoria

    def get_shortname(self):
        """Devuelve el nombre corto que tendrá el curso de esta asignatura en Moodle."""
        return (
            f'{self.centro_id}_{self.plan_id_nk}_{self.asignatura_id}_'
            f'{self.cod_grupo_asignatura}_{self.anyo_academico}'
        )


class Calendario(models.Model):
    """Este modelo almacena el año académico actual."""

    anyo = models.PositiveSmallIntegerField(verbose_name=_('Año académico'), default=2019)
    slug = models.SlugField(unique=True, default='actual')

    class Meta:
        db_table = 'calendario'
        permissions = [('calendario', _('Puede modificar el año académico actual.'))]


class Pod(models.Model):
    """Correspondencia entre asignaturas regladas y profesores.

    Establecida en el Plan de Ordenación Docente.
    La tabla se carga mediante una tarea ETL (Pentaho Spoon).
    """

    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name='Cód. plan')
    centro_id = models.IntegerField(blank=True, null=True, verbose_name='Cód. centro')
    asignatura_id = models.IntegerField(blank=True, null=True, verbose_name='Cód. asignatura')
    cod_grupo_asignatura = models.IntegerField(blank=True, null=True, verbose_name='Grupo')
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name='Año académico')
    nip = models.CharField(max_length=10, blank=True, null=True, verbose_name='NIP')
    apellido1 = models.CharField(max_length=32, blank=True, null=True, verbose_name='Primer apellido')
    apellido2 = models.CharField(max_length=32, blank=True, null=True, verbose_name='Segundo apellido')
    nombre = models.CharField(max_length=32, blank=True, null=True, verbose_name='Nombre')
    tipo_docencia = models.IntegerField()

    class Meta:
        db_table = 'pod'
        index_together = ['nip', 'anyo_academico']

    def __str__(self):
        return '{0} {1} {2} {3}'.format(self.anyo_academico, self.plan_id_nk, self.asignatura_id, self.nip)

    # Alternative: https://pypi.org/project/django-composite-foreignkey/
    def get_asignatura(self):
        """Devuelve el modelo Asignatura correspondiente a este registro."""
        asig = Asignatura.objects.get(
            anyo_academico=self.anyo_academico,
            centro_id=self.centro_id,
            plan_id_nk=self.plan_id_nk,
            asignatura_id=self.asignatura_id,
            cod_grupo_asignatura=self.cod_grupo_asignatura,
        )
        return asig


class Categoria(models.Model):
    """
    Este modelo representa la categoría de los cursos.

    Las categorías son jerárquicas:
    Curso académico > Centro o departamento > Estudio
    """

    NO_REGLADAS = (
        'Biblioteca',
        'CIRCE',
        'Coordinación',
        'CULM',
        'Curso P.A.S.',
        'Cursos 2019-2020',
        'EPJ',
        'Formación',
        'ICE',
        'Miscelánea',
        'POUZ',
        'Proyectos de innovacion',
        'Trabajos finales y prácticas externas',
        'UEZ',
        'Universa',
    )

    plataforma_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plataforma'))
    id_nk = models.CharField(max_length=45, blank=True, null=True, verbose_name=_('Cód. en plataforma'))
    nombre = models.CharField(max_length=250, blank=True, null=True)
    supercategoria = models.ForeignKey(
        'self', models.PROTECT, blank=True, null=True, verbose_name=_('Categoría padre')
    )
    centro_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. centro'), db_index=True)
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plan'))
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name=_('Año académico'), db_index=True)

    class Meta:
        db_table = 'categoria'
        unique_together = (('anyo_academico', 'centro_id', 'plan_id_nk'),)
        verbose_name = _('categoría')

    @classmethod
    def crear_desde_asignatura(cls, asignatura):
        """Crea una categoría de plan de estudios para la asignatura indicada."""
        supercategoria = get_object_or_None(
            Categoria, anyo_academico=asignatura.anyo_academico, centro_id=asignatura.centro_id, plan_id_nk=None
        )
        if not supercategoria:
            supercategoria = Categoria.crear_de_centro(asignatura)
        return cls.crear(
            asignatura.anyo_academico,
            asignatura.nombre_estudio,
            supercategoria.id,
            asignatura.centro_id,
            asignatura.plan_id_nk,
        )

    @classmethod
    def crear_de_centro(cls, asignatura):
        """Crea una categoría de centro/departamento para la asignatura indicada."""
        supercategoria = get_object_or_None(
            Categoria, anyo_academico=asignatura.anyo_academico, supercategoria_id=None
        )
        if not supercategoria:
            supercategoria = Categoria.crear_de_anyo(asignatura.anyo_academico)
        return cls.crear(asignatura.anyo_academico, asignatura.nombre_centro, supercategoria.id, asignatura.centro_id)

    @classmethod
    def crear_de_anyo(cls, anyo):
        """Crea una categoría para el año indicado."""
        return cls.crear(anyo, f'Cursos {anyo}-{anyo + 1}')

    @classmethod
    def crear(cls, anyo_academico, nombre, supercategoria_id=None, centro_id=None, plan_id_nk=None):
        """Crea una categoría con los datos indicados, en la aplicación y en Moodle."""
        nueva_categoria = cls(
            plataforma_id=1,
            nombre=nombre,
            supercategoria_id=supercategoria_id,
            centro_id=centro_id,
            plan_id_nk=plan_id_nk,
            anyo_academico=anyo_academico,
        )
        nueva_categoria.save()
        nueva_categoria.crear_en_plataforma()
        return nueva_categoria

    def crear_en_plataforma(self):
        """Crea la categoría en la plataforma."""
        cliente = WSClient()
        datos_categoria = self.get_datos()
        datos_recibidos = cliente.crear_categoria(datos_categoria)
        self.id_nk = datos_recibidos['id']
        self.save()

    def get_datos(self):
        """Devuelve los datos necesarios para crear la categoría en Moodle usando WS.

        Consultar Administration → Site Administration → Plugins → Web Services →
                  API Documentation → core_course_create_categories
        """
        return {
            'name': self.nombre,
            'parent': self.supercategoria.id_nk if self.supercategoria else None,
            'idnumber': f'cat_{self.id}',
        }


class Curso(models.Model):
    """Este modelo representa un curso en Moodle.

    Pueden ser de 2 tipos:

    * correspondientes a una asignatura dada de alta en Sigma (de un estudio reglado)
    * no reglados
    """

    class Estado(models.IntegerChoices):
        """Representa los diferentes estados en los que se puede encontrar un curso."""

        SOLICITADO = 1, _('Solicitado')
        AUTORIZADO = 2, _('Autorizado')
        CREADO = 3, _('Creado')
        SUSPENDIDO = 4, _('Suspendido')
        BORRADO = 5, _('Borrado')
        DENEGADO = 6, _('Denegado')

    nombre = models.CharField(max_length=200)
    fecha_solicitud = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de solicitud'))
    fecha_autorizacion = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de autorización'))
    autorizador = models.ForeignKey('accounts.CustomUser', models.PROTECT, blank=True, null=True)
    plataforma_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plataforma'))
    id_nk = models.CharField(max_length=45, blank=True, null=True, verbose_name=_('Código en plataforma'))
    fecha_creacion = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de creación'))
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('URL'))
    categoria = models.ForeignKey(Categoria, models.PROTECT, blank=True, null=True, verbose_name=_('Categoría'))
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name=_('Año académico'))
    asignatura = models.OneToOneField(
        Asignatura, blank=True, null=True, on_delete=models.PROTECT, verbose_name=_('Asignatura')
    )
    estado = models.IntegerField(choices=Estado.choices, verbose_name=_('Estado'))
    motivo_solicitud = models.TextField(blank=True, null=True, verbose_name=_('Motivo de la solicitud'))
    comentarios = models.TextField(blank=True, null=True, verbose_name=_('Comentarios'))
    profesores = models.ManyToManyField('accounts.CustomUser', related_name='profesores', through='ProfesorCurso')

    class Meta:
        db_table = 'curso'
        ordering = ('anyo_academico', 'nombre')
        permissions = [
            ('cursos_creados', _('Puede ver el listado de cursos creados.')),
            ('cursos_pendientes', _('Puede ver el listado de cursos por aprobar.')),
        ]

    def get_absolute_url(self):
        return reverse('curso-detail', args=[self.id])

    def actualizar_tras_creacion(self, datos_recibidos):
        """Actualiza el modelo con los datos recibidos de Moodle al crear el curso."""

        self.id_nk = datos_recibidos['id']
        self.fecha_creacion = timezone.now()
        url_plataforma = get_config('URL_PLATAFORMA')
        self.url = f'{url_plataforma}/course/view.php?id={self.id_nk}'
        self.estado = Curso.Estado.CREADO
        self.save()

    def anyadir_profesor(self, usuario):
        """Añade al usuario a la lista de profesores del curso y lo matricula en Moodle."""
        cliente = WSClient()
        cliente.matricular_profesor(usuario, self)
        profesor_curso = ProfesorCurso(curso=self, profesor=usuario, fecha_alta=timezone.now())
        profesor_curso.save()

    @property
    def curso_academico(self):
        """Devuelve el curso académivo. Vg: 2019/2020"""

        if self.anyo_academico:
            return f'{self.anyo_academico}/{self.anyo_academico + 1}'
        return '—'

    def get_datos(self):
        """Devuelve los datos necesarios para crear el curso en Moodle usando WS.

        Consultar Administration → Site Administration → Plugins → Web Services →
                  API Documentation → core_course_create_courses
        """

        return {
            'fullname': self.nombre,
            'shortname': self.asignatura.get_shortname() if self.asignatura else f'NR_{self.id}',
            'categoryid': self.categoria.id_nk,  # id de la categoría en Moodle
            'idnumber': self.id,
            'visible': 1,
            # `startdate` es la hora actual más 60 segundos.
            # Así es un poco mayor que la fecha de creación en la plataforma.
            'startdate': int(time() + 60),
        }


class ProfesorCurso(models.Model):
    """Vinculación entre un curso y la persona que lo creó/solicitó."""

    id = models.AutoField(primary_key=True)
    curso = models.ForeignKey('Curso', models.PROTECT)
    profesor = models.ForeignKey('accounts.CustomUser', models.PROTECT)
    fecha_alta = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de alta'))
    fecha_baja = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de baja'))

    class Meta:
        db_table = 'profesor_curso'


class RightsSupport(models.Model):
    """Dummy auxiliary model in order to create global permissions not related to a model."""

    class Meta:
        managed = False  # No database table creation or deletion operations will be performed for this model.

        permissions = (('matricular_plan', _('Puede matricular en un curso a todos los alumnos de un plan')),)
