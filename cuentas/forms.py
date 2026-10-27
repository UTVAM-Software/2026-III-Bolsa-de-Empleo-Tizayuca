from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, Permission, User


def permisos_qs():
    return Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'codename')


class SelectorPermisos(forms.ModelMultipleChoiceField):
    """Muestra cada permiso como 'vacantes | Vacante | Can add vacante'."""

    def label_from_instance(self, p):
        return f'{p.content_type.app_label} | {p.content_type.name} | {p.name}'


CAMPOS_USUARIO = ['username', 'first_name', 'last_name', 'email',
                  'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']
ETIQUETAS_USUARIO = {
    'is_active': 'Activo', 'is_staff': 'Puede entrar a /admin',
    'is_superuser': 'Superusuario', 'groups': 'Grupos (roles)',
}


class RolUsuarioMixin:
    """Solo un superusuario puede crear o promover a otro superusuario."""

    def __init__(self, *args, puede_superusuario=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].widget = forms.CheckboxSelectMultiple()
        self.fields['groups'].queryset = Group.objects.order_by('name')
        self.fields['user_permissions'] = SelectorPermisos(
            queryset=permisos_qs(), required=False, label='Permisos directos',
            help_text='Además de los que ya le dan sus grupos. Ctrl/Cmd + clic para elegir varios.',
            widget=forms.SelectMultiple(attrs={'size': 12}))
        if not puede_superusuario:
            del self.fields['is_superuser']


class UsuarioCrearForm(RolUsuarioMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = CAMPOS_USUARIO
        labels = ETIQUETAS_USUARIO


class UsuarioEditarForm(RolUsuarioMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = CAMPOS_USUARIO
        labels = ETIQUETAS_USUARIO


class GrupoForm(forms.ModelForm):
    permissions = SelectorPermisos(
        queryset=permisos_qs(), required=False, label='Permisos del grupo',
        help_text='Ctrl/Cmd + clic para elegir varios.',
        widget=forms.SelectMultiple(attrs={'size': 16}))

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {'name': 'Nombre del grupo'}


class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['name', 'content_type', 'codename']
        labels = {'name': 'Descripción', 'content_type': 'Modelo', 'codename': 'Código (ej. verificar_empresa)'}
