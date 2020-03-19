from datetime import date, datetime
import json
from dateutil.relativedelta import relativedelta
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestConnectionError
import zeep

from annoying.functions import get_config, get_object_or_None
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, RedirectView, TemplateView, UpdateView
from django.views.generic.edit import CreateView
from django_tables2.views import SingleTableView
from templated_email import send_templated_mail

from .filters import AsignaturaListFilter
from .forms import SolicitaForm, AsignaturaFilterFormHelper
from .models import Asignatura, Calendario, Categoria, Curso, Estado, Pod, ProfesorCurso
from .tables import AsignaturasTable, CursosCreadosTable, CursosPendientesTable, CursoTable, PodTable
from .utils import PagedFilteredTableView
from .wsclient import WSClient


class ChecksMixin(UserPassesTestMixin):
    """Proporciona comprobaciones para autorizar o no una acción a un usuario."""

    def es_pas_o_pdi(self):
        """Devuelve si el usuario es PAS o PDI de la UZ o de sus centros adscritos."""
        usuario_actual = self.request.user
        colectivos_del_usuario = json.loads(usuario_actual.colectivos) if usuario_actual.colectivos else []
        self.permission_denied_message = _(
            'Usted no es PAS ni PDI de la Universidad de Zaragoza' ' o de sus centros adscritos.'
        )

        return any(col_autorizado in colectivos_del_usuario for col_autorizado in ['PAS', 'ADS', 'PDI'])

    def test_func(self):
        raise NotImplementedError(
            '{0} carece de la implementación del método test_func().'.format(self.__class__.__name__)
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
            return redirect('curso-detail', asignatura.curso.id)

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

        return redirect('curso-detail', curso.id)

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _cargar_asignatura_en_curso(asignatura):
        """Crea una nueva instancia de Curso con los datos de la asignatura indicada."""
        curso = Curso(
            nombre=asignatura.nombre_asignatura,
            fecha_solicitud=datetime.today(),
            # Las asignaturas Sigm@ se aprueban automáticamente, por el administrador.
            fecha_autorizacion=datetime.today(),
            autorizador_id=1,
            plataforma_id=1,
            categoria=asignatura.get_categoria(),
            anyo_academico=asignatura.anyo_academico,
            asignatura_id=asignatura.id,
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
        return Asignatura.objects.filter(anyo_academico=anyo_academico)

    def test_func(self):
        return self.es_pas_o_pdi()


class CalendarioUpdate(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    """Muestra un formulario para actualizar el año académico actual."""

    permission_required = 'geo.calendario'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    model = Calendario
    fields = ('anyo',)
    template_name = 'gestion/calendario_form.html'
    success_message = mark_safe(
        str(_('Se ha actualizado el curso académico actual.'))
        + '<br><br>\n'
        + str(_('Recuerde que a continuación <b>se debe</b>:'))
        + '<br>\n<ul>\n<li>'
        + str(
            _(
                'Mover los cursos de las categoría «Varios» del año anterior '
                'a la del año actual, tanto en GEO como en Moodle.'
            )
        )
        + '</li>\n<li>'
        + str(_('Ídem con los cursos de la categoría «Escuela de Doctorado».'))
        + '</li>\n<li>'
        + str(_('Actualizar el año en las pasarelas de GEO ' '(carga de asignaturas y POD).'))
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
        # Crear categorías «Varios», «Escuela de Doctorado» y «No reglada».
        self._crear_categoria(anyo, 'Varios', cat_anyo.id)
        self._crear_categoria(anyo, 'Escuela de Doctorado', cat_anyo.id)
        cat_nr = self._crear_categoria(anyo, 'No reglada', cat_anyo.id)
        # Crear las subcategorías de los estudios no reglados
        for nombre in Categoria.NO_REGLADAS:
            self._crear_categoria(anyo, nombre, cat_nr.id)

        return super().form_valid(form)

    @staticmethod
    def _crear_categoria(anyo, nombre, supercategoria_id):
        """Comprueba si existe la categoría, y la crea si es necesario."""
        cat = get_object_or_None(Categoria, anyo_academico=anyo, nombre=nombre, supercategoria_id=supercategoria_id)
        if not cat:
            cat = Categoria(plataforma_id=1, anyo_academico=anyo, nombre=nombre, supercategoria_id=supercategoria_id)
            cat.save()
        if not cat.id_nk:
            cat.crear_en_plataforma()
        return cat


class CursoDetailView(LoginRequiredMixin, DetailView):
    """Muestra información detallada de un curso."""

    model = Curso
    template_name = 'curso/detail.html'


class CursosCreadosView(LoginRequiredMixin, PermissionRequiredMixin, SingleTableView):
    """Muestra los cursos creados en un año dado."""

    permission_required = 'geo.cursos_creados'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    paginate_by = 20
    table_class = CursosCreadosTable
    template_name = 'gestion/cursos-creados.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anyo_academico = self.kwargs.get('anyo_academico') or Calendario.objects.get(slug='actual').anyo
        context['curso'] = f'{anyo_academico}/{anyo_academico + 1}'
        return context

    def get_queryset(self):
        anyo_academico = self.kwargs.get('anyo_academico') or Calendario.objects.get(slug='actual').anyo
        return Curso.objects.filter(estado=3, anyo_academico=anyo_academico)  # Creados este año


class CursosPendientesView(LoginRequiredMixin, PermissionRequiredMixin, SingleTableView):
    """Muestra los cursos no reglados pendientes de aprobación."""

    permission_required = 'geo.cursos_pendientes'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')
    context_object_name = 'cursos_pendientes'
    paginate_by = 20
    ordering = ['-fecha_solicitud']
    queryset = Curso.objects.filter(estado=1)  # Solicitado
    table_class = CursosPendientesTable
    template_name = 'gestion/cursos-pendientes.html'


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
            return redirect('curso-detail', curso_id)

        asignaturas = Asignatura.objects.filter(anyo_academico=curso.anyo_academico, plan_id_nk=plan_id_nk)
        cliente = WSClient()

        try:
            for asignatura in asignaturas:
                cliente.automatricular(asignatura, curso, active=1)
        except Exception as ex:
            messages.error(request, 'ERROR: %s' % str(ex))
            return redirect('curso-detail', curso_id)

        messages.success(
            request,
            _(
                f'Se ha matriculado en este curso a todos los alumnos del plan {plan_id_nk}'
                ' ({asignaturas[0].nombre_estudio}, {asignaturas[0].nombre_centro}).'
            ),
        )

        return redirect('curso-detail', curso_id)


class MisAsignaturasView(LoginRequiredMixin, ChecksMixin, SingleTableView):
    """Muestra las asignaturas del usuario, según el POD, y permite crear cursos."""

    table_class = PodTable
    template_name = 'pod/mis-asignaturas.html'

    def get_queryset(self):
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        return Pod.objects.filter(nip=self.request.user.username, anyo_academico=anyo_academico)

    def test_func(self):
        return self.es_pas_o_pdi()


class MisCursosView(LoginRequiredMixin, SingleTableView):
    """Muestra los cursos creados por el usuario."""

    table_class = CursoTable
    template_name = 'curso/mis-cursos.html'

    def get_context_data(self, **kwargs):
        context = super(MisCursosView, self).get_context_data(**kwargs)
        anyo_academico = Calendario.objects.get(slug='actual').anyo
        context['curso'] = f'{anyo_academico}/{anyo_academico + 1}'
        return context

    def get_queryset(self):
        return Curso.objects.filter(
            profesores=self.request.user.id, anyo_academico=Calendario.objects.get(slug='actual').anyo
        )


class ResolverSolicitudCursoView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    """Autoriza o deniega una solicitud de curso."""

    permission_required = 'geo.cursos_pendientes'
    permission_denied_message = _('Sólo los gestores pueden acceder a esta página.')

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('cursos-pendientes')

    def post(self, request, *args, **kwargs):
        id_recibido = request.POST.get('id')
        curso = get_object_or_404(Curso, pk=id_recibido)
        curso.autorizador = request.user
        curso.fecha_autorizacion = datetime.now()
        curso.comentarios = request.POST.get('comentarios')

        if request.POST.get('decision') == 'autorizar':
            curso.estado = Estado.objects.get(id=2)  # Autorizado
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
            curso.estado = Estado.objects.get(id=6)  # Denegado
            curso.save()
            messages.info(request, _(f'El curso «{curso.nombre}» ha sido denegado.'))

        self._notifica_resolucion(curso)
        return super().post(request, *args, **kwargs)

    @staticmethod
    def _notifica_resolucion(curso):
        """Envía un correo al solicitante del curso informando de la resolucíon."""
        send_templated_mail(
            template_name='resolucion',
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=[curso.profesores.first().email],
            context={'curso': curso, 'site_url': get_config('SITE_URL')},
        )


class SolicitarCursoNoRegladoView(LoginRequiredMixin, ChecksMixin, CreateView):
    """Muestra un formulario para solicitar un curso no reglado."""

    model = Curso
    template_name = 'curso/solicitar.html'

    def get(self, request, *args, **kwargs):
        formulario = SolicitaForm(user=self.request.user)
        return render(request, self.template_name, {'form': formulario})

    def post(self, request, *args, **kwargs):
        formulario = SolicitaForm(data=request.POST, user=self.request.user)
        if formulario.is_valid():
            curso = formulario.save()
            messages.success(request, _(f'La solicitud ha sido recibida. Se le avisará cuando se resuelva.'))
            self._notifica_solicitud(curso)

            return redirect('mis-cursos')

        return render(request, self.template_name, {'form': formulario})

    def test_func(self):
        return self.es_pas_o_pdi()

    @staticmethod
    def _notifica_solicitud(curso):
        """Envía email a los miembros del grupo Gestores informando de la solicitud."""
        grupo_gestores = Group.objects.get(name='Gestores')
        gestores = grupo_gestores.user_set.all()
        destinatarios = list(map(lambda g: g.email, gestores))
        send_templated_mail(
            template_name='solicitud',
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=destinatarios,
            context={'curso': curso, 'site_url': get_config('SITE_URL')},
        )


class ForanoView(LoginRequiredMixin, ChecksMixin, View):
    """Crea una vinculacion de un usuario externo en Gestión de Identidades."""

    def get(self, request, *args, **kwargs):
        return render(request, 'forano/vincular.html')

    def post(self, request, *args, **kwargs):
        nip = request.POST.get('nip')
        wsdl = get_config('WSDL_VINCULACIONES')
        session = Session()
        session.auth = HTTPBasicAuth(get_config('USER_VINCULACIONES'), get_config('PASS_VINCULACIONES'))

        try:
            client = zeep.Client(wsdl=wsdl, transport=zeep.transports.Transport(session=session))
        except RequestConnectionError:
            messages.error(request, 'No fue posible conectarse al WS de Identidades.')
            return redirect('vincular-forano')
        except Exception as ex:
            messages.error(request, 'ERROR: %s' % str(ex))
            return redirect('vincular-forano')

        response = client.service.creaVinculacion(
            f'{nip}',  # nip
            '53',  # codVinculacion Usuarios invitados a Moodle
            date.today().isoformat(),  # fechaInicio
            (date.today() + relativedelta(years=1)).isoformat(),  # fechaFin
            request.user.username,  # nipResponsable
        )

        if response.aviso:
            messages.warning(request, response.descripcionAviso)

        if response.error:
            messages.error(request, response.descripcionResultado)
        else:
            messages.success(
                request,
                _(
                    f'El NIP «{nip}» ha sido vinculado a Moodle.  Es posible que usted'
                    ' no vea al invitado entre los usuarios de la plataforma hasta que'
                    ' el invitado acceda a la plataforma la primera vez.'
                ),
            )
        return redirect('vincular-forano')

    def test_func(self):
        return self.es_pas_o_pdi()
