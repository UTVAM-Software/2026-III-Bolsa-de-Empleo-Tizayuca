from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from empresas.models import Empresa

from .forms import CategoriaForm, VacanteForm
from .models import Categoria, Vacante


def es_admin(user):
    """Administrador = superusuario o miembro del grupo 'Administradores' (el municipio)."""
    return user.is_superuser or user.groups.filter(name='Administradores').exists()


# ---------------------------------------------------------------------------
# Página pública
# ---------------------------------------------------------------------------

def inicio(request):
    vacantes = (
        Vacante.objects.filter(activa=True)
        .select_related('empresa', 'categoria')
        .order_by('-destacada', '-fecha_publicacion')
    )

    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')

    if busqueda:
        vacantes = vacantes.filter(
            Q(titulo__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(empresa__nombre__icontains=busqueda)
        )
    if categoria_id:
        vacantes = vacantes.filter(categoria_id=categoria_id)

    # Paginamos para no mandar miles de vacantes de golpe
    pagina = Paginator(vacantes, 12).get_page(request.GET.get('page'))

    contexto = {
        'vacantes': pagina,
        'page_obj': pagina,
        'total': pagina.paginator.count,
        'categorias': Categoria.objects.all(),
        'busqueda': busqueda,
        'categoria_id': categoria_id,
    }
    return render(request, 'vacantes/inicio.html', contexto)


# ---------------------------------------------------------------------------
# CRUD de Vacantes (requiere sesión y permisos)
# ---------------------------------------------------------------------------

class VacantesDelUsuarioMixin:
    """OWASP A01: una empresa solo ve y modifica SUS vacantes.
    Si intenta abrir /vacantes/gestion/15/editar/ de otra empresa, recibe 404."""

    def get_queryset(self):
        qs = Vacante.objects.select_related('empresa', 'categoria')
        if es_admin(self.request.user):
            return qs
        return qs.filter(empresa__usuario=self.request.user)


class VacanteLista(LoginRequiredMixin, PermissionRequiredMixin, VacantesDelUsuarioMixin, ListView):
    permission_required = 'vacantes.view_vacante'
    template_name = 'vacantes/vacante_lista.html'
    context_object_name = 'vacantes'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().order_by('-fecha_publicacion')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(titulo__icontains=q) | Q(empresa__nombre__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '').strip()
        return ctx


class VacanteFormMixin:
    form_class = VacanteForm
    template_name = 'crud/formulario.html'
    success_url = reverse_lazy('vacantes:lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['es_admin'] = es_admin(self.request.user)
        return kwargs


class VacanteCrear(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                   VacanteFormMixin, CreateView):
    permission_required = 'vacantes.add_vacante'
    success_message = 'Vacante "%(titulo)s" creada.'
    extra_context = {'titulo_pagina': 'Nueva vacante'}

    def dispatch(self, request, *args, **kwargs):
        # Una cuenta de empresa necesita su perfil de Empresa para publicar
        if (request.user.has_perm('vacantes.add_vacante') and not es_admin(request.user)
                and not Empresa.objects.filter(usuario=request.user).exists()):
            messages.error(request, 'Tu usuario no tiene una empresa registrada.')
            return redirect('vacantes:lista')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not es_admin(self.request.user):
            form.instance.empresa = Empresa.objects.get(usuario=self.request.user)
        return super().form_valid(form)


class VacanteEditar(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                    VacantesDelUsuarioMixin, VacanteFormMixin, UpdateView):
    permission_required = 'vacantes.change_vacante'
    success_message = 'Vacante "%(titulo)s" actualizada.'
    extra_context = {'titulo_pagina': 'Editar vacante'}


class VacanteEliminar(LoginRequiredMixin, PermissionRequiredMixin, VacantesDelUsuarioMixin, DeleteView):
    permission_required = 'vacantes.delete_vacante'
    template_name = 'crud/confirmar_eliminar.html'
    success_url = reverse_lazy('vacantes:lista')
    extra_context = {'tipo': 'la vacante', 'cancelar': 'vacantes:lista'}

    def form_valid(self, form):
        messages.success(self.request, f'Vacante "{self.object.titulo}" eliminada.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# CRUD de Categorías (catálogo que alimenta la lista desplegable)
# ---------------------------------------------------------------------------

class CategoriaLista(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'vacantes.view_categoria'
    model = Categoria
    template_name = 'vacantes/categoria_lista.html'
    context_object_name = 'categorias'
    paginate_by = 20
    ordering = ['nombre']


class CategoriaCrear(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'vacantes.add_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'crud/formulario.html'
    success_url = reverse_lazy('vacantes:categoria_lista')
    success_message = 'Categoría "%(nombre)s" creada.'
    extra_context = {'titulo_pagina': 'Nueva categoría', 'cancelar': 'vacantes:categoria_lista'}


class CategoriaEditar(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'vacantes.change_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'crud/formulario.html'
    success_url = reverse_lazy('vacantes:categoria_lista')
    success_message = 'Categoría "%(nombre)s" actualizada.'
    extra_context = {'titulo_pagina': 'Editar categoría', 'cancelar': 'vacantes:categoria_lista'}


class CategoriaEliminar(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'vacantes.delete_categoria'
    model = Categoria
    template_name = 'crud/confirmar_eliminar.html'
    success_url = reverse_lazy('vacantes:categoria_lista')
    extra_context = {'tipo': 'la categoría', 'cancelar': 'vacantes:categoria_lista'}

    def form_valid(self, form):
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, 'No se puede eliminar: hay vacantes que usan esta categoría.')
            return redirect('vacantes:categoria_lista')
        messages.success(self.request, 'Categoría eliminada.')
        return respuesta
