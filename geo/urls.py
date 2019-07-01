from django.urls import path

from .views import (
    ASCrearCursoView,
    AyudaView,
    CursoDetailView,
    CursosPendientesView,
    HomePageView,
    MisAsignaturasView,
    MisCursosView,
    ResolverSolicitudCursoView,
    SolicitarCursoNoRegladoView,
)


urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("ayuda/", AyudaView.as_view(), name="ayuda"),
    path("curso/<int:pk>/", CursoDetailView.as_view(), name="curso-detail"),
    path(
        "asignatura-sigma/<int:pk>/crear-curso",
        ASCrearCursoView.as_view(),
        name="as-crear-curso",
    ),
    path(
        "gestion/cursos-pendientes",
        CursosPendientesView.as_view(),
        name="cursos-pendientes",
    ),
    path("pod/mis-asignaturas", MisAsignaturasView.as_view(), name="mis-asignaturas"),
    path("curso/mis-cursos", MisCursosView.as_view(), name="mis-cursos"),
    path(
        "curso/resolver-solicitud",
        ResolverSolicitudCursoView.as_view(),
        name="resolver-solicitud",
    ),
    path(
        "curso/solicitar", SolicitarCursoNoRegladoView.as_view(), name="curso-solicitar"
    ),
]
