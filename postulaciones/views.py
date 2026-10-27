from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect

from candidatos.models import Candidato
from cuentas.mixins import CrearBase, EditarBase, EliminarBase, ListaBase, es_admin

from .forms import PostulacionForm
from .models import Postulacion


def rol_de(user):
    if es_admin(user):
        return 'admin'
    if Candidato.objects.filter(usuario=user).exists():
        return 'candidato'
    return 'empresa'


class PostulacionRutas:
    model = Postulacion
    titulo = 'Postulaciones'
    url_lista = 'postulaciones:lista'
    url_crear = 'postulaciones:crear'
    url_editar = 'postulaciones:editar'
    url_eliminar = 'postulaciones:eliminar'
    # El candidato ve las suyas; la empresa ve las que llegaron a SUS vacantes
    campos_propietario = ('candidato__usuario', 'vacante__empresa__usuario')


class FormPorRolMixin:
    """El formulario muestra campos distintos según el rol (admin, candidato o empresa)."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['rol'] = rol_de(self.request.user)
        return kwargs


class PostulacionLista(LoginRequiredMixin, PermissionRequiredMixin, PostulacionRutas, ListaBase):
    permission_required = 'postulaciones.view_postulacion'
    columnas = [('Candidato', 'candidato'), ('Vacante', 'vacante__titulo'),
                ('Empresa', 'vacante__empresa__nombre'), ('Fecha', 'fecha'), ('Estado', 'estado'),
                ('En proceso', 'esta_abierta')]
    buscar_en = ['vacante__titulo', 'candidato__usuario__first_name', 'candidato__usuario__username']

    def get_queryset(self):
        return (super().get_queryset()
                .select_related('candidato__usuario', 'vacante__empresa')
                .order_by('-fecha'))


class PostulacionCrear(LoginRequiredMixin, PermissionRequiredMixin, PostulacionRutas, FormPorRolMixin, CrearBase):
    permission_required = 'postulaciones.add_postulacion'
    form_class = PostulacionForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm(self.permission_required) and rol_de(request.user) == 'empresa':
            messages.error(request, 'Para postularte necesitas un perfil de candidato.')
            return redirect('candidatos:crear')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if rol_de(self.request.user) == 'candidato':
            candidato = Candidato.objects.get(usuario=self.request.user)
            if Postulacion.objects.filter(candidato=candidato, vacante=form.cleaned_data['vacante']).exists():
                form.add_error('vacante', 'Ya te postulaste a esta vacante.')
                return self.form_invalid(form)
            form.instance.candidato = candidato
        return super().form_valid(form)


class PostulacionEditar(LoginRequiredMixin, PermissionRequiredMixin, PostulacionRutas, FormPorRolMixin, EditarBase):
    permission_required = 'postulaciones.change_postulacion'
    form_class = PostulacionForm


class PostulacionEliminar(LoginRequiredMixin, PermissionRequiredMixin, PostulacionRutas, EliminarBase):
    permission_required = 'postulaciones.delete_postulacion'
