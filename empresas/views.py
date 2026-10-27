from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from cuentas.mixins import AsignarUsuarioMixin, CrearBase, EditarBase, EliminarBase, ListaBase, es_admin

from .forms import EmpresaForm
from .models import Empresa


class EmpresaRutas:
    model = Empresa
    titulo = 'Empresas'
    url_lista = 'empresas:lista'
    url_crear = 'empresas:crear'
    url_editar = 'empresas:editar'
    url_eliminar = 'empresas:eliminar'
    campos_propietario = ('usuario',)   # una empresa solo se ve y modifica a sí misma


class EmpresaLista(LoginRequiredMixin, PermissionRequiredMixin, EmpresaRutas, ListaBase):
    permission_required = 'empresas.view_empresa'
    columnas = [('Nombre', 'nombre'), ('Tipo', 'tipo'), ('Giro', 'giro'),
                ('Teléfono', 'telefono'), ('Vacantes activas', 'vacantes_activas'),
                ('Estado', 'estado_verificacion')]
    buscar_en = ['nombre', 'giro']
    ordering = ['nombre']


class EmpresaCrear(LoginRequiredMixin, PermissionRequiredMixin, EmpresaRutas, AsignarUsuarioMixin, CrearBase):
    permission_required = 'empresas.add_empresa'
    form_class = EmpresaForm


class EmpresaEditar(LoginRequiredMixin, PermissionRequiredMixin, EmpresaRutas, EditarBase):
    permission_required = 'empresas.change_empresa'
    form_class = EmpresaForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['es_admin'] = es_admin(self.request.user)
        return kwargs


class EmpresaEliminar(LoginRequiredMixin, PermissionRequiredMixin, EmpresaRutas, EliminarBase):
    permission_required = 'empresas.delete_empresa'
