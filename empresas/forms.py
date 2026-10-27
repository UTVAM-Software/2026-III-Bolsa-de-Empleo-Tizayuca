from django import forms

from .models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['usuario', 'nombre', 'tipo', 'giro', 'descripcion', 'direccion', 'telefono', 'verificada']
        labels = {'descripcion': 'Descripción', 'direccion': 'Dirección', 'telefono': 'Teléfono'}
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, es_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo el municipio asigna el usuario dueño y verifica empresas
        if not es_admin:
            del self.fields['usuario']
            del self.fields['verificada']
