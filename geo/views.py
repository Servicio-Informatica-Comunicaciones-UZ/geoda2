from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView
from django_tables2.views import SingleTableView

from .forms import SolicitaForm
from .models import AsignaturaSigma, Calendario, Curso, Pod, ProfesorCurso
from .tables import CursoTable, PodTable
from .wsclient import WSClient


class AyudaView(TemplateView):
    """Muestra la página de ayuda."""

    template_name = "ayuda.html"


class HomePageView(TemplateView):
    """Muestra la página principal."""

    template_name = "home.html"


class ASCrearCursoView(LoginRequiredMixin, View):
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

        return redirect("curso-detail", curso.id)

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


class MisAsignaturasView(LoginRequiredMixin, SingleTableView):
    """Muestra las asignaturas del usuario, según el POD, y permite crear cursos."""

    def get_queryset(self):
        anyo_academico = Calendario.get_anyo_academico_actual()
        return Pod.objects.filter(
            nip=self.request.user.username, anyo_academico=anyo_academico
        )

    table_class = PodTable
    template_name = "pod/mis-asignaturas.html"


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


class SolicitarCursoNoRegladoView(LoginRequiredMixin, CreateView):
    """Muestra un formulario para solicitar un curso no reglado."""

    model = Curso
    template_name = "curso/solicitar.html"

    def get(self, request, *args, **kwargs):
        formulario = SolicitaForm(user=self.request.user)
        return render(request, self.template_name, {"form": formulario})

    def post(self, request, *args, **kwargs):
        formulario = SolicitaForm(data=request.POST, user=self.request.user)
        if formulario.is_valid():
            formulario.save()
            return redirect("mis-cursos")

        return render(request, self.template_name, {"form": formulario})
