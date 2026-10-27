from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect

from cuentas.mixins import AsignarUsuarioMixin, CrearBase, EditarBase, EliminarBase, ListaBase, es_admin

from .forms import CandidatoForm, ExperienciaForm, HabilidadForm
from .models import Candidato, Experiencia, Habilidad


class ConRolMixin:
    """Le pasa al formulario si quien lo usa es administrador."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['es_admin'] = es_admin(self.request.user)
        return kwargs


# ---------------------------------------------------------------------------
# Candidatos
# ---------------------------------------------------------------------------

class CandidatoRutas:
    model = Candidato
    titulo = 'Candidatos'
    url_lista = 'candidatos:lista'
    url_crear = 'candidatos:crear'
    url_editar = 'candidatos:editar'
    url_eliminar = 'candidatos:eliminar'
    campos_propietario = ('usuario',)   # un candidato solo ve su propio perfil


class CandidatoLista(LoginRequiredMixin, PermissionRequiredMixin, CandidatoRutas, ListaBase):
    permission_required = 'candidatos.view_candidato'
    columnas = [('Nombre', 'nombre_completo'), ('Teléfono', 'telefono'), ('Colonia', 'colonia'),
                ('Escolaridad', 'escolaridad'), ('Años de experiencia', 'anios_experiencia'),
                ('Habilidades', 'habilidades')]
    buscar_en = ['usuario__first_name', 'usuario__last_name', 'usuario__username', 'colonia']

    def get_queryset(self):
        return super().get_queryset().select_related('usuario').prefetch_related('habilidades', 'experiencias')


class CandidatoCrear(LoginRequiredMixin, PermissionRequiredMixin, CandidatoRutas, AsignarUsuarioMixin, CrearBase):
    permission_required = 'candidatos.add_candidato'
    form_class = CandidatoForm


class CandidatoEditar(LoginRequiredMixin, PermissionRequiredMixin, CandidatoRutas, ConRolMixin, EditarBase):
    permission_required = 'candidatos.change_candidato'
    form_class = CandidatoForm


class CandidatoEliminar(LoginRequiredMixin, PermissionRequiredMixin, CandidatoRutas, EliminarBase):
    permission_required = 'candidatos.delete_candidato'


# ---------------------------------------------------------------------------
# Habilidades (catálogo que aparece como lista de casillas en el perfil)
# ---------------------------------------------------------------------------

class HabilidadRutas:
    model = Habilidad
    titulo = 'Habilidades'
    url_lista = 'candidatos:habilidad_lista'
    url_crear = 'candidatos:habilidad_crear'
    url_editar = 'candidatos:habilidad_editar'
    url_eliminar = 'candidatos:habilidad_eliminar'


class HabilidadLista(LoginRequiredMixin, PermissionRequiredMixin, HabilidadRutas, ListaBase):
    permission_required = 'candidatos.view_habilidad'
    columnas = [('Nombre', 'nombre')]
    buscar_en = ['nombre']
    ordering = ['nombre']


class HabilidadCrear(LoginRequiredMixin, PermissionRequiredMixin, HabilidadRutas, CrearBase):
    permission_required = 'candidatos.add_habilidad'
    form_class = HabilidadForm


class HabilidadEditar(LoginRequiredMixin, PermissionRequiredMixin, HabilidadRutas, EditarBase):
    permission_required = 'candidatos.change_habilidad'
    form_class = HabilidadForm


class HabilidadEliminar(LoginRequiredMixin, PermissionRequiredMixin, HabilidadRutas, EliminarBase):
    permission_required = 'candidatos.delete_habilidad'


# ---------------------------------------------------------------------------
# Experiencia laboral
# ---------------------------------------------------------------------------

class ExperienciaRutas:
    model = Experiencia
    titulo = 'Experiencia laboral'
    url_lista = 'candidatos:experiencia_lista'
    url_crear = 'candidatos:experiencia_crear'
    url_editar = 'candidatos:experiencia_editar'
    url_eliminar = 'candidatos:experiencia_eliminar'
    campos_propietario = ('candidato__usuario',)


class ExperienciaLista(LoginRequiredMixin, PermissionRequiredMixin, ExperienciaRutas, ListaBase):
    permission_required = 'candidatos.view_experiencia'
    columnas = [('Candidato', 'candidato'), ('Puesto', 'puesto'), ('Empresa', 'empresa'),
                ('Inicio', 'fecha_inicio'), ('Fin', 'fecha_fin'), ('Meses', 'duracion_meses')]
    buscar_en = ['puesto', 'empresa']

    def get_queryset(self):
        return super().get_queryset().select_related('candidato__usuario')


class ExperienciaCrear(LoginRequiredMixin, PermissionRequiredMixin, ExperienciaRutas, ConRolMixin, CrearBase):
    permission_required = 'candidatos.add_experiencia'
    form_class = ExperienciaForm

    def dispatch(self, request, *args, **kwargs):
        if (request.user.has_perm(self.permission_required) and not es_admin(request.user)
                and not Candidato.objects.filter(usuario=request.user).exists()):
            messages.error(request, 'Primero registra tu perfil de candidato.')
            return redirect('candidatos:crear')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not es_admin(self.request.user):
            form.instance.candidato = Candidato.objects.get(usuario=self.request.user)
        return super().form_valid(form)


class ExperienciaEditar(LoginRequiredMixin, PermissionRequiredMixin, ExperienciaRutas, ConRolMixin, EditarBase):
    permission_required = 'candidatos.change_experiencia'
    form_class = ExperienciaForm


class ExperienciaEliminar(LoginRequiredMixin, PermissionRequiredMixin, ExperienciaRutas, EliminarBase):
    permission_required = 'candidatos.delete_experiencia'
