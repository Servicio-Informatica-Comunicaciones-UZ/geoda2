import json
import zeep
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from requests import Session
from requests.auth import HTTPBasicAuth

from annoying.functions import get_config
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.views.generic.edit import CreateView
from django_tables2.views import SingleTableView
from templated_email import send_templated_mail

from .forms import SolicitaForm
from .models import AsignaturaSigma, Calendario, Curso, Estado, Pod, ProfesorCurso
from .tables import AsignaturasTable, CursoTable, PodTable
from .wsclient import WSClient


class ChecksMixin(UserPassesTestMixin):
    """Proporciona comprobaciones para autorizar o no una acción a un usuario."""

    def es_pas_o_pdi(self):
        """
        Devuelve si el usuario actual es PAS o PDI de la UZ o de sus centros adscritos.
        """
        usuario_actual = self.request.user
        colectivos_del_usuario = json.loads(usuario_actual.colectivos)
        self.permission_denied_message = _(
            "Usted no es PAS ni PDI de la Universidad de Zaragoza"
            " o de sus centros adscritos."
        )

        return any(
            col_autorizado in colectivos_del_usuario
            for col_autorizado in ["PAS", "ADS", "PDI"]
        )


class AyudaView(TemplateView):
    """Muestra la página de ayuda."""

    template_name = "ayuda.html"


class HomePageView(TemplateView):
    """Muestra la página principal."""

    template_name = "home.html"


class ASCrearCursoView(LoginRequiredMixin, ChecksMixin, View):
    """
    Crea un nuevo Curso para una asignatura Sigma.

    Si la creación tiene éxito, el navegador es redirigido a la ficha del curso.
    """

    def get(self, request, *args, **kwargs):
        asignatura = get_object_or_404(AsignaturaSigma, id=kwargs["pk"])
        curso_existente = asignatura.get_curso_or_none()
        if curso_existente:
            messages.error(request, _("El curso ya estaba creado."))
            return redirect("curso-detail", curso_existente.id)

        curso = self._cargar_asignatura_en_curso(asignatura)
        datos_curso = curso.get_datos()

        cliente = WSClient()
        datos_recibidos = cliente.crear_curso(datos_curso)
        curso.actualizar_tras_creacion(datos_recibidos)
        self._anyadir_usuario_como_profesor(curso)
        mensaje = cliente.automatricular(asignatura, curso)
        messages.info(request, mensaje)
        messages.success(request, _("Curso creado correctamente en Moodle."))

        return redirect("curso-detail", curso.id)

    def test_func(self):
        return self.es_pas_o_pdi()

    def _anyadir_usuario_como_profesor(self, curso):
        """
        Añade al usuario que solicita el curso a la lista de profesores del curso.
        """

        profesor_curso = ProfesorCurso(
            curso=curso, profesor=self.request.user, fecha_alta=datetime.today()
        )
        profesor_curso.save()
        messages.warning(
            self.request,
            _(
                "Para acceder como profesor al curso en la plataforma ADD, es posible "
                "que tenga que cerrar la sesión en la plataforma y volver a entrar."
            ),
        )

    def _cargar_asignatura_en_curso(self, asignatura):
        """
        Crea una nueva instancia de Curso con los datos de la asignatura Sigma indicada.
        """

        curso = Curso(
            nombre=asignatura.nombre_asignatura,
            fecha_solicitud=datetime.today(),
            # Las asignaturas Sigm@ se aprueban automáticamente, por el administrador.
            fecha_autorizacion=datetime.today(),
            autorizador_id=1,
            plataforma_id=1,
            categoria=asignatura.get_categoria(),
            anyo_academico=asignatura.anyo_academico,
            asignatura_sigma_id=asignatura.id,
        )
        curso.save()
        return curso


class ASTodasView(LoginRequiredMixin, ChecksMixin, SingleTableView):
    """Muestra todas las asignaturas, y permite crear curso de cualquiera de ellas."""

    table_class = AsignaturasTable
    template_name = "asignatura/todas.html"

    def get_queryset(self):
        anyo_academico = Calendario.get_anyo_academico_actual()
        return AsignaturaSigma.objects.filter(anyo_academico=anyo_academico)

    def test_func(self):
        return self.es_pas_o_pdi()


class CursoDetailView(LoginRequiredMixin, DetailView):
    """Muestra información detallada de un curso."""

    model = Curso
    template_name = "curso/detail.html"


class CursosPendientesView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Muestra los cursos no reglados pendientes de aprobación."""

    permission_required = "geo.cursos_pendientes"
    permission_denied_message = _("Sólo los gestores pueden acceder a esta página.")
    context_object_name = "cursos_pendientes"
    paginate_by = 10
    ordering = ["-fecha_solicitud"]
    queryset = Curso.objects.filter(estado=1)  # Solicitado
    template_name = "gestion/cursos-pendientes.html"


class MisAsignaturasView(LoginRequiredMixin, ChecksMixin, SingleTableView):
    """Muestra las asignaturas del usuario, según el POD, y permite crear cursos."""

    def get_queryset(self):
        anyo_academico = Calendario.get_anyo_academico_actual()
        return Pod.objects.filter(
            nip=self.request.user.username, anyo_academico=anyo_academico
        )

    table_class = PodTable
    template_name = "pod/mis-asignaturas.html"

    def test_func(self):
        return self.es_pas_o_pdi()


class MisCursosView(LoginRequiredMixin, SingleTableView):
    """Muestra los cursos creados por el usuario."""

    table_class = CursoTable
    anyo_academico = Calendario.get_anyo_academico_actual()
    curso = f"{anyo_academico}/{anyo_academico + 1}"
    template_name = "curso/mis-cursos.html"

    def get_context_data(self, **kwargs):
        context = super(MisCursosView, self).get_context_data(**kwargs)
        context["curso"] = self.curso
        return context

    def get_queryset(self):
        return Curso.objects.filter(
            profesores=self.request.user.id, anyo_academico=self.anyo_academico
        )


class ResolverSolicitudCursoView(
    LoginRequiredMixin, PermissionRequiredMixin, RedirectView
):
    """Autoriza o deniega una solicitud de curso."""

    permission_required = "geo.cursos_pendientes"
    permission_denied_message = _("Sólo los gestores pueden acceder a esta página.")

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy("cursos-pendientes")

    def post(self, request, *args, **kwargs):
        id = request.POST.get("id")
        curso = get_object_or_404(Curso, pk=id)
        curso.autorizador = request.user
        curso.fecha_autorizacion = datetime.now()
        curso.motivo_denegacion = request.POST.get("motivo_denegacion")

        if request.POST.get("decision") == "autorizar":
            curso.estado = Estado.objects.get(id=2)  # Autorizado
            curso.save()

            cliente = WSClient()
            datos_recibidos = cliente.crear_curso(curso.get_datos())
            curso.actualizar_tras_creacion(datos_recibidos)
            messages.info(
                request, _(f"El curso «{curso.nombre}» ha sido autorizado y creado.")
            )
        else:
            curso.estado = Estado.objects.get(id=6)  # Denegado
            curso.save()
            messages.info(request, _(f"El curso «{curso.nombre}» ha sido denegado."))

        self._notifica_resolucion(curso)
        return super().post(request, *args, **kwargs)

    def _notifica_resolucion(self, curso):
        """Envía un correo al solicitante del curso informando de la resolucíon."""
        send_templated_mail(
            template_name="resolucion",
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=[curso.profesores.first().email],
            context={"curso": curso, "site_url": get_config("SITE_URL")[:-1]},
        )


class SolicitarCursoNoRegladoView(LoginRequiredMixin, ChecksMixin, CreateView):
    """Muestra un formulario para solicitar un curso no reglado."""

    model = Curso
    template_name = "curso/solicitar.html"

    def get(self, request, *args, **kwargs):
        formulario = SolicitaForm(user=self.request.user)
        return render(request, self.template_name, {"form": formulario})

    def post(self, request, *args, **kwargs):
        formulario = SolicitaForm(data=request.POST, user=self.request.user)
        if formulario.is_valid():
            curso = formulario.save()
            messages.success(
                request,
                _(f"La solicitud ha sido recibida. Se le avisará cuando se resuelva."),
            )
            self._notifica_solicitud(curso)

            return redirect("mis-cursos")

        return render(request, self.template_name, {"form": formulario})

    def test_func(self):
        return self.es_pas_o_pdi()

    def _notifica_solicitud(self, curso):
        """Envía email a los miembros del grupo Gestores informando de la solicitud."""
        grupo_gestores = Group.objects.get(name="Gestores")
        gestores = grupo_gestores.user_set.all()
        destinatarios = list(map(lambda g: g.email, gestores))
        send_templated_mail(
            template_name="solicitud",
            from_email=None,  # settings.DEFAULT_FROM_EMAIL
            recipient_list=destinatarios,
            context={"curso": curso, "site_url": get_config("SITE_URL")[:-1]},
        )


class ForanoView(LoginRequiredMixin, ChecksMixin, View):
    """
    Muestra un formulario para crear una vinculacion de un usuario externo
    en Gestión de Identidades.
    """

    def get(self, request, *args, **kwargs):
        return render(request, "forano/vincular.html")

    def post(self, request, *args, **kwargs):
        nip = request.POST.get("nip")
        wsdl = get_config("WSDL_VINCULACIONES")
        session = Session()
        session.auth = HTTPBasicAuth(
            get_config("USER_VINCULACIONES"), get_config("PASS_VINCULACIONES")
        )
        client = zeep.Client(
            wsdl=wsdl, transport=zeep.transports.Transport(session=session)
        )
        response = client.service.creaVinculacion(
            f"{nip}",  # nip
            "6",  # codVinculacion  FIXME
            date.today().isoformat(),  # fechaInicio
            (date.today() + relativedelta(years=1)).isoformat(),  # fechaFin FIXME
            request.user.username,  # nipResponsable
        )

        if response.error:
            messages.error(request, response.descripcionResultado)
        else:
            messages.success(
                request,
                _(
                    f"El NIP «{nip}» ha sido vinculado a Moodle.  Es posible que usted"
                    " no vea al invitado entre los usuarios de la plataforma hasta que"
                    " el invitado acceda a la plataforma la primera vez."
                ),
            )
        return redirect("vincular-forano")

    def test_func(self):
        return self.es_pas_o_pdi()
