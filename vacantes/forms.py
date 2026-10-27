from django import forms

from .models import Categoria, Vacante


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']


class VacanteForm(forms.ModelForm):
    class Meta:
        model = Vacante
        fields = [
            'empresa', 'categoria', 'titulo', 'descripcion', 'requisitos',
            'sueldo_min', 'sueldo_max', 'horario', 'ubicacion', 'destacada', 'activa',
        ]
        labels = {
            'titulo': 'Título del puesto',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'sueldo_min': 'Sueldo mínimo',
            'sueldo_max': 'Sueldo máximo',
            'ubicacion': 'Ubicación',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'requisitos': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, es_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Una empresa no elige empresa (se asigna sola) ni puede destacar su vacante:
        # eso solo lo hace el municipio (administrador).
        if not es_admin:
            del self.fields['empresa']
            del self.fields['destacada']

    def clean(self):
        datos = super().clean()
        minimo, maximo = datos.get('sueldo_min'), datos.get('sueldo_max')
        if minimo and maximo and minimo > maximo:
            self.add_error('sueldo_max', 'El sueldo máximo no puede ser menor que el mínimo.')
        return datos
