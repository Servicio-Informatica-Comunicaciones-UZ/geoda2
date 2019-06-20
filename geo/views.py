from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView
from django_tables2.views import SingleTableView

from .forms import SolicitaForm
from .models import AsignaturaSigma, Calendario, Curso, Pod
from .tables import CursoTable, PodTable


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
        asignatura_sigma = AsignaturaSigma.objects.get(id=kwargs["pk"])
        curso_existente = asignatura_sigma.get_curso_or_none()
        if curso_existente:
            # TODO: Mensaje Flash
            # TODO: Redirect
            return HttpResponse("El curso ya estaba creado.")

        return HttpResponse(asignatura_sigma.nombre_asignatura)

    def _cargar_asignatura_en_curso(self, asignatura):
        """
        Crea una nueva instancia de `Curso`.

        Crea una nueva instancia de Curso con los datos de la asignatura Sigma indicada.
        """
        pass


class CursoDetailView(LoginRequiredMixin, DetailView):
    """Muestra información detallada de un curso."""

    model = Curso
    template_name = "curso/detail.html"


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
