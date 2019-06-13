from datetime import date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic.edit import CreateView
from django.views.generic import DetailView, TemplateView
from django_tables2.views import SingleTableView
from .models import AsignaturaSigma, Curso, Pod
from .tables import PodTable, CursoTable
from .forms import SolicitaForm
from .methods import devuelveAñoAcademicoActual


class HomePageView(TemplateView):
    template_name = "home.html"


class ASCrearCursoView(LoginRequiredMixin, View):
    """Crea un nuevo Curso para una asignatura Sigma.
    Si la creación tiene éxito, el navegador es redirigido a la ficha del curso."""

    def get(self, request, *args, **kwargs):
        asignatura_sigma = AsignaturaSigma.objects.get(id=kwargs["pk"])
        curso_existente = asignatura_sigma.get_curso_or_none()
        if curso_existente:
            # TODO: Mensaje Flash
            # TODO: Redirect
            return HttpResponse("El curso ya estaba creado.")

        return HttpResponse(asignatura_sigma.nombre_asignatura)

    def _cargar_asignatura_en_curso(self, asignatura):
        """Crea una nueva instancia de Curso
        con los datos de la asignatura Sigma indicada."""
        pass


class CursoDetailView(LoginRequiredMixin, DetailView):
    model = Curso
    template_name = "curso/detail.html"


class MisAsignaturasView(LoginRequiredMixin, SingleTableView):
    # model = Pod
    # queryset = Pod.objects.all()
    def get_queryset(self):
        fecha = date.today()
        anyo_academico = fecha.year - 1 if fecha.month < 10 else fecha.year
        return Pod.objects.filter(
            nip=self.request.user.username, anyo_academico=anyo_academico
        )

    table_class = PodTable
    template_name = "pod/mis-asignaturas.html"

    # filterset_class = PodFilter


class MisCursosView(LoginRequiredMixin, SingleTableView):

    table_class = CursoTable
    año_academico = devuelveAñoAcademicoActual()
    curso = "{}/{}".format(año_academico, año_academico + 1)
    template_name = "curso/mis-cursos.html"

    def get_context_data(self, **kwargs):
        context = super(MisCursosView, self).get_context_data(**kwargs)
        context["curso"] = self.curso
        return context

    def get_queryset(self):
        return Curso.objects.filter(
            profesores=self.request.user.id, anyo_academico=self.año_academico
        )


class SolicitarCursoNoRegladoView(LoginRequiredMixin, CreateView):

    model = Curso
    template_name = "curso/solicitar.html"

    def get(self, request, *args, **kwargs):
        formulario = SolicitaForm(user=self.request.user)
        return render(request, self.template_name, {"form": formulario})

    def post(self, request, *args, **kwargs):
        formulario = SolicitaForm(data=request.POST, user=self.request.user)
        if formulario.is_valid():
            formulario.save()
            return HttpResponseRedirect("/curso/mis-cursos")

        return render(request, self.template_name, {"form": formulario})

    def form_valid(self, form):
        return super().form_valid(form)
