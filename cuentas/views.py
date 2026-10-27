"""Gestión de Django Auth (User, Group, Permission) desde la propia app, sin depender de /admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.functional import cached_property
from django.views.generic import FormView

from .forms import GrupoForm, PermisoForm, UsuarioCrearForm, UsuarioEditarForm
from .mixins import CrearBase, EditarBase, EliminarBase, ListaBase


@login_required
def panel(request):
    """Página a la que llega el usuario al iniciar sesión.
    Solo muestra los módulos para los que tiene permiso."""
    modulos = [
        ('Gestión', [
            ('vacantes.view_vacante', 'vacantes:lista', 'Vacantes', 'Publicar y administrar vacantes'),
            ('postulaciones.view_postulacion', 'postulaciones:lista', 'Postulaciones', 'Solicitudes a vacantes'),
            ('empresas.view_empresa', 'empresas:lista', 'Empresas', 'Negocios y empresas registradas'),
            ('candidatos.view_candidato', 'candidatos:lista', 'Candidatos', 'Perfiles de buscadores de empleo'),
            ('candidatos.view_experiencia', 'candidatos:experiencia_lista', 'Experiencia laboral', 'Historial de trabajos'),
        ]),
        ('Catálogos', [
            ('vacantes.view_categoria', 'vacantes:categoria_lista', 'Categorías', 'Giros de las vacantes'),
            ('candidatos.view_habilidad', 'candidatos:habilidad_lista', 'Habilidades', 'Habilidades de los candidatos'),
        ]),
        ('Usuarios y seguridad', [
            ('auth.view_user', 'cuentas:usuario_lista', 'Usuarios', 'Cuentas, contraseñas y roles'),
            ('auth.view_group', 'cuentas:grupo_lista', 'Grupos', 'Roles y sus permisos'),
            ('auth.view_permission', 'cuentas:permiso_lista', 'Permisos', 'Permisos del sistema'),
        ]),
    ]
    secciones = []
    for seccion, items in modulos:
        visibles = [i for i in items if request.user.has_perm(i[0])]
        if visibles:
            secciones.append((seccion, visibles))
    return render(request, 'cuentas/panel.html', {'secciones': secciones})


# ---------------------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------------------

class UsuarioRutas:
    model = User
    titulo = 'Usuarios'
    url_lista = 'cuentas:usuario_lista'
    url_crear = 'cuentas:usuario_crear'
    url_editar = 'cuentas:usuario_editar'
    url_eliminar = 'cuentas:usuario_eliminar'


class FormUsuarioMixin:
    """Le avisa al formulario si quien lo usa puede crear superusuarios."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['puede_superusuario'] = self.request.user.is_superuser
        return kwargs


class UsuarioLista(LoginRequiredMixin, PermissionRequiredMixin, UsuarioRutas, ListaBase):
    permission_required = 'auth.view_user'
    template_name = 'cuentas/usuario_lista.html'
    columnas = [('Usuario', 'username'), ('Nombre', 'get_full_name'), ('Correo', 'email'),
                ('Grupos', 'groups'), ('Activo', 'is_active'), ('Superusuario', 'is_superuser')]
    buscar_en = ['username', 'first_name', 'last_name', 'email']
    ordering = ['username']

    def get_queryset(self):
        return super().get_queryset().prefetch_related('groups')


class UsuarioCrear(LoginRequiredMixin, PermissionRequiredMixin, UsuarioRutas, FormUsuarioMixin, CrearBase):
    permission_required = 'auth.add_user'
    form_class = UsuarioCrearForm


class SinTocarSuperusuariosMixin:
    """Un administrador que no es superusuario no puede editar ni borrar superusuarios."""

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs


class UsuarioEditar(LoginRequiredMixin, PermissionRequiredMixin, UsuarioRutas,
                    SinTocarSuperusuariosMixin, FormUsuarioMixin, EditarBase):
    permission_required = 'auth.change_user'
    form_class = UsuarioEditarForm


class UsuarioEliminar(LoginRequiredMixin, PermissionRequiredMixin, UsuarioRutas,
                      SinTocarSuperusuariosMixin, EliminarBase):
    permission_required = 'auth.delete_user'

    def form_valid(self, form):
        if self.object == self.request.user:
            messages.error(self.request, 'No puedes eliminar tu propia cuenta.')
            return redirect(self.url_lista)
        return super().form_valid(form)


class UsuarioPassword(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Cambiar la contraseña de otro usuario (como en el admin de Django)."""
    permission_required = 'auth.change_user'
    form_class = SetPasswordForm
    template_name = 'crud/formulario.html'

    @cached_property
    def usuario(self):
        # Se busca DESPUÉS de validar login y permiso (por eso no va en dispatch)
        qs = User.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return get_object_or_404(qs, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.usuario
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo_pagina'] = f'Cambiar contraseña: {self.usuario.username}'
        ctx['cancelar'] = 'cuentas:usuario_lista'
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Contraseña de "{self.usuario.username}" actualizada.')
        return redirect('cuentas:usuario_lista')


# ---------------------------------------------------------------------------
# Grupos (roles)
# ---------------------------------------------------------------------------

class GrupoRutas:
    model = Group
    titulo = 'Grupos'
    url_lista = 'cuentas:grupo_lista'
    url_crear = 'cuentas:grupo_crear'
    url_editar = 'cuentas:grupo_editar'
    url_eliminar = 'cuentas:grupo_eliminar'


class GrupoLista(LoginRequiredMixin, PermissionRequiredMixin, GrupoRutas, ListaBase):
    permission_required = 'auth.view_group'
    columnas = [('Nombre', 'name'), ('Usuarios', 'num_usuarios'), ('Permisos', 'num_permisos')]
    buscar_en = ['name']
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset().annotate(
            num_usuarios=Count('user', distinct=True), num_permisos=Count('permissions', distinct=True))


class GrupoCrear(LoginRequiredMixin, PermissionRequiredMixin, GrupoRutas, CrearBase):
    permission_required = 'auth.add_group'
    form_class = GrupoForm


class GrupoEditar(LoginRequiredMixin, PermissionRequiredMixin, GrupoRutas, EditarBase):
    permission_required = 'auth.change_group'
    form_class = GrupoForm


class GrupoEliminar(LoginRequiredMixin, PermissionRequiredMixin, GrupoRutas, EliminarBase):
    permission_required = 'auth.delete_group'


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------

class PermisoRutas:
    model = Permission
    titulo = 'Permisos'
    url_lista = 'cuentas:permiso_lista'
    url_crear = 'cuentas:permiso_crear'
    url_editar = 'cuentas:permiso_editar'
    url_eliminar = 'cuentas:permiso_eliminar'


class PermisoLista(LoginRequiredMixin, PermissionRequiredMixin, PermisoRutas, ListaBase):
    permission_required = 'auth.view_permission'
    columnas = [('App', 'content_type__app_label'), ('Modelo', 'content_type__name'),
                ('Código', 'codename'), ('Descripción', 'name')]
    buscar_en = ['name', 'codename', 'content_type__app_label']
    ordering = ['content_type__app_label', 'content_type__model', 'codename']

    def get_queryset(self):
        return super().get_queryset().select_related('content_type')


class PermisoCrear(LoginRequiredMixin, PermissionRequiredMixin, PermisoRutas, CrearBase):
    permission_required = 'auth.add_permission'
    form_class = PermisoForm


class PermisoEditar(LoginRequiredMixin, PermissionRequiredMixin, PermisoRutas, EditarBase):
    permission_required = 'auth.change_permission'
    form_class = PermisoForm


class PermisoEliminar(LoginRequiredMixin, PermissionRequiredMixin, PermisoRutas, EliminarBase):
    permission_required = 'auth.delete_permission'
