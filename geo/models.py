# Standard library
from time import time

# Third-party
from annoying.functions import get_config, get_object_or_None

# Django
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Local Django
from .wsclient import WSClient


class Asignatura(models.Model):
    """Este modelo representa un grupo de una asignatura Sigma, de un estudio reglado.

    La tabla se carga mediante una tarea ETL (Pentaho Spoon).
    """

    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plan'))
    nombre_estudio = models.CharField(
        max_length=254, blank=True, null=True, verbose_name=_('Estudio')
    )
    centro_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. centro'))
    nombre_centro = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_('Centro')
    )
    tipo_estudio_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Cód. tipo estudio')
    )
    nombre_tipo_estudio = models.CharField(
        max_length=30, blank=True, null=True, verbose_name=_('Tipo de estudio')
    )
    asignatura_id = models.IntegerField(
        blank=True, db_index=True, null=True, verbose_name=_('Cód. asignatura')
    )
    nombre_asignatura = models.CharField(
        blank=True, db_index=True, max_length=120, null=True, verbose_name=_('Asignatura')
    )
    prela_cu = models.CharField(max_length=5, blank=True, null=True)
    tipo_periodo = models.CharField(
        max_length=1, blank=True, null=True, verbose_name=_('Tipo de periodo')
    )
    valor_periodo = models.CharField(
        max_length=2, blank=True, null=True, verbose_name=_('Periodo')
    )
    cod_grupo_asignatura = models.IntegerField(
        blank=True, null=True, verbose_name=_('Cód. grupo de la asignatura')
    )
    turno = models.CharField(max_length=1, blank=True, null=True)
    tipo_docencia = models.IntegerField(blank=True, null=True, verbose_name=_('Tipo de docencia'))
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name=_('Año académico'))
    edicion = models.IntegerField(blank=True, null=True, verbose_name=_('Edición'))

    class Meta:
        db_table = 'asignatura'
        unique_together = (
            ('plan_id_nk', 'asignatura_id', 'cod_grupo_asignatura', 'centro_id', 'anyo_academico'),
        )
        verbose_name = _('asignatura SIGM@')
        verbose_name_plural = _('asignaturas SIGM@')

    def get_categoria(self):
        """Devuelve la categoría correspondiente a esta asignatura.

        Si no existe previamente, se crea la categoría (y sus categorías superiores).
        """
        categoria = get_object_or_None(
            Categoria,
            plan_id_nk=self.plan_id_nk,
            centro_id=self.centro_id,
            anyo_academico=self.anyo_academico,
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

    def get_profesores(self):
        """Devuelve los usuarios que son docentes de la asignatura según el POD."""
        pods = Pod.objects.filter(
            anyo_academico=self.anyo_academico,
            asignatura_id=self.asignatura_id,
            cod_grupo_asignatura=self.cod_grupo_asignatura,
            centro_id=self.centro_id,
            plan_id_nk=self.plan_id_nk,
        )
        profesores = [pod.get_usuario_or_None() for pod in pods]
        # Si llegara una asignación a un NIP que no exista en la tabla de usuarios, la omitimos.
        profesores = list(filter(None, profesores))
        return profesores


class Calendario(models.Model):
    """Este modelo almacena el año académico actual."""

    anyo = models.PositiveSmallIntegerField(verbose_name=_('Año académico'), default=2019)
    slug = models.SlugField(unique=True, default='actual')

    class Meta:
        db_table = 'calendario'
        permissions = [('calendario', _('Puede modificar el año académico actual.'))]


class Categoria(models.Model):
    """
    Este modelo representa la categoría de los cursos.

    Las categorías son jerárquicas:
    Curso académico > Centro o departamento > Estudio
    """

    NO_REGLADAS = (
        'Actividades académicas complementarias',
        'Biblioteca',
        'CIFICE',
        'CIRCE',
        'Coordinación',
        'CULM',
        'Curso P.A.S.',
        'EPJ',
        # La Escuela de Doctorado tiene una categoría normal, con 1 curso por cada PD,
        # y esta categoría NR para actividades de formación transversal y específica.
        'Escuela de Doctorado',
        'Formación',
        'Miscelánea',
        'POUZ',
        'Proyectos de innovacion',
        'Trabajos finales y prácticas externas',
        'UEZ',
        'Universa',
    )

    plataforma_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plataforma'))
    id_nk = models.CharField(
        max_length=45, blank=True, null=True, verbose_name=_('Cód. en plataforma')
    )
    nombre = models.CharField(max_length=250, blank=True, null=True)
    supercategoria = models.ForeignKey(
        'self', models.PROTECT, blank=True, null=True, verbose_name=_('Categoría padre')
    )
    centro_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Cód. centro'), db_index=True
    )
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plan'))
    anyo_academico = models.IntegerField(
        blank=True, null=True, verbose_name=_('Año académico'), db_index=True
    )

    class Meta:
        db_table = 'categoria'
        unique_together = (('anyo_academico', 'centro_id', 'plan_id_nk'),)
        verbose_name = _('categoría')

    def __str__(self):
        return f'{self.anyo_academico} {self.get_centro_id_display()} {self.nombre}'

    def get_centro_id_display(self):
        return self.centro_id or '—'

    @classmethod
    def crear_desde_asignatura(cls, asignatura):
        """Crea una categoría de plan de estudios para la asignatura indicada."""
        supercategoria = get_object_or_None(
            Categoria,
            anyo_academico=asignatura.anyo_academico,
            centro_id=asignatura.centro_id,
            plan_id_nk=None,
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
        return cls.crear(
            asignatura.anyo_academico,
            asignatura.nombre_centro,
            supercategoria.id,
            asignatura.centro_id,
        )

    @classmethod
    def crear_de_anyo(cls, anyo):
        """Crea una categoría para el año indicado."""
        return cls.crear(anyo, f'Cursos {anyo}-{anyo + 1}')

    @classmethod
    def crear(
        cls, anyo_academico, nombre, supercategoria_id=None, centro_id=None, plan_id_nk=None
    ):
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


class Centro(models.Model):
    """
    Modelo que representa un centro de estudios.

    `id` es el código del centro en Sigma.
    """

    id = models.PositiveSmallIntegerField(_('cód. académico'), primary_key=True)
    nombre = models.CharField(max_length=255)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    esta_activo = models.BooleanField(_('¿Activo?'), default=False)

    class Meta:
        db_table = 'centro'
        ordering = ['nombre']

    def __str__(self):
        return f'{ self.nombre } ({ self.id })'


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

    nombre = models.CharField(
        max_length=200,
        help_text=_(
            'El nombre del curso no se puede cambiar,'
            ' así que debe ser descriptivo y diferenciable de otros.'
        ),
        verbose_name=_('Nombre del curso'),
    )
    solicitante = models.ForeignKey(
        'accounts.CustomUser',
        models.PROTECT,
        blank=True,
        null=True,
        related_name='cursos_solicitados',
    )
    fecha_solicitud = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Fecha de solicitud')
    )
    fecha_autorizacion = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Fecha de autorización')
    )
    autorizador = models.ForeignKey(
        'accounts.CustomUser',
        models.PROTECT,
        blank=True,
        null=True,
        related_name='cursos_autorizados',
    )
    plataforma_id = models.IntegerField(blank=True, null=True, verbose_name=_('Cód. plataforma'))
    id_nk = models.CharField(
        max_length=45, blank=True, null=True, verbose_name=_('Código en plataforma')
    )
    fecha_creacion = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Fecha de creación')
    )
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('URL'))
    categoria = models.ForeignKey(
        Categoria, models.PROTECT, blank=True, null=True, verbose_name=_('Categoría')
    )
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name=_('Año académico'))
    asignatura = models.OneToOneField(
        Asignatura,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='curso',
        verbose_name=_('Asignatura'),
    )
    estado = models.IntegerField(choices=Estado.choices, verbose_name=_('Estado'))
    motivo_solicitud = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Motivo de la solicitud'),
        help_text=_(
            'Razón por la que se solicita el curso como no reglado, '
            'justificación de su creación y público al que va dirigido.'
        ),
    )
    comentarios = models.TextField(blank=True, null=True, verbose_name=_('Comentarios'))
    profesores = models.ManyToManyField(
        'accounts.CustomUser', related_name='cursos', through='ProfesorCurso'
    )  # NOTA: Incluye los que hayan sido dados de baja.

    class Meta:
        db_table = 'curso'
        ordering = ('anyo_academico', 'nombre')
        permissions = [
            ('cursos_todos', _('Puede ver el listado de todos los cursos.')),
            ('cursos_pendientes', _('Puede ver el listado de cursos por aprobar.')),
            ('curso_administrar', _('Puede acceder a la interfaz de administración de Curso.')),
            ('curso_delete', _('Puede eliminar cursos.')),
            ('curso_historial', _('Puede ver el histórico de profesores de un curso.')),
        ]

    def __str__(self):
        return f'{self.nombre}'

    def get_absolute_url(self):
        return reverse('curso_detail', args=[self.id])

    def actualizar_tras_creacion(self, datos_recibidos):
        """Actualiza el modelo con los datos recibidos de Moodle al crear el curso."""

        self.id_nk = datos_recibidos['id']
        self.fecha_creacion = timezone.now()
        url_plataforma = get_config('URL_PLATAFORMA')
        self.url = f'{url_plataforma}/course/view.php?id={self.id_nk}'
        self.estado = Curso.Estado.CREADO
        self.save()

    def anyadir_profesor(self, usuario):
        """Añade al usuario a la lista de profesores del curso en GEO, y lo matricula en Moodle."""
        cliente = WSClient()
        cliente.matricular_profesor(usuario, self)
        pc = ProfesorCurso.objects.create(curso=self, profesor=usuario, fecha_alta=timezone.now())
        return pc

    def borrar_en_plataforma(self):
        """Borra el curso en Moodle."""
        cliente = WSClient()
        return cliente.borrar_curso(curso=self)

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
            'fullname': f'{self.nombre} ({self.curso_academico})'
            if self.asignatura
            else f'{self.nombre}',  # A los cursos no reglados no se les añade el curso académico
            'shortname': self.asignatura.get_shortname() if self.asignatura else f'NR_{self.id}',
            'categoryid': self.categoria.id_nk,  # id de la categoría en Moodle
            'idnumber': self.id,
            'visible': 1,
            # `startdate` es la hora actual más 60 segundos.
            # Así es un poco mayor que la fecha de creación en la plataforma.
            'startdate': int(time() + 60),
        }

    @property
    def profesores_activos(self):
        """Devuelve los usuarios que están dados de alta como profesores del curso."""
        asignaciones = self.profesorcurso_set.filter(
            Q(fecha_baja__gt=timezone.now()) | Q(fecha_baja=None)
        ).select_related('profesor')
        profesores = [asignacion.profesor for asignacion in asignaciones]
        return profesores


class Estudio(models.Model):
    """
    Modelo para representar un estudio.

    `id` es el código del estudio en Sigma.
    """

    id = models.PositiveIntegerField(_('Cód. estudio'), primary_key=True)
    nombre = models.CharField(max_length=255)
    # Los EEPP tienen un código (tablas TCS de Sigma) pero no tienen realmente planes ni estudios.
    # Creamos un estudio ficticio para cada estudio propio,
    # dándole como `id` el `cod_ep` precedido de un `9` para evitar posibles colisiones.
    cod_ep = models.PositiveSmallIntegerField(_('Cód. estudio propio'), null=True)
    esta_activo = models.BooleanField(_('¿Activo?'), default=True)

    class Meta:
        db_table = 'estudio'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Forano(models.Model):
    """Usuario invitado, que no es profesor, PAS ni estudiante de la Universidad."""

    class Estado(models.IntegerChoices):
        """Representa los estados en los que se puede encontrar una solicitud de vinculación."""

        SOLICITADO = 1, _('Solicitado')
        DENEGADO = 2, _('Denegado')
        AUTORIZADO = 3, _('Autorizado')

        __empty__ = _('Cualquiera')

    nip = models.PositiveIntegerField(
        verbose_name=_('NIP a vincular'),
        help_text=_('Número de Identificación Personal del usuario a vincular.'),
        validators=[MinValueValidator(100_001), MaxValueValidator(9_999_999)],
    )
    nombre = models.CharField(
        max_length=127,
        verbose_name=_('Nombre y apellidos'),
        help_text=_('Nombre y apellidos del usuario a vincular.'),
    )
    email = models.EmailField(
        _('correo electrónico'),
        help_text=_('Dirección de correo electrónico del usuario a vincular'),
        null=True,
    )
    fecha_solicitud = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Fecha de solicitud')
    )
    fecha_autorizacion = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Fecha de autorización')
    )
    estado = models.IntegerField(choices=Estado.choices, verbose_name=_('Estado'))
    motivo_solicitud = models.TextField(
        verbose_name=_('Motivación de la solicitud'),
        help_text=_(
            'Quién es el usuario externo, motivos por los que solicita su vinculación a Moodle, '
            'así como el curso en el que participaría y con qué rol.'
        ),
    )
    comentarios = models.TextField(blank=True, null=True, verbose_name=_('Comentarios'))
    autorizador = models.ForeignKey(
        'accounts.CustomUser',
        models.PROTECT,
        blank=True,
        null=True,
        related_name='foranos_resueltos',
    )
    # curso = models.ForeignKey(
    #     Curso, models.PROTECT, blank=True, null=True, verbose_name=_('Curso')
    # )
    solicitante = models.ForeignKey(
        'accounts.CustomUser',
        models.PROTECT,
        blank=True,
        null=True,
        related_name='foranos_solicitados',
    )

    class Meta:
        db_table = 'forano'
        ordering = ('-fecha_solicitud',)
        permissions = [('forano', _('Puede ver y resolver las solicitudes de vinculación.'))]

    def get_absolute_url(self):
        return reverse('forano_detail', args=[self.id])


class MatriculaAutomatica(models.Model):
    """Matrícula automática en cursos de Moodle con los datos de matriculación de Sigma"""

    id = models.BigAutoField(primary_key=True)
    courseid = models.PositiveBigIntegerField(db_index=True)
    active = models.BooleanField(_('¿Activo?'), default=True)
    fijo = models.BooleanField(_('¿Registro predefinido?'), default=False)

    asignatura_id = models.IntegerField(
        _('Cód. asignatura'),
        blank=True,
        db_index=True,
        null=True,
        validators=[MinValueValidator(10_001), MaxValueValidator(999_999)],
        help_text=_(
            'Puede consultar el código de una asignatura'
            ' en la <a href="https://estudios.unizar.es" target="_blank">web de estudios</a>'
            ' <span class="fas fa-link"></span>.'
        ),
    )
    cod_grupo_asignatura = models.IntegerField(
        _('Cód. grupo de la asignatura'),
        blank=True,
        null=True,
        help_text=_('Déjelo en blanco para seleccionar <strong>todos</strong> los grupos.'),
    )
    plan = models.ForeignKey(
        'Plan',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        limit_choices_to={'esta_activo': True},
        help_text=_(
            'Tenga en cuenta que un mismo código de asignatura'
            ' se puede impartir en varios planes.'
        ),
    )
    centro = models.ForeignKey(
        'Centro',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        limit_choices_to={'esta_activo': True},
        help_text=_(
            'Tenga en cuenta que un mismo código de asignatura'
            ' se puede impartir en varios centros.'
        ),
    )

    class Meta:
        db_table = 'matricula_automatica'
        unique_together = (
            ('asignatura_id', 'cod_grupo_asignatura', 'plan', 'courseid', 'centro'),
        )

    def get_nombre_asignatura(self):
        # TODO: Renombrar Asignatura a GrupoAsignatura,
        # y crear un modelo Asignatura con sus id y nombres
        asignatura = Asignatura.objects.filter(asignatura_id=self.asignatura_id).first()
        return asignatura.nombre_asignatura if asignatura else None

    @property
    def curso(self):
        return Curso.objects.get(id_nk=self.courseid)


class Matriculacion(models.Model):
    """Matriculación Sigma de un alumno en una asignatura"""

    anyo_academico = models.IntegerField(verbose_name=_('Año académico'))
    nip = models.PositiveIntegerField(
        verbose_name=_('NIP del alumno'),
        help_text=_('Número de Identificación Personal del alumno matriculado.'),
        validators=[MinValueValidator(100_001), MaxValueValidator(9_999_999)],
    )
    centro = models.ForeignKey('Centro', on_delete=models.PROTECT, related_name='matriculaciones')
    plan = models.ForeignKey(
        'Plan',
        on_delete=models.PROTECT,
        limit_choices_to={'esta_activo': True},
    )
    asignatura_id = models.IntegerField(_('Cód. asignatura'), db_index=True)
    tipo_asignatura = models.CharField(max_length=15)
    cod_grupo_asignatura = models.IntegerField(_('Cód. grupo de la asignatura'))

    class Meta:
        db_table = 'matriculacion'


class Plan(models.Model):
    """
    Modelo para representar un plan de estudios.

    El campo `id` es el código del plan en Sigma.
    """

    id = models.PositiveIntegerField(_('Cód. plan'), primary_key=True)
    esta_activo = models.BooleanField(_('¿Activo?'), default=True)
    centro = models.ForeignKey('Centro', on_delete=models.PROTECT, related_name='planes')
    estudio = models.ForeignKey('Estudio', on_delete=models.PROTECT, related_name='planes')
    # Los EEPP tienen un código (tablas TCS de Sigma) pero no tienen realmente planes ni estudios.
    # Creamos un plan ficticio para cada estudio propio,
    # dándole como `id` el `cod_ep` precedido de un `9` para evitar posibles colisiones.
    cod_ep = models.PositiveSmallIntegerField(_('Cód. estudio propio'), null=True)

    class Meta:
        db_table = 'plan'

    def __str__(self):
        # TODO Use format_lazy
        return f'{ self.estudio.nombre } (plan { self.id })'


class Pod(models.Model):
    """Correspondencia entre asignaturas regladas y profesores.

    Establecida en el Plan de Ordenación Docente.
    La tabla se carga mediante una tarea ETL (Pentaho Spoon).
    """

    # `id` en la tabla `plan`
    plan_id_nk = models.IntegerField(blank=True, null=True, verbose_name='Cód. plan')
    centro_id = models.IntegerField(blank=True, null=True, verbose_name='Cód. centro')
    # `asignatura_id` en la tabla `asignatura`
    asignatura_id = models.IntegerField(blank=True, null=True, verbose_name='Cód. asignatura')
    cod_grupo_asignatura = models.IntegerField(
        blank=True, null=True, verbose_name='Cód. grupo de la asignatura'
    )
    anyo_academico = models.IntegerField(blank=True, null=True, verbose_name='Año académico')
    nip = models.CharField(max_length=10, blank=True, null=True, verbose_name='NIP')
    apellido1 = models.CharField(
        max_length=32, blank=True, null=True, verbose_name='Primer apellido'
    )
    apellido2 = models.CharField(
        max_length=32, blank=True, null=True, verbose_name='Segundo apellido'
    )
    nombre = models.CharField(max_length=32, blank=True, null=True, verbose_name='Nombre')
    tipo_docencia = models.IntegerField(_("Tipo de docencia"))

    class Meta:
        db_table = 'pod'
        index_together = ['nip', 'anyo_academico']
        verbose_name = 'registro del Plan de Ordenación Docente'
        verbose_name_plural = 'registros del Plan de Ordenación Docente'

    def __str__(self):
        return '{} {} {} {}'.format(
            self.anyo_academico, self.plan_id_nk, self.asignatura_id, self.nip
        )

    # Alternative: https://pypi.org/project/django-composite-foreignkey/
    def get_asignatura_or_None(self):
        """Devuelve el modelo Asignatura correspondiente a este registro."""
        try:
            asig = Asignatura.objects.get(
                anyo_academico=self.anyo_academico,
                centro_id=self.centro_id,
                plan_id_nk=self.plan_id_nk,
                asignatura_id=self.asignatura_id,
                cod_grupo_asignatura=self.cod_grupo_asignatura,
            )
        except Asignatura.DoesNotExist:
            return None
        return asig

    def get_usuario_or_None(self):
        """Devuelve el modelo User correspondiente a este registro."""
        User = get_user_model()
        return get_object_or_None(User, username=self.nip)


class ProfesorCurso(models.Model):
    """Vinculación entre un curso y la persona que lo creó/solicitó."""

    id = models.AutoField(primary_key=True)
    curso = models.ForeignKey('Curso', models.CASCADE)
    profesor = models.ForeignKey('accounts.CustomUser', models.PROTECT)
    fecha_alta = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de alta'))
    fecha_baja = models.DateTimeField(blank=True, null=True, verbose_name=_('Fecha de baja'))

    class Meta:
        db_table = 'profesor_curso'
        ordering = ('curso_id', 'fecha_alta', 'fecha_baja')
        verbose_name = _('asignación profesor-curso')
        verbose_name_plural = _('asignaciones profesor-curso')

        permissions = [
            ('anyadir_profesorcurso', _('Puede añadir un profesor a un curso.')),
            ('pc_anular', _('Puede dar de baja a un profesor de un curso.')),
        ]


class RightsSupport(models.Model):
    """Dummy auxiliary model in order to create global permissions not related to a model."""

    class Meta:
        # No database table creation or deletion operations will be performed for this model.
        managed = False

        permissions = (
            ('matricular_plan', _('Puede matricular en un curso a todos los alumnos de un plan')),
            ('anyadir_alumnos', _('Puede matricular alumnos en un curso')),
        )
