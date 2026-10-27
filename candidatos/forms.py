from django import forms

from .models import Candidato, Experiencia, Habilidad


class HabilidadForm(forms.ModelForm):
    class Meta:
        model = Habilidad
        fields = ['nombre']


class CandidatoForm(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = ['usuario', 'telefono', 'colonia', 'escolaridad', 'resumen', 'cv', 'habilidades']
        labels = {'telefono': 'Teléfono', 'cv': 'Currículum (PDF)'}
        widgets = {
            'resumen': forms.Textarea(attrs={'rows': 3}),
            'habilidades': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, es_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not es_admin:
            del self.fields['usuario']


class ExperienciaForm(forms.ModelForm):
    class Meta:
        model = Experiencia
        fields = ['candidato', 'puesto', 'empresa', 'fecha_inicio', 'fecha_fin']
        labels = {'fecha_fin': 'Fecha de fin (vacío si es tu trabajo actual)'}
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, es_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not es_admin:
            del self.fields['candidato']

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior al inicio.')
        return datos
