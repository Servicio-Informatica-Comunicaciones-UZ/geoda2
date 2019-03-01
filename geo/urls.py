from django.urls import path

# from . import views
from .views import HomePageView, ASCrearCursoView, CursoDetailView, MisAsignaturasView, MisCursosView, SolicitarCursoNoRegladoView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("curso/<int:pk>/", CursoDetailView.as_view(), name="curso-detail"),
    path(
        "asignatura-sigma/<int:pk>/crear-curso",
        ASCrearCursoView.as_view(),
        name="as-crear-curso",
    ),
    path("pod/mis-asignaturas", MisAsignaturasView.as_view(), name="mis-asignaturas"),
    path("curso/mis-cursos", MisCursosView.as_view(), name="mis-cursos"),
    path("curso/solicitar", SolicitarCursoNoRegladoView.as_view(), name="solicitar-curso-no-reglado"),
]
