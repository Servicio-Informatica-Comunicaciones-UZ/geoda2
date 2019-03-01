from datetime import date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic.edit import CreateView
from django.views.generic import DetailView, ListView, TemplateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, SingleTableView
from django_tables2 import RequestConfig
from .models import AsignaturaSigma, Curso, Pod
from .tables import PodTable, CursoTable
from .forms import SolicitaForm


class HomePageView(TemplateView):
    template_name = "home.html"


class ASCrearCursoView(LoginRequiredMixin, View):
    """Crea un nuevo Curso para una asignatura Sigma.
    Si la creación tiene éxito, el navegador es redirigido a la ficha del curso."""

    def get(self, request, *args, **kwargs):
        asignatura_sigma = AsignaturaSigma.objects.get(id=kwargs['pk'])
        curso_existente = asignatura_sigma.get_curso_or_none()
        if (curso_existente):
            # TODO: Mensaje Flash
            # TODO: Redirect
            return HttpResponse("El curso ya estaba creado.")

        return HttpResponse(asignatura_sigma.nombre_asignatura)

    def _cargar_asignatura_en_curso(self, asignatura):
        """Crea una nueva instancia de Curso con los datos de la asignatura Sigma indicada."""
        pass


class CursoDetailView(LoginRequiredMixin, DetailView):
    model = Curso
    template_name = "curso/detail.html"


# class MisAsignaturasView(ListView):  # We subclass ListView.  It returns object_list .
#    model = Pod
#    template_name = 'pod/mis-asignaturas.html'
#    # https://docs.djangoproject.com/en/2.1/topics/class-based-views/generic-display/#making-friendly-template-contexts
#    context_object_name = 'pod_list'  # Le damos un nombre más descriptivo que object_list

# def misAsignaturas(request):
#    table = PodTable(Pod.objects.all())
#    RequestConfig(request).configure(table)
#    return render(request, 'pod/mis-asignaturas.html', {'table': table})


class MisAsignaturasView(LoginRequiredMixin, SingleTableView):
    # model = Pod
    # queryset = Pod.objects.all()
    def get_queryset(self):
        fecha = date.today()
        anyo_academico = fecha.year - 1 if fecha.month < 10 else fecha.year
        return Pod.objects.filter(nip=self.request.user.username, anyo_academico=2018)

    table_class = PodTable
    template_name = "pod/mis-asignaturas.html"

    # filterset_class = PodFilter

class MisCursosView(LoginRequiredMixin, SingleTableView):

    def get_queryset(self):
        fecha = date.today()
        anyo_academico = fecha.year - 1 if fecha.month < 10 else fecha.year
        return Curso.objects.filter(profesores=self.request.user.id, anyo_academico=2018)

    table_class = CursoTable
    template_name = "curso/mis-cursos.html"

class SolicitarCursoNoRegladoView(LoginRequiredMixin, CreateView):

    model = Curso
    template_name = "curso/solicitar.html"
    form_class = SolicitaForm
