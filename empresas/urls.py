from django.urls import path

from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.EmpresaLista.as_view(), name='lista'),
    path('nueva/', views.EmpresaCrear.as_view(), name='crear'),
    path('<int:pk>/editar/', views.EmpresaEditar.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.EmpresaEliminar.as_view(), name='eliminar'),
]
