from django.urls import path

from .views import (
    ASCrearCursoView,
    ASTodasView,
    AyudaView,
    CalendarioActualView,
    CalendarioUpdate,
    CursoDeleteView,
    CursoDetailView,
    CursoRematricularView,
    CursosTodosView,
    CursosPendientesView,
    ForanoDetailView,
    # ForanoResolverView,
    ForanoSolicitarView,
    ForanoTodosView,
    HomePageView,
    MatricularPlanView,
    MisAsignaturasView,
    MisCursosView,
    ProfesorCursoAnularView,
    ProfesorCursoAnyadirView,
    ResolverSolicitudCursoView,
    SolicitarCursoNoRegladoView,
)


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('ayuda/', AyudaView.as_view(), name='ayuda'),
    path('calendario/actual/', CalendarioActualView.as_view(), name='calendario_actual'),
    path('asignatura/<int:pk>/crear-curso/', ASCrearCursoView.as_view(), name='as_crear_curso'),
    path('asignatura/', ASTodasView.as_view(), name='as_todas'),
    path('gestion/calendario/<slug:slug>/', CalendarioUpdate.as_view(), name='calendario'),
    path('gestion/curso/<int:pk>/delete/', CursoDeleteView.as_view(), name='curso_delete'),
    path('gestion/curso/resolver/', ResolverSolicitudCursoView.as_view(), name='curso_resolver'),
    path('gestion/curso/<int:anyo_academico>/', CursosTodosView.as_view(), name='curso_todos'),
    path('gestion/curso/', CursosTodosView.as_view(), name='curso_todos'),
    path('gestion/curso/pendientes/', CursosPendientesView.as_view(), name='curso_pendientes'),
    path('gestion/forano/<int:pk>/', ForanoDetailView.as_view(), name='forano_detail'),
    path('gestion/forano/', ForanoTodosView.as_view(), name='forano_todos'),
    # path('gestion/forano/resolver/', ForanoResolverView.as_view(), name='forano_resolver'),
    path('gestion/matricular-plan/', MatricularPlanView.as_view(), name='matricular_plan'),
    path('gestion/profesor-curso/', ProfesorCursoAnyadirView.as_view(), name='pc_anyadir'),
    path(
        'gestion/profesor-curso/<int:pk>/anular',
        ProfesorCursoAnularView.as_view(),
        name='pc_anular',
    ),
    path('pod/', MisAsignaturasView.as_view(), name='mis_asignaturas'),
    path('curso/<int:pk>/', CursoDetailView.as_view(), name='curso_detail'),
    path('curso/', MisCursosView.as_view(), name='mis_cursos'),
    path('curso/rematricular/', CursoRematricularView.as_view(), name='curso_rematricular'),
    path('curso/solicitar/', SolicitarCursoNoRegladoView.as_view(), name='curso_solicitar'),
    path('usuario-externo/solicitar/', ForanoSolicitarView.as_view(), name='forano_solicitar'),
]
