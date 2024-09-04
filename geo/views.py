# standard library
import json
from datetime import date
from os.path import splitext

# third-party
import magic
import zeep
from annoying.functions import get_config, get_object_or_None
from dateutil.relativedelta import relativedelta

# Django
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.models import Group
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, RedirectView, TemplateView, UpdateView
from django.views.generic.edit import CreateView, DeleteView
from django_tables2.views import SingleTableView
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestConnectionError
from templated_email import send_templated_mail

# local Django
from .filters import AsignaturaListFilter, CursoFilter, ForanoFilter
from .forms import (  # MatricularPlanForm,
    AsignaturaFilterFormHelper,
    CursoFilterFormHelper,
    CursoSolicitarForm,
    ForanoFilterFormHelper,
    MatriculaAutomaticaForm,
    ProfesorCursoAddForm,
)
from .models import (
    Asignatura,
    Calendario,
    Categoria,
    Curso,
    Forano,
    MatriculaAutomatica,
    Matriculacion,
    Plan,
    Pod,
    ProfesorCurso,
)
from .tables import (
    AsignaturasTable,
    CursosPendientesTable,
    CursosTodosTable,
    CursoTable,
    ForanoTodosTable,
)
from .utils import PagedFilteredTableView, matricular_grupo_sigma
from .wsclient import WSClient


class ChecksMixin(UserPassesTestMixin):
    """Proporciona comprobaciones para autorizar o no una acción a un usuario."""

    def es_pas_o_pdi(self):
        """Devuelve si el usuario es PAS o PDI de la UZ o de sus centros adscritos."""
        usuario_actual = self.request.user
        colectivos_del_usuario = (
            json.loads(usuario_actual.colectivos) if usuario_actual.colectivos else []
        )
        self.permission_denied_message = _(
            'Usted no es PAS ni PDI de la Universidad de Zaragoza o de sus centros adscritos.'
        )

        return any(
            col_autorizado in colectivos_del_usuario
            for col_autorizado in ['PAS', 'INV', 'ADS', 'PDI']
        )

    def es_profesor_del_curso(self, curso_id):
        """Devuelve si el usuario actual es profesor del curso indicado."""
        self.permission_denied_message = _('Usted no es profesor de este curso')
        curso = get_object_or_404(Curso, pk=curso_id)
        usuario_actual = self.request.user

        return usuario_actual in curso.profesores_activos

    def test_func(self):
        raise NotImplementedError(
            f'{self.__class__.__name__} carece de la implementación del método test_func().'
        )


class AyudaView(TemplateView):
    """Muestra la página de ayuda."""

    template_name = 'ayuda.html'


class HomePageView(TemplateView):
    """Muestra la página principal."""

    template_name = 'home.html'


class ASCrearCursoView(LoginRequiredMixin, ChecksMixin, View):
    """Crea un nuevo Curso para una asignatura Sigma.

    Si la creación tiene éxito, el navegador es redirigido a la ficha del curso.
    """

    def post(self, request, *args, **kwargs):  # noqa: lint.ignore=C901
        usuario = self.request.user
        if not usuario.email:
            messages.error(
                request,
                mark_safe(
                    _(
                        'No se puede crear el curso porque usted no tiene definida '
                        'ninguna dirección de correo electrónico en '
                        '<a href="https://identidad.unizar.es">Gestión de Identidades</a>.'
                    )
                ),
            )
            return redirect('mis_asignaturas')

        asignatura = get_object_or_404(Asignatura, id=kwargs['pk'])
        plan = get_object_or_None(Plan, id=asignatura.plan_id_nk)
        if not plan:
            messages.error(
                request,
                _('ERROR: No se encontró el plan %d en la tabla de planes de GEO.')
                % asignatura.plan_id_nk,
            )
            return redirect('mis_asignaturas')

        try:
            curso = self._cargar_asignatura_en_curso(asignatura, usuario)
        except Exception as ex:
            messages.error(request, _('ERROR: %(ex)s') % {'ex': ex})
            return redirect('mis_asignaturas')

        # Comprobar si existe la categoría en la plataforma, y si no, crearla.
        categoria = curso.categoria
        if not categoria.id_nk:
            categoria.crear_en_plataforma()

        # Crear el curso en la plataforma
        cliente = WSClient()
        datos_curso = curso.get_datos()
        try:
            datos_recibidos = cliente.crear_curso(datos_curso)
        except Exception as ex:
            messages.error(request, _('ERROR: %(ex)s') % {'ex': ex})
            return redirect('curso_detail', curso.id)
        curso.actualizar_tras_creacion(datos_recibidos)

        # Dejamos de rellenar la tabla `sigma`: usamos la tabla `matricula_automatica` local
        # mensaje = cliente.automatricular(asignatura, curso)
        # messages.info(request, mensaje)

        # Crear registro desactivado en la tabla `matricula_automatica` local
        try:
            ma = MatriculaAutomatica(
                courseid=curso.id_nk,
                asignatura_nk=asignatura.asignatura_id,  # Cód. Sigma de la asignatura
                cod_grupo_asignatura=asignatura.cod_grupo_asignatura,
                centro_id=asignatura.centro_id,
                plan_id=asignatura.plan_id_nk,
                active=False,
                fijo=True,
                curso_id=curso.id,
            )
            ma.save()
        except Exception as ex:
            messages.warning(
                request,
                _(
                    'AVISO: No fue posible crear el registro de matrícula automática. {ex}'.format(
                        ex=ex
                    )
                ),
            )

        profesores = asignatura.get_profesores()
        profesores.append(usuario)
        profesores = set(profesores)
        for profesor in profesores:
            try:
                curso.anyadir_profesor(profesor)
            except Exception as ex:
                messages.error(request, f'ERROR: {ex}')
                return redirect('curso_detail', curso.id)

        messages.success(request, _('Curso creado correctamente en Moodle.'))

        return redirect('curso_detail', curso.id)

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _cargar_asignatura_en_curso(asignatura, usuario):
        """Crea una nueva instancia de Curso con los datos de la asignatura indicada."""
        curso = Curso(
            nombre=asignatura.nombre_asignatura,
            solicitante=usuario,
            fecha_solicitud=timezone.now(),
            # Las asignaturas Sigm@ se aprueban automáticamente, por el administrador.
            fecha_autorizacion=timezone.now(),
            autorizador_id=1,
            plataforma_id=1,
            categoria=asignatura.get_categoria(),
            anyo_academico=asignatura.anyo_academico,
            asignatura_id=asignatura.id,
            # Las asignaturas regladas son aprobadas automáticamente
            estado=Curso.Estado.AUTORIZADO,
        )
        curso.save()
        return curso


class ASTodasView(LoginRequiredMixin, ChecksMixin, PagedFilteredTableView):
    """Muestra todas las asignaturas, y permite crear curso de cualquiera de ellas."""

    filter_class = AsignaturaListFilter
    model = Asignatura
    table_class = AsignaturasTable
    template_name = 'asignatura/todas.html'
    formhelper_class = AsignaturaFilterFormHelper

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        context['curso'] = f'{anyo_academico}/{anyo_academico + 1}'
        return context

    def get_queryset(self):
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        return Asignatura.objects.filter(anyo_academico=anyo_academico).select_related('curso')

    def test_func(self):
        return self.es_pas_o_pdi()


class CalendarioActualView(View):
    """Devuelve el año académico actual en formato JSON."""

    def get(self, request, *args, **kwargs):
        anyo_actual = Calendario.objects.get(slug='actual').anyo
        return HttpResponse(f'{{"anyo": {anyo_actual}}}')


class CalendarioUpdate(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Muestra un formulario para actualizar el año académico actual."""

    permission_required = 'geo.calendario'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    model = Calendario
    fields = ('anyo',)
    template_name = 'gestion/calendario_form.html'

    # Tras cambiar el año hay que mover en Moodle
    # las categorías «Varios» (5047) y «Escuela de Doctorado» (5021),
    # así como la de cursos no reglados bianuales que toque.

    # NOTA: La Escuela de Doctorado tiene dos categorías:
    #
    # * una categoría (5021) directamente en «Cursos 20xx-20yy»,
    #   con 1 curso por cada PD, que es la que se pasa de un año al siguiente.
    # * otra categoría (5747, 5701, 5776...) dentro de la categoría «No reglada» de cada año,
    #   para actividades de formación transversal y específica.

    # Se puede usar `moosh` para mover en Moodle una categoría a otra.
    # Example: Move the category with id 5021 to be in the category with id 6543:
    #     moosh category-move 5021 6543

    # También hay que mover esas tres categorías en Geoda:
    #
    # SELECT id, anyo_academico FROM categoria WHERE supercategoria_id IS NULL
    #   ORDER BY anyo_academico DESC LIMIT 1;  -- Obtener el `id` de la nueva supercategoría
    # UPDATE categoria SET anyo_academico=<anyo>, supercategoria_id=<id> WHERE id_nk=5047;
    # UPDATE categoria SET anyo_academico=<anyo>, supercategoria_id=<id> WHERE id_nk=5021;
    # y la de cursos no reglados bianuales que toque:
    # SELECT * FROM categoria WHERE nombre LIKE 'Bianuales%'
    #   ORDER BY anyo_academico DESC LIMIT 1,1; -- Obtener el id_nk de la penúltima bianual
    # SELECT * FROM categoria WHERE nombre = 'No reglada' AND anyo_academico = <anyo>; -- id
    # UPDATE categoria SET anyo_academico=<anyo>, supercategoria_id=<id> WHERE id_nk=<id_nk>;

    success_message = mark_safe(
        str(_('Se ha actualizado el curso académico actual.'))
        + '<br><br>\n'
        + str(_('Recuerde que a continuación <b>se debe</b>:'))
        + '<br>\n<ul>\n<li>'
        + str(
            _(
                'Mover las categorías «Varios» y «Escuela de Doctorado» del año anterior '
                'a la del año actual, tanto en GEO como en Moodle.<br>'
                'Así como la de cursos no reglados bianuales que toque.'
            )
        )
        + '</li>\n<li>'
        + str(_('Actualizar el año en las pasarelas de GEO (carga de asignaturas y POD).'))
        + '</li>\n</ul>\n'
        + str(_('<b>Contacte con los responsables de Moodle y GEO del SICUZ.</b>'))
    )
    success_url = reverse_lazy('calendario', args=['actual'])

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        anyo = int(self.request.POST.get('anyo'))
        anyo_anterior = anyo - 1
        siguiente_anyo = anyo + 1
        nombre_cat_anyo = f'Cursos {anyo}-{siguiente_anyo}'

        # Eliminar de la tabla `matriculacion` los alumnos del año anterior, si los hubiera.
        Matriculacion.objects.filter(anyo_academico=anyo_anterior).delete()

        # Crear categoría para el año académico. Vg: «Cursos 2019-2020»
        cat_anyo = self._crear_categoria(anyo, nombre_cat_anyo, None)
        # Crear categoría «No reglada».
        cat_nr = self._crear_categoria(anyo, 'No reglada', cat_anyo.id)
        # Crear las subcategorías de los estudios no reglados
        for nombre in Categoria.NO_REGLADAS:
            self._crear_categoria(anyo, nombre, cat_nr.id)
        # Crear nueva categoría de cursos no reglados bianuales
        self._crear_categoria(anyo, f'Bianuales {anyo}-{anyo+2}', cat_nr.id)

        return super().form_valid(form)

    @staticmethod
    def _crear_categoria(anyo, nombre, supercategoria_id):
        """Comprueba si existe la categoría, y la crea si es necesario."""
        cat = get_object_or_None(
            Categoria, anyo_academico=anyo, nombre=nombre, supercategoria_id=supercategoria_id
        )
        if not cat:
            cat = Categoria(
                plataforma_id=1,
                anyo_academico=anyo,
                nombre=nombre,
                supercategoria_id=supercategoria_id,
            )
            cat.save()
        if not cat.id_nk:
            cat.crear_en_plataforma()
        return cat


class CursoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Curso
    permission_required = 'geo.curso_delete'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    success_url = reverse_lazy('curso_todos')
    template_name = 'gestion/curso_confirm_delete.html'

    def post(self, request, *args, **kwargs):
        curso = self.get_object()
        if curso.id_nk:
            respuesta = curso.borrar_en_plataforma()

            if respuesta and respuesta.get('warnings'):
                for advertencia in respuesta['warnings']:
                    messages.error(
                        request,
                        _('ERROR al borrar el curso en Moodle: ') + advertencia.get('message'),
                    )
                return redirect('curso_detail', curso.id)

            for pc in curso.profesorcurso_set.all():
                pc.delete()

            matriculas_automaticas = MatriculaAutomatica.objects.filter(courseid=curso.id_nk)
            matriculas_automaticas.delete()

        # Innecesario porque el registro será eliminado de la tabla.
        # curso.estado = Curso.Estado.BORRADO
        # curso.save()

        messages.success(
            request,
            _('El curso «%(nombre)s» ha sido borrado con éxito.') % {'nombre': curso.nombre},
        )
        return super().post(request, *args, **kwargs)


class CursoDetailView(LoginRequiredMixin, DetailView):
    """Muestra información detallada de un curso."""

    model = Curso
    template_name = 'curso/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso_id = self.get_object().id

        asignaciones = self.object.profesorcurso_set.filter(
            Q(fecha_baja__gt=timezone.now()) | Q(fecha_baja=None)
        ).select_related('profesor')
        profesores = [asignacion.profesor for asignacion in asignaciones]
        es_profesor_del_curso = self.request.user in profesores

        # mp_form = MatricularPlanForm()
        # Inicializo aquí el valor de `curso_id` en el formulario.
        # No lo paso como un diccionario al crear el formulario, porque entonces
        # `is_bound` sería True, y el campo `nip` se marcaría como `is_invalid`.
        # mp_form.fields['curso_id'].initial = curso_id

        pc_form = ProfesorCursoAddForm()
        pc_form.fields['curso_id'].initial = curso_id

        context.update(
            {
                'asignaciones': asignaciones,
                'matriculas_automaticas': MatriculaAutomatica.objects.filter(
                    courseid=self.object.id_nk
                ),
                'ma_form': MatriculaAutomaticaForm,
                # 'mp_form': mp_form,
                'pc_form': pc_form,
                'puede_matricular_profesores': es_profesor_del_curso
                or self.request.user.has_perm('geo.anyadir_profesorcurso'),
                'puede_matricular_alumnos': es_profesor_del_curso
                or self.request.user.has_perm('geo.anyadir_alumnos'),
            }
        )

        return context


class CursoMatricularNipsView(LoginRequiredMixin, ChecksMixin, View):
    def post(self, request, *args, **kwargs):
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id)
        fichero = request.FILES.get('file')

        if not fichero:
            messages.error(request, _('Debe enviar un fichero de texto con los NIPs.'))
            return redirect('curso_detail', curso_id)

        ext = splitext(fichero.name)[1].lower()
        if ext not in ('.csv', '.tsv', '.txt'):
            messages.error(request, _('La extensión del fichero debería ser .txt o .csv .'))
            return redirect('curso_detail', curso_id)

        filetype = magic.from_buffer(fichero.read(2048), mime=True)
        fichero.seek(0)
        if not (filetype.startswith('text/') or filetype == 'application/csv'):
            messages.error(request, _('El fichero no parece ser un documento de texto plano.'))
            return redirect('curso_detail', curso_id)

        try:
            nips = fichero.read(10 * 1024).decode('utf-8').splitlines()  # Max 10 KiB
        except UnicodeDecodeError as ex:
            messages.error(
                self.request,
                mark_safe(
                    _(
                        'Error al leer el fichero. '
                        'Posiblemente contenta algún carácter extraño.<br>\n'
                        'Revise el fichero para corregirlo, o bien vuelva a generarlo.<br>\n'
                        'ERROR: %(ex)s.'
                    )
                    % {'ex': ex}
                ),
            )
            return redirect('curso_detail', curso_id)

        cliente = WSClient()
        try:
            num_matriculados, usuarios_no_encontrados = cliente.matricular_alumnos(nips, curso)
        except Exception as ex:
            messages.error(self.request, _('ERROR: %(ex)s.') % {'ex': ex})
            return redirect('curso_detail', curso_id)

        if usuarios_no_encontrados:
            messages.warning(
                request,
                _('No se encontró en Moodle el usuario de los siguientes NIPs: ')
                + ', '.join(usuarios_no_encontrados),
            )

        messages.success(
            request,
            _('Se ha matriculado en el curso a %(num)s alumnos.') % {'num': num_matriculados},
        )
        return redirect('curso_detail', curso_id)

    def test_func(self):
        return self.es_profesor_del_curso(
            self.request.POST.get('curso_id')
        ) or self.request.user.has_perm('geo.anyadir_alumnos')


class CursoRematricularView(LoginRequiredMixin, ChecksMixin, View):
    """Rematricula en un curso de Moodle al profesorado que consta en GEO."""

    def post(self, request, *args, **kwargs):
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id)

        cliente = WSClient()
        for profesor in curso.profesores_activos:
            try:
                cliente.matricular_profesor(profesor, curso)
            except Exception as ex:
                messages.error(self.request, _('ERROR: %(ex)s.') % {'ex': ex})
                return redirect('curso_detail', curso_id)

        messages.success(request, _('Se ha vuelto a matricular al profesorado del curso.'))
        return redirect('curso_detail', curso_id)

    def test_func(self):
        return self.es_profesor_del_curso(
            self.request.POST.get('curso_id')
        ) or self.request.user.has_perm('geo.anyadir_profesorcurso')


class CursosTodosView(LoginRequiredMixin, PermissionRequiredMixin, PagedFilteredTableView):
    """Muestra todos los cursos de un año dado, permitiendo filtrar por su estado."""

    filter_class = CursoFilter
    formhelper_class = CursoFilterFormHelper
    model = Curso
    permission_required = 'geo.cursos_todos'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    paginate_by = 20
    table_class = CursosTodosTable
    template_name = 'gestion/curso_todos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anyo_academico = (
            self.kwargs.get('anyo_academico') or Calendario.objects.get(slug='actual').anyo
        )
        context['curso'] = f'{anyo_academico}/{anyo_academico + 1}'
        return context

    def get_queryset(self):
        anyo_academico = (
            self.kwargs.get('anyo_academico') or Calendario.objects.get(slug='actual').anyo
        )
        return Curso.objects.filter(anyo_academico=anyo_academico).prefetch_related('profesores')


class CursosPendientesView(LoginRequiredMixin, PermissionRequiredMixin, SingleTableView):
    """Muestra los cursos no reglados pendientes de aprobación."""

    permission_required = 'geo.cursos_pendientes'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    context_object_name = 'cursos_pendientes'
    paginate_by = 20
    ordering = ['-fecha_solicitud']
    queryset = Curso.objects.filter(estado=Curso.Estado.SOLICITADO).prefetch_related('profesores')
    table_class = CursosPendientesTable
    template_name = 'gestion/curso_pendientes.html'


"""
class MatricularPlanView(LoginRequiredMixin, PermissionRequiredMixin, View):
    # Matricula en un curso a todos los alumnos del plan indicado.

    permission_required = 'geo.matricular_plan'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')

    def post(self, request, *args, **kwargs):
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id)
        try:
            plan_id_nk = int(request.POST.get('plan_id_nk'))
        except ValueError:
            messages.error(request, _('El código de plan indicado no es válido.'))
            return redirect('curso_detail', curso_id)

        asignaturas = Asignatura.objects.filter(
            anyo_academico=curso.anyo_academico, plan_id_nk=plan_id_nk
        )
        cliente = WSClient()

        try:
            for asignatura in asignaturas:
                cliente.automatricular(asignatura, curso, active=1)
        except Exception as ex:
            messages.error(request, 'ERROR: %s' % str(ex))
            return redirect('curso_detail', curso_id)

        messages.success(
            request,
            _(
                'Se ha matriculado en este curso a todos los alumnos del plan {%(plan)s}'
                ' (%(estudio)s, %(centro)s).'
            )
            % {
                'plan': plan_id_nk,
                'estudio': asignaturas[0].nombre_estudio,
                'centro': asignaturas[0].nombre_centro,
            },
        )

        return redirect('curso_detail', curso_id)
"""


class MisAsignaturasView(LoginRequiredMixin, ChecksMixin, SingleTableView):
    """Muestra las asignaturas del usuario, según el POD, y permite crear cursos."""

    table_class = AsignaturasTable
    template_name = 'pod/mis_asignaturas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        context['curso'] = f'{anyo_academico}/{anyo_academico + 1}'
        return context

    def get_queryset(self):
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        pods = Pod.objects.filter(nip=self.request.user.username, anyo_academico=anyo_academico)
        asignaturas = [pod.get_asignatura_or_None() for pod in pods]
        # Si llegara una asignación a una asignatura que no esté en la tabla `asignatura`,
        # la omitimos.
        asignaturas = list(filter(None, asignaturas))
        return asignaturas

    def test_func(self):
        return self.es_pas_o_pdi()


class MisCursosView(LoginRequiredMixin, SingleTableView):
    """Muestra los cursos creados por el usuario."""

    table_class = CursoTable
    template_name = 'curso/mis_cursos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        context['curso'] = f'{anyo_academico}/{anyo_academico + 1}'
        return context

    def get_queryset(self):
        return Curso.objects.filter(
            profesores=self.request.user.id,
            anyo_academico=Calendario.objects.get(slug='actual').anyo,
        )


class ResolverSolicitudCursoView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    """Autoriza o deniega una solicitud de curso."""

    permission_required = 'geo.cursos_pendientes'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('curso_pendientes')

    def post(self, request, *args, **kwargs):
        id_recibido = request.POST.get('id')
        curso = get_object_or_404(Curso, pk=id_recibido)
        curso.autorizador = request.user
        curso.fecha_autorizacion = timezone.now()
        curso.comentarios = request.POST.get('comentarios')

        if request.POST.get('decision') == 'autorizar':
            curso.estado = Curso.Estado.AUTORIZADO
            curso.save()

            # Comprobar si existe la categoría en la plataforma, y si no, crearla.
            # categoria = curso.categoria
            # if not categoria.id_nk:
            #     categoria.crear_en_plataforma()

            cliente = WSClient()
            try:
                datos_recibidos = cliente.crear_curso(curso.get_datos())
            except Exception as err:
                messages.error(
                    request, _('ERROR: No fue posible crear el curso: %(err)s.') % {'err': err}
                )
                return redirect('curso_detail', id_recibido)

            curso.actualizar_tras_creacion(datos_recibidos)
            try:
                cliente.matricular_profesor(curso.profesores.first(), curso)
            except Exception as ex:
                messages.warning(self.request, _('AVISO: %(ex)s.') % {'ex': ex})

            messages.info(
                request,
                _('El curso «%(nombre)s» ha sido autorizado y creado.') % {'nombre': curso.nombre},
            )
        else:
            curso.estado = Curso.Estado.DENEGADO
            curso.save()
            messages.info(
                request, _('El curso «%(nombre)s» ha sido denegado.') % {'nombre': curso.nombre}
            )

        try:
            self._notifica_resolucion(curso, request.build_absolute_uri('/')[:-1])
        except Exception as err:
            messages.warning(
                request,
                _(
                    'No se envió por correo electrónico la notificación de la resolución'
                    ' sobre la solicitud de curso: %(err)s.'
                )
                % {'err': err},
            )

        return super().post(request, *args, **kwargs)

    @staticmethod
    def _notifica_resolucion(curso, site_url):
        """Envía un correo al solicitante del curso y los gestores informando de la resolución."""
        grupo_gestores = Group.objects.get(name='Gestores')
        gestores = grupo_gestores.user_set.all()
        correos_gestores = [g.email for g in gestores]
        send_templated_mail(
            template_name='resolucion',
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=[curso.profesores.first().email],
            bcc=correos_gestores,
            context={'curso': curso, 'site_url': site_url},
        )


class SolicitarCursoNoRegladoView(LoginRequiredMixin, ChecksMixin, CreateView):
    """Muestra un formulario para solicitar un curso no reglado."""

    model = Curso
    template_name = 'curso/solicitar.html'

    def get(self, request, *args, **kwargs):
        usuario = self.request.user
        if not usuario.email:
            messages.error(
                request,
                mark_safe(
                    _(
                        'Usted no puede solicitar cursos porque no tiene definida '
                        'ninguna dirección de correo electrónico en '
                        '<a href="https://identidad.unizar.es">Gestión de Identidades</a>.'
                    )
                ),
            )
            return redirect('mis_cursos')

        # `get_context_data()` is in ModelFormMixin
        # which cannot be used without the `fields` attribute (maybe with form_class?).
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        context = {
            'curso': f'{anyo_academico}/{anyo_academico + 1}',
            'form': CursoSolicitarForm(user=self.request.user),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        formulario = CursoSolicitarForm(data=request.POST, user=self.request.user)
        if formulario.is_valid():
            curso = formulario.save()
            messages.success(
                request, _('La solicitud ha sido recibida. Se le avisará cuando se resuelva.')
            )
            try:
                self._notifica_solicitud(curso, request.build_absolute_uri('/')[:-1])
            except Exception as err:  # smtplib.SMTPAuthenticationError etc
                messages.warning(
                    request,
                    _(
                        'No se enviaron por correo las notificaciones'
                        ' de la solicitud de curso no reglado: %(err)s'
                    )
                    % {'err': err},
                )

            return redirect('mis_cursos')

        return render(request, self.template_name, {'form': formulario})

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _notifica_solicitud(curso, site_url):
        """Envía email a los Gestores informando de la solicitud de curso no reglado."""
        grupo_gestores = Group.objects.get(name='Gestores')
        gestores = grupo_gestores.user_set.all()
        destinatarios = [g.email for g in gestores]
        send_templated_mail(
            template_name='solicitud',
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=destinatarios,
            context={'curso': curso, 'site_url': site_url},
        )


class ForanoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Muestra información detallada de una solicitud de vinculación."""

    model = Forano
    permission_required = 'geo.forano'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    template_name = 'gestion/forano_detail.html'


class ForanoSolicitarView(LoginRequiredMixin, ChecksMixin, CreateView):
    """
    Muestra un formulario para solicitar que se añada un NIP
    al grupo de vinculación «Usuarios invitados a Moodle».
    """

    model = Forano
    fields = ('nip', 'nombre', 'email', 'motivo_solicitud')
    required = ('nip', 'nombre', 'email', 'motivo_solicitud')
    template_name = 'forano/solicitar.html'

    def post(self, request, *args, **kwargs):  # noqa: max-complexity: 11
        form = self.get_form()
        if form.is_valid():
            forano = form.save(False)
            forano.fecha_solicitud = timezone.now()
            forano.estado = Forano.Estado.SOLICITADO
            forano.solicitante = self.request.user
            forano.save(True)

            try:
                self._notifica_solicitud(forano, request.build_absolute_uri('/')[:-1])
            except Exception as err:
                messages.warning(
                    request,
                    _(
                        'No se enviaron las notificaciones de la solicitud de vinculación'
                        ' por correo electrónico: %(err)s'
                    )
                    % {'err': err},
                )

            # Nos conectamos al WebService de Gestión de Identidades para establecer la vinculación
            wsdl = get_config('WSDL_VINCULACIONES')
            session = Session()
            session.auth = HTTPBasicAuth(
                get_config('USER_VINCULACIONES'), get_config('PASS_VINCULACIONES')
            )

            try:
                client = zeep.Client(
                    wsdl=wsdl, transport=zeep.transports.Transport(session=session)
                )
            except RequestConnectionError:
                messages.error(request, _('Se produjo un error de conexión. Vuelva a intentarlo.'))
                return redirect('forano_solicitar')
            except Exception as ex:
                messages.error(request, _('ERROR: %(ex)s') % {'ex': ex})
                return redirect('forano_solicitar')

            # Llamamos al método `creaVinculacion()`
            # de unizar/gestion/identidad/webservice/VinculacionesImpl.java
            try:
                response = client.service.creaVinculacion(
                    f'{forano.nip}',  # nip
                    '53',  # codVinculacion Usuarios invitados a Moodle
                    date.today().isoformat(),  # fechaInicio
                    (date.today() + relativedelta(years=1)).isoformat(),  # fechaFin (en 1 año)
                    self.request.user.username,  # nipResponsable
                    forano.email,  # correoPersonal
                )
            except zeep.exceptions.TransportError:
                messages.error(
                    request, _('Se produjo un error de transporte. Vuelva a intentarlo.')
                )
                return redirect('forano_solicitar')

            if response.aviso:
                messages.warning(request, response.descripcionAviso)

            if response.error:
                forano.comentarios = response.descripcionResultado
                forano.save()
                messages.error(request, response.descripcionResultado)
            else:
                forano.autorizador = request.user  # Auto
                forano.fecha_autorizacion = timezone.now()
                forano.estado = Forano.Estado.AUTORIZADO
                forano.save()

                messages.success(
                    request,
                    _(
                        'Se va a examinar su solicitud.'
                        ' Si en 24 horas no ha recibido ninguna comunicación en contra,'
                        ' podrá proceder a incluir al invitado en el curso Moodle.'
                    ),
                )

            return redirect('mis_cursos')

        return render(request, self.template_name, {'form': form})

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _notifica_solicitud(forano, site_url):
        """Envía email a los Gestores informando de la solicitud de vinculación."""
        grupo_gestores = Group.objects.get(name='Gestores')
        gestores = grupo_gestores.user_set.all()
        destinatarios = [g.email for g in gestores]
        send_templated_mail(
            template_name='solicitud_forano',
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=destinatarios,
            context={'forano': forano, 'site_url': site_url},
        )


class ForanoTodosView(LoginRequiredMixin, PermissionRequiredMixin, PagedFilteredTableView):
    """Muestra todas las solicitudes de vinculación, permitiendo filtrar por su estado."""

    filter_class = ForanoFilter
    formhelper_class = ForanoFilterFormHelper
    model = Forano
    permission_required = 'geo.forano'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    paginate_by = 20
    queryset = Forano.objects.select_related('solicitante')
    table_class = ForanoTodosTable
    template_name = 'gestion/forano_todos.html'


# class ForanoResolverView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """Crea una vinculacion de un usuario externo en Gestión de Identidades."""

#     permission_required = 'geo.forano'
#     permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')

#     def post(self, request, *args, **kwargs):
#         id_recibido = request.POST.get('id')
#         forano = get_object_or_404(Forano, pk=id_recibido)
#         forano.autorizador = request.user
#         forano.fecha_autorizacion = timezone.now()
#         forano.comentarios = request.POST.get('comentarios')

#         if request.POST.get('decision') == 'denegar':
#             forano.estado = Forano.Estado.DENEGADO
#             forano.save()
#             messages.info(request, _(f'El usuario externo «{forano.nip}» ha sido denegado.'))
#             self._notifica_resolucion(forano)
#         else:
#             forano.estado = Forano.Estado.AUTORIZADO
#             forano.save()

#             wsdl = get_config('WSDL_VINCULACIONES')
#             session = Session()
#             session.auth = HTTPBasicAuth(
#                 get_config('USER_VINCULACIONES'), get_config('PASS_VINCULACIONES')
#             )

#             try:
#                 client = zeep.Client(
#                     wsdl=wsdl, transport=zeep.transports.Transport(session=session)
#                 )
#             except RequestConnectionError:
#                 messages.error(request, 'No fue posible conectarse al WS de Identidades.')
#                 return redirect('forano_todos')
#             except Exception as ex:
#                 messages.error(request, 'ERROR: %s' % str(ex))
#                 return redirect('forano_todos')

#             response = client.service.creaVinculacion(
#                 f'{forano.nip}',  # nip
#                 '53',  # codVinculacion Usuarios invitados a Moodle
#                 date.today().isoformat(),  # fechaInicio
#                 (date.today() + relativedelta(years=1)).isoformat(),  # fechaFin
#                 forano.solicitante.username,  # nipResponsable
#             )

#             if response.aviso:
#                 messages.warning(request, response.descripcionAviso)

#             if response.error:
#                 messages.error(request, response.descripcionResultado)
#             else:
#                 messages.success(
#                     request,
#                     _(
#                         f'El NIP «{forano.nip}» ha sido vinculado a Moodle.  Es posible que Vd.'
#                         ' no vea al invitado entre los usuarios de la plataforma hasta que'
#                         ' el invitado acceda a la plataforma por primera vez.'
#                     ),
#                 )
#                 self._notifica_resolucion(forano)

#         return redirect('forano_todos')

#     @staticmethod
#     def _notifica_resolucion(forano):
#         """Envía un correo al solicitante del usuario-externo informando de la resolucíon."""
#         send_templated_mail(
#             template_name='resolucion_forano',
#             from_email=None,  # settings.DEFAULT_FROM_EMAIL
#             recipient_list=[forano.solicitante.email],
#             context={'forano': forano},
#         )


class MatriculaAutomaticaAnyadirView(LoginRequiredMixin, ChecksMixin, View):
    """
    Añade un registro para la matrícula automática de alumnos matriculados en asignaturas Sigma.
    """

    def post(self, request, *args, **kwargs):
        curso_id = kwargs['pk']
        curso = get_object_or_404(Curso, pk=curso_id)
        formulario = MatriculaAutomaticaForm(data=request.POST)
        if formulario.is_valid():
            data = formulario.cleaned_data
            # Los gestores pueden matricular a todo un plan o centro,
            # pero el PDI debe elegir una asignatura.
            if not self.request.user.has_perm('geo.anyadir_alumnos') and not data['asignatura_nk']:
                messages.error(request, _('No ha seleccionado ninguna asignatura.'))
                return redirect('curso_detail', curso_id)

            # No se puede matricular a todos los estudiantes de la Universidad.
            if not data['asignatura_nk'] and not data['centro'] and not data['plan']:
                messages.error(
                    request, _('No ha seleccionado ninguna asignatura, centro ni plan.')
                )
                return redirect('curso_detail', curso_id)

            # Introducir un grupo de asignatura no tiene sentido sin una asignatura, centro y plan.
            if data['cod_grupo_asignatura'] and not (
                data['asignatura_nk'] and data['centro'] and data['plan']
            ):
                messages.error(
                    request,
                    _(
                        'Para seleccionar un grupo'
                        ' es obligatorio indicar la asignatura, centro y plan.'
                    ),
                )
                return redirect('curso_detail', curso_id)

            anyo_academico = Calendario.objects.get(slug='actual').anyo
            if curso.anyo_academico < anyo_academico:
                messages.error(
                    request,
                    _('No se puede añadir registros a cursos antiguos.'),
                )
                return redirect('curso_detail', curso_id)

            ma = formulario.save(commit=False)
            ma.curso_id = curso.id  # id en GEO
            ma.courseid = curso.id_nk  # id en Moodle
            try:
                ma.save()
            except Exception as ex:
                mensaje = mark_safe(
                    _(
                        'Error al guardar el registro. ¿Seguro que no existe ya?<br>\n'
                        'ERROR: %(ex)s.'
                    )
                    % {'ex': ex}
                )
                messages.error(request, mensaje)
                return redirect('curso_detail', curso_id)

            # Matricular en Moodle a los estudiantes del nuevo registro de matrícula automática.
            num_matriculados = matricular_grupo_sigma(
                ma.courseid, ma.asignatura_nk, ma.cod_grupo_asignatura, ma.centro_id, ma.plan_id
            )
            mensaje = _(f'Se ha matriculado a {num_matriculados} estudiantes.')
            messages.info(request, mensaje)

        else:
            messages.error(request, formulario.errors)
            return redirect('curso_detail', curso_id)

        return redirect(
            reverse('curso_detail', kwargs={'pk': curso_id}) + '#matriculacion-automatica'
        )

    def test_func(self):
        return self.es_profesor_del_curso(self.kwargs.get('pk')) or self.request.user.has_perm(
            'geo.anyadir_alumnos'
        )


class MatriculaAutomaticaLinkView(LoginRequiredMixin, RedirectView):
    """
    Autenticar al usuario y redirigir al ancla de matrícula automática,

    Si se va directamente a la URL sin estar autenticado, al pasar por el SSO se pierde el ancla.
    """

    def get_redirect_url(self, *args, **kwargs):
        return reverse('curso_detail', kwargs={'pk': kwargs['pk']}) + '#matriculacion-automatica'


class ProfesorCursoAnularView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Dar de baja una asignación profesor-curso."""

    permission_required = 'geo.pc_anular'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')

    model = ProfesorCurso
    fields = ['fecha_baja']

    success_message = (
        'Ha establecido como fecha de baja el %(fecha_baja)s'
        ' para %(tratamiento)s %(nombre_docente)s en este curso.'
    )
    template_name = 'gestion/profesorcurso_form.html'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        cliente = WSClient()
        try:
            respuestas = cliente.desmatricular(self.object.profesor, self.object.curso)
        except Exception as ex:
            messages.error(self.request, _('ERROR: %(ex)s.') % {'ex': ex})
            return redirect('curso_detail', self.object.curso_id)

        for respuesta in respuestas:
            for error in respuesta.get('errors'):
                messages.error(
                    self.request, _('ERROR al dar de baja en Moodle: ') + error.get('message')
                )

        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        docente = self.object.profesor

        return self.success_message % dict(
            cleaned_data,
            fecha_baja=date_format(self.object.fecha_baja),
            tratamiento='la profesora' if docente.sexo == 'F' else 'el profesor',
            nombre_docente=docente.full_name,
        )

    def get_success_url(self):
        return reverse('curso_detail', args=[self.object.curso_id])


class ProfesorCursoAnyadirView(LoginRequiredMixin, ChecksMixin, View):
    """
    Matricula a un usuario como profesor de un curso.

    Crea el usuario si no existe, y crea una asignación profesor-curso.
    """

    def post(self, request, *args, **kwargs):  # noqa: lint.ignore=C901
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id)

        # Obtenemos el usuario (si ya existe en el sistema).
        User = get_user_model()
        nip = request.POST.get('nip')
        profesor = get_object_or_None(User, username=nip)

        if not profesor:
            # El usuario no existe previamente. Lo creamos con los datos de Gestión de Identidades.
            try:
                profesor = User.crear_usuario(request, nip)
            except Exception as ex:
                messages.error(request, f'ERROR: {ex.args[0]}')
                return redirect('curso_detail', curso_id)
        else:
            # El usuario existe. Actualizamos sus datos con los de Gestión de Identidades.
            try:
                profesor.actualizar(self.request)
            except Exception as ex:
                # Si Identidades devuelve un error, finalizamos mostrando el mensaje de error.
                messages.error(request, _('ERROR: %(ex)s') % {'ex': ex})
                return redirect('curso_detail', curso_id)

        # Si el usuario no está activo, finalizamos explicando esta circunstancia.
        if not profesor.is_active:
            messages.error(
                request,
                _('ERROR: %(nombre)s no está activo en Gestión de Identidades.')
                % {'nombre': profesor.full_name},
            )
            return redirect('curso_detail', curso_id)

        # Si el usuario no tiene email, no podrá entrar en Moodle.
        if not profesor.email:
            messages.error(
                request,
                _(
                    'ERROR: %(nombre)s no tiene establecida'
                    ' ninguna dirección de correo electrónico en Gestión de Identidades.'
                )
                % {'nombre': profesor.full_name},
            )
            return redirect('curso_detail', curso_id)

        # Si el usuario ya es profesor del curso, no lo añadimos por segunda vez.
        if profesor in curso.profesores_activos:
            messages.error(
                request,
                _(
                    'ERROR: %(nombre)s ya es profesor de este curso.'
                    ' Si se ha dado de baja en Moodle,'
                    ' puede rematricularlo en la sección inferior.'
                )
                % {'nombre': profesor.full_name},
            )
            return redirect('curso_detail', curso_id)

        # Añadimos al usuario como profesor del curso.
        try:
            curso.anyadir_profesor(profesor)
        except Exception as ex:
            messages.error(request, f'ERROR: {ex}')
            return redirect('curso_detail', curso_id)

        messages.success(request, _('Se ha añadido el profesor al curso.'))
        return redirect('curso_detail', curso_id)

    def test_func(self):
        return self.es_profesor_del_curso(
            self.request.POST.get('curso_id')
        ) or self.request.user.has_perm('geo.anyadir_profesorcurso')


def teapot(request, whatever):
    """Pasarle a Django direcciones PHP es como pedirle a una tetera que haga café."""
    return HttpResponse("I'm a teapot", status=418)
