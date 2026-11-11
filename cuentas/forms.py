from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command


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


class RegistroForm(UserCreationForm):
    """Registro público: la persona elige si busca empleo o si es una empresa.
    Nunca se puede elegir un rol de administración desde aquí."""
    TIPOS = [('candidato', 'Busco empleo'), ('empresa', 'Soy una empresa o negocio')]

    tipo = forms.ChoiceField(choices=TIPOS, label='Tipo de cuenta', widget=forms.RadioSelect,
                             initial='candidato')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {'username': 'Usuario', 'first_name': 'Nombre(s)', 'last_name': 'Apellidos',
                  'email': 'Correo electrónico'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        nombre = 'Candidatos' if self.cleaned_data['tipo'] == 'candidato' else 'Empresas'
        if not Group.objects.filter(name=nombre).exists():
            call_command('crear_grupos', verbosity=0)
        grupo = Group.objects.get(name=nombre)
        usuario.groups.add(grupo)
        return usuario
