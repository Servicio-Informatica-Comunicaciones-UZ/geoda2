from django.urls import path

from .views import (
    ASCrearCursoView,
    ASTodasView,
    AyudaView,
    CalendarioUpdate,
    CursoDetailView,
    CursosTodosView,
    CursosPendientesView,
    ForanoDetailView,
    ForanoResolverView,
    ForanoSolicitarView,
    ForanoTodosView,
    HomePageView,
    MatricularPlanView,
    MisAsignaturasView,
    MisCursosView,
    ResolverSolicitudCursoView,
    SolicitarCursoNoRegladoView,
)


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('ayuda/', AyudaView.as_view(), name='ayuda'),
    path('asignatura/<int:pk>/crear-curso', ASCrearCursoView.as_view(), name='as-crear-curso'),
    path('asignatura/todas', ASTodasView.as_view(), name='as-todas'),
    path('gestion/calendario/<slug:slug>', CalendarioUpdate.as_view(), name='calendario'),
    path('gestion/cursos-todos/<int:anyo_academico>', CursosTodosView.as_view(), name='cursos-todos'),
    path('gestion/cursos-todos', CursosTodosView.as_view(), name='cursos-todos'),
    path('gestion/cursos-pendientes', CursosPendientesView.as_view(), name='cursos-pendientes'),
    path('gestion/forano/<int:pk>/', ForanoDetailView.as_view(), name='forano-detail'),
    path('gestion/forano-todos', ForanoTodosView.as_view(), name='forano-todos'),
    path('gestion/forano/resolver', ForanoResolverView.as_view(), name='forano-resolver'),
    path('gestion/matricular-plan', MatricularPlanView.as_view(), name='matricular-plan'),
    path('pod/mis-asignaturas', MisAsignaturasView.as_view(), name='mis-asignaturas'),
    path('curso/<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    path('curso/mis-cursos', MisCursosView.as_view(), name='mis-cursos'),
    path('curso/resolver-solicitud', ResolverSolicitudCursoView.as_view(), name='resolver-solicitud'),
    path('curso/solicitar', SolicitarCursoNoRegladoView.as_view(), name='curso-solicitar'),
    path('usuario-externo/solicitar', ForanoSolicitarView.as_view(), name='forano-solicitar'),
]
