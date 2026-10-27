"""Piezas reutilizables para todas las vistas CRUD del sistema.

Las vistas concretas SIEMPRE declaran explícitamente:
    class XLista(LoginRequiredMixin, PermissionRequiredMixin, ListaBase):
        permission_required = 'app.view_modelo'
para que el control de acceso (OWASP A01) se vea claro en cada vista.
"""
from functools import reduce
from operator import or_

from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, ListView, UpdateView


def es_admin(user):
    """Administrador = superusuario o miembro del grupo 'Administradores' (el municipio)."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name='Administradores').exists()
    )


class PropietarioMixin:
    """Control de acceso horizontal (OWASP A01 / IDOR).

    `campos_propietario` son rutas hacia el usuario dueño del registro, por ejemplo
    ('usuario',) o ('candidato__usuario', 'vacante__empresa__usuario').
    Un usuario que no es administrador solo obtiene los registros que le pertenecen;
    si escribe a mano la URL de un registro ajeno, Django responde 404.
    Si `campos_propietario` está vacío, el modelo es un catálogo (todos ven todo).
    """
    campos_propietario = ()

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not self.campos_propietario or es_admin(user):
            return qs
        filtro = reduce(or_, [Q(**{campo: user}) for campo in self.campos_propietario])
        return qs.filter(filtro).distinct()


class ContextoCrudMixin:
    """Datos que usan las plantillas genéricas de templates/crud/."""
    titulo = ''
    url_lista = url_crear = url_editar = url_eliminar = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.model._meta
        user = self.request.user
        ctx.update({
            'titulo': self.titulo,
            'cancelar': self.url_lista,
            'url_lista': self.url_lista,
            'url_crear': self.url_crear,
            'url_editar': self.url_editar,
            'url_eliminar': self.url_eliminar,
            'puede_crear': user.has_perm(f'{meta.app_label}.add_{meta.model_name}'),
            'puede_editar': user.has_perm(f'{meta.app_label}.change_{meta.model_name}'),
            'puede_eliminar': user.has_perm(f'{meta.app_label}.delete_{meta.model_name}'),
        })
        return ctx


class ListaBase(PropietarioMixin, ContextoCrudMixin, ListView):
    template_name = 'crud/lista.html'
    paginate_by = 20
    columnas = []        # [('Encabezado', 'campo__o__propiedad'), ...]
    buscar_en = []       # campos para el buscador: ['nombre', 'empresa__nombre']

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q and self.buscar_en:
            qs = qs.filter(reduce(or_, [Q(**{f'{c}__icontains': q}) for c in self.buscar_en]))
        if not qs.ordered:
            qs = qs.order_by('-pk')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['columnas'] = self.columnas
        ctx['q'] = self.request.GET.get('q', '').strip()
        ctx['con_buscador'] = bool(self.buscar_en)
        return ctx


class FormularioBase(ContextoCrudMixin):
    template_name = 'crud/formulario.html'

    def get_success_url(self):
        from django.urls import reverse
        return reverse(self.url_lista)

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f'"{self.object}" guardado correctamente.')
        return respuesta


class CrearBase(FormularioBase, CreateView):
    pass


class EditarBase(PropietarioMixin, FormularioBase, UpdateView):
    pass


class EliminarBase(PropietarioMixin, ContextoCrudMixin, DeleteView):
    template_name = 'crud/confirmar_eliminar.html'

    def get_success_url(self):
        from django.urls import reverse
        return reverse(self.url_lista)

    def form_valid(self, form):
        nombre = str(self.object)
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, f'No se puede eliminar "{nombre}" porque otros registros dependen de él.')
            return redirect(self.url_lista)
        messages.success(self.request, f'"{nombre}" eliminado.')
        return respuesta


class AsignarUsuarioMixin:
    """Para perfiles 1 a 1 con el usuario (Empresa, Candidato).
    El administrador elige el usuario; cualquier otro crea SU propio perfil."""

    def dispatch(self, request, *args, **kwargs):
        if (request.user.has_perm(self.permission_required) and not es_admin(request.user)
                and self.model.objects.filter(usuario=request.user).exists()):
            messages.info(request, 'Ya tienes tu perfil registrado.')
            return redirect(self.url_lista)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['es_admin'] = es_admin(self.request.user)
        return kwargs

    def form_valid(self, form):
        if not es_admin(self.request.user):
            form.instance.usuario = self.request.user
        return super().form_valid(form)
