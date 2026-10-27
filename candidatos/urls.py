from django.urls import path

from . import views

app_name = 'candidatos'

urlpatterns = [
    path('', views.CandidatoLista.as_view(), name='lista'),
    path('nuevo/', views.CandidatoCrear.as_view(), name='crear'),
    path('<int:pk>/editar/', views.CandidatoEditar.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.CandidatoEliminar.as_view(), name='eliminar'),

    path('habilidades/', views.HabilidadLista.as_view(), name='habilidad_lista'),
    path('habilidades/nueva/', views.HabilidadCrear.as_view(), name='habilidad_crear'),
    path('habilidades/<int:pk>/editar/', views.HabilidadEditar.as_view(), name='habilidad_editar'),
    path('habilidades/<int:pk>/eliminar/', views.HabilidadEliminar.as_view(), name='habilidad_eliminar'),

    path('experiencia/', views.ExperienciaLista.as_view(), name='experiencia_lista'),
    path('experiencia/nueva/', views.ExperienciaCrear.as_view(), name='experiencia_crear'),
    path('experiencia/<int:pk>/editar/', views.ExperienciaEditar.as_view(), name='experiencia_editar'),
    path('experiencia/<int:pk>/eliminar/', views.ExperienciaEliminar.as_view(), name='experiencia_eliminar'),
]
