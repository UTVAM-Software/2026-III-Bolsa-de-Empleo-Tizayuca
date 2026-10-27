from django.urls import path

from . import views

app_name = 'vacantes'

urlpatterns = [
    # Pública
    path('', views.inicio, name='inicio'),

    # Gestión de vacantes (con login)
    path('gestion/vacantes/', views.VacanteLista.as_view(), name='lista'),
    path('gestion/vacantes/nueva/', views.VacanteCrear.as_view(), name='crear'),
    path('gestion/vacantes/<int:pk>/editar/', views.VacanteEditar.as_view(), name='editar'),
    path('gestion/vacantes/<int:pk>/eliminar/', views.VacanteEliminar.as_view(), name='eliminar'),

    # Gestión de categorías
    path('gestion/categorias/', views.CategoriaLista.as_view(), name='categoria_lista'),
    path('gestion/categorias/nueva/', views.CategoriaCrear.as_view(), name='categoria_crear'),
    path('gestion/categorias/<int:pk>/editar/', views.CategoriaEditar.as_view(), name='categoria_editar'),
    path('gestion/categorias/<int:pk>/eliminar/', views.CategoriaEliminar.as_view(), name='categoria_eliminar'),
]
