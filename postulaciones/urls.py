from django.urls import path

from . import views

app_name = 'postulaciones'

urlpatterns = [
    path('', views.PostulacionLista.as_view(), name='lista'),
    path('nueva/', views.PostulacionCrear.as_view(), name='crear'),
    path('<int:pk>/editar/', views.PostulacionEditar.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.PostulacionEliminar.as_view(), name='eliminar'),
]
