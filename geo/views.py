# standard library
import json
from datetime import date

# third-party
import zeep
from annoying.functions import get_config, get_object_or_None
from dateutil.relativedelta import relativedelta
from django_tables2.views import SingleTableView
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestConnectionError
from templated_email import send_templated_mail

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

# local Django
from .filters import AsignaturaListFilter, CursoFilter, ForanoFilter
from .forms import (
    AsignaturaFilterFormHelper,
    CursoFilterFormHelper,
    CursoSolicitarForm,
    ForanoFilterFormHelper,
    MatricularPlanForm,
    ProfesorCursoAddForm,
)
from .models import Asignatura, Calendario, Categoria, Curso, Forano, Pod, ProfesorCurso
from .tables import (
    AsignaturasTable,
    CursosTodosTable,
    CursosPendientesTable,
    CursoTable,
    ForanoTodosTable,
    PodTable,
)
from .utils import PagedFilteredTableView
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
            col_autorizado in colectivos_del_usuario for col_autorizado in ['PAS', 'ADS', 'PDI']
        )

    def test_func(self):
        raise NotImplementedError(
            '{0} carece de la implementación del método test_func().'.format(
                self.__class__.__name__
            )
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

    def get(self, request, *args, **kwargs):
        asignatura = get_object_or_404(Asignatura, id=kwargs['pk'])
        if hasattr(asignatura, 'curso'):
            messages.error(request, _('El curso ya estaba creado.'))
            return redirect('curso_detail', asignatura.curso.id)

        curso = self._cargar_asignatura_en_curso(asignatura)

        # Comprobar si existe la categoría en la plataforma, y si no, crearla.
        categoria = curso.categoria
        if not categoria.id_nk:
            categoria.crear_en_plataforma()

        cliente = WSClient()
        datos_curso = curso.get_datos()
        datos_recibidos = cliente.crear_curso(datos_curso)
        curso.actualizar_tras_creacion(datos_recibidos)
        curso.anyadir_profesor(self.request.user)
        mensaje = cliente.automatricular(asignatura, curso)
        messages.info(request, mensaje)
        messages.success(request, _('Curso creado correctamente en Moodle.'))

        return redirect('curso_detail', curso.id)

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _cargar_asignatura_en_curso(asignatura):
        """Crea una nueva instancia de Curso con los datos de la asignatura indicada."""
        curso = Curso(
            nombre=asignatura.nombre_asignatura,
            fecha_solicitud=timezone.now(),
            # Las asignaturas Sigm@ se aprueban automáticamente, por el administrador.
            fecha_autorizacion=timezone.now(),
            autorizador_id=1,
            plataforma_id=1,
            categoria=asignatura.get_categoria(),
            anyo_academico=asignatura.anyo_academico,
            asignatura_id=asignatura.id,
            estado=Curso.Estado.AUTORIZADO,  # Las asignaturas regladas son aprobadas automáticamente
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

    def get_queryset(self):
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        return Asignatura.objects.filter(anyo_academico=anyo_academico).select_related('curso')

    def test_func(self):
        return self.es_pas_o_pdi()


class CalendarioActualView(View):
    """Devuelve el año académico actual."""

    def get(self, request, *args, **kwargs):
        return HttpResponse(Calendario.objects.get(slug='actual').anyo)


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
    # las categorías Varios (5047) y Escuela de Doctorado (5021).
    # Se puede usar `moosh` para mover una categoría a otra.
    # Example: Move the category with id 5 to be in the category with id 7:
    # moosh category-move 5 7

    # También hay que moverlas en Geoda:
    # SELECT id, anyo_academico FROM categoria WHERE supercategoria_id IS NULL
    #   ORDER BY anyo_academico DESC LIMIT 1;
    # UPDATE categoria SET anyo_academico=<anyo>, supercategoria_id=<id> WHERE id_nk=5047;
    # UPDATE categoria SET anyo_academico=<anyo>, supercategoria_id=<id> WHERE id_nk=5021;

    success_message = mark_safe(
        str(_('Se ha actualizado el curso académico actual.'))
        + '<br><br>\n'
        + str(_('Recuerde que a continuación <b>se debe</b>:'))
        + '<br>\n<ul>\n<li>'
        + str(
            _(
                'Mover las categorías «Varios» y «Escuela de Doctorado» del año anterior '
                'a la del año actual, tanto en GEO como en Moodle.'
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
        siguiente_anyo = anyo + 1
        nombre_cat_anyo = f'Cursos {anyo}-{siguiente_anyo}'

        # Crear categoría para el año académico. Vg: «Cursos 2019-2020»
        cat_anyo = self._crear_categoria(anyo, nombre_cat_anyo, None)
        # Crear categoría «No reglada».
        cat_nr = self._crear_categoria(anyo, 'No reglada', cat_anyo.id)
        # Crear las subcategorías de los estudios no reglados
        for nombre in Categoria.NO_REGLADAS:
            self._crear_categoria(anyo, nombre, cat_nr.id)

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

        messages.success(request, _(f"El curso «{curso.nombre}» ha sido borrado con éxito."))
        return super().post(request, *args, **kwargs)


class CursoDetailView(LoginRequiredMixin, DetailView):
    """Muestra información detallada de un curso."""

    model = Curso
    template_name = 'curso/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso_id = self.get_object().id

        mp_form = MatricularPlanForm()
        # Inicializo aquí el valor de `curso_id` en el formulario.
        # No lo paso como un diccionario al crear el formulario, porque entonces
        # `is_bound` sería True, y el campo `nip` se marcaría como `is_invalid`.
        mp_form.fields['curso_id'].initial = curso_id
        context['mp_form'] = mp_form

        pc_form = ProfesorCursoAddForm()
        pc_form.fields['curso_id'].initial = curso_id
        context['pc_form'] = pc_form

        context['asignaciones'] = self.object.profesorcurso_set.filter(
            Q(fecha_baja__gt=timezone.now()) | Q(fecha_baja=None)
        ).select_related

        return context


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


class MatricularPlanView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Matricula en un curso a todos los alumnos del plan indicado."""

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
                f'Se ha matriculado en este curso a todos los alumnos del plan {plan_id_nk}'
                ' ({asignaturas[0].nombre_estudio}, {asignaturas[0].nombre_centro}).'
            ),
        )

        return redirect('curso_detail', curso_id)


class MisAsignaturasView(LoginRequiredMixin, ChecksMixin, SingleTableView):
    """Muestra las asignaturas del usuario, según el POD, y permite crear cursos."""

    table_class = PodTable
    template_name = 'pod/mis_asignaturas.html'

    def get_queryset(self):
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        return Pod.objects.filter(nip=self.request.user.username, anyo_academico=anyo_academico)

    def test_func(self):
        return self.es_pas_o_pdi()


class MisCursosView(LoginRequiredMixin, SingleTableView):
    """Muestra los cursos creados por el usuario."""

    table_class = CursoTable
    template_name = 'curso/mis_cursos.html'

    def get_context_data(self, **kwargs):
        context = super(MisCursosView, self).get_context_data(**kwargs)
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
            datos_recibidos = cliente.crear_curso(curso.get_datos())
            curso.actualizar_tras_creacion(datos_recibidos)
            cliente.matricular_profesor(curso.profesores.first(), curso)
            messages.info(request, _(f'El curso «{curso.nombre}» ha sido autorizado y creado.'))
        else:
            curso.estado = Curso.Estado.DENEGADO
            curso.save()
            messages.info(request, _(f'El curso «{curso.nombre}» ha sido denegado.'))

        self._notifica_resolucion(curso, request.build_absolute_uri('/')[:-1])
        return super().post(request, *args, **kwargs)

    @staticmethod
    def _notifica_resolucion(curso, site_url):
        """Envía un correo al solicitante del curso informando de la resolucíon."""
        send_templated_mail(
            template_name='resolucion',
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=[curso.profesores.first().email],
            context={'curso': curso, 'site_url': site_url},
        )


class SolicitarCursoNoRegladoView(LoginRequiredMixin, ChecksMixin, CreateView):
    """Muestra un formulario para solicitar un curso no reglado."""

    model = Curso
    template_name = 'curso/solicitar.html'

    def get(self, request, *args, **kwargs):
        formulario = CursoSolicitarForm(user=self.request.user)
        return render(request, self.template_name, {'form': formulario})

    def post(self, request, *args, **kwargs):
        formulario = CursoSolicitarForm(data=request.POST, user=self.request.user)
        if formulario.is_valid():
            curso = formulario.save()
            messages.success(
                request, _(f'La solicitud ha sido recibida. Se le avisará cuando se resuelva.')
            )
            self._notifica_solicitud(curso, request.build_absolute_uri('/')[:-1])

            return redirect('mis_cursos')

        return render(request, self.template_name, {'form': formulario})

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _notifica_solicitud(curso, site_url):
        """Envía email a los miembros del grupo Gestores informando de la solicitud."""
        grupo_gestores = Group.objects.get(name='Gestores')
        gestores = grupo_gestores.user_set.all()
        destinatarios = list(map(lambda g: g.email, gestores))
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
    fields = ('nip', 'motivo_solicitud')
    required = ('nip', 'motivo_solicitud')
    template_name = 'forano/solicitar.html'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            forano = form.save(False)
            forano.fecha_solicitud = timezone.now()
            forano.estado = Forano.Estado.SOLICITADO
            forano.solicitante = self.request.user
            forano.save(True)

            self._notifica_solicitud(forano, request.build_absolute_uri('/')[:-1])

            # Establecemos la vinculación
            forano.autorizador = request.user  # Auto
            forano.fecha_autorizacion = timezone.now()
            forano.estado = Forano.Estado.AUTORIZADO
            forano.save()

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
                messages.error(request, _('Se produjo un error. Solicite soporte.'))
                return redirect('forano_solicitud')
            except Exception as ex:
                messages.error(request, 'ERROR: %s' % str(ex))
                return redirect('forano_solicitud')

            response = client.service.creaVinculacion(
                f'{forano.nip}',  # nip
                '53',  # codVinculacion Usuarios invitados a Moodle
                date.today().isoformat(),  # fechaInicio
                (date.today() + relativedelta(years=1)).isoformat(),  # fechaFin (en 1 año)
                self.request.user.username,  # nipResponsable
            )

            if response.aviso:
                messages.warning(request, response.descripcionAviso)

            if response.error:
                messages.error(request, response.descripcionResultado)
            else:
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
        """Envía email a los miembros del grupo Gestores informando de la solicitud."""
        grupo_gestores = Group.objects.get(name='Gestores')
        gestores = grupo_gestores.user_set.all()
        destinatarios = list(map(lambda g: g.email, gestores))
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
#                         f'El NIP «{forano.nip}» ha sido vinculado a Moodle.  Es posible que usted'
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
        # This method is called when valid form data has been POSTed. It should return an HttpResponse.
        cliente = WSClient()
        respuestas = cliente.desmatricular(self.object.profesor, self.object.curso)
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


class ProfesorCursoAnyadirView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Crea una asignación profesor-curso."""

    permission_required = 'geo.anyadir_profesorcurso'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')

    def post(self, request, *args, **kwargs):
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id)

        User = get_user_model()
        nip = request.POST.get('nip')
        profesor = get_object_or_None(User, username=nip)

        if not profesor:
            profesor = User.crear_usuario(request, nip)

        curso.anyadir_profesor(profesor)
        messages.success(request, _('Se ha añadido el profesor al curso.'))

        return redirect('curso_detail', curso_id)
