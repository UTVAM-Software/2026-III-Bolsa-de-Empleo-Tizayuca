from django.urls import path

from . import views

app_name = 'cuentas'

urlpatterns = [
    path('', views.panel, name='panel'),

    path('usuarios/', views.UsuarioLista.as_view(), name='usuario_lista'),
    path('usuarios/nuevo/', views.UsuarioCrear.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioEditar.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/contrasena/', views.UsuarioPassword.as_view(), name='usuario_password'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioEliminar.as_view(), name='usuario_eliminar'),

    path('grupos/', views.GrupoLista.as_view(), name='grupo_lista'),
    path('grupos/nuevo/', views.GrupoCrear.as_view(), name='grupo_crear'),
    path('grupos/<int:pk>/editar/', views.GrupoEditar.as_view(), name='grupo_editar'),
    path('grupos/<int:pk>/eliminar/', views.GrupoEliminar.as_view(), name='grupo_eliminar'),

    path('permisos/', views.PermisoLista.as_view(), name='permiso_lista'),
    path('permisos/nuevo/', views.PermisoCrear.as_view(), name='permiso_crear'),
    path('permisos/<int:pk>/editar/', views.PermisoEditar.as_view(), name='permiso_editar'),
    path('permisos/<int:pk>/eliminar/', views.PermisoEliminar.as_view(), name='permiso_eliminar'),
]
