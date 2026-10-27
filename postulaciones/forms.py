from django import forms

from vacantes.models import Vacante

from .models import Postulacion


class PostulacionForm(forms.ModelForm):
    """Los campos cambian según el rol:
    - administrador: todo
    - candidato: elige vacante y escribe mensaje (no puede cambiar su estado)
    - empresa: solo cambia el estado (vista, entrevista, aceptada, rechazada)
    """

    class Meta:
        model = Postulacion
        fields = ['candidato', 'vacante', 'estado', 'mensaje']
        widgets = {'mensaje': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, rol='admin', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vacante'].queryset = Vacante.objects.filter(activa=True).select_related('empresa')
        if rol == 'candidato':
            for campo in ('candidato', 'estado'):
                del self.fields[campo]
            if self.instance.pk:          # una vez enviada, ya no puede cambiar de vacante
                del self.fields['vacante']
        elif rol == 'empresa':
            for campo in ('candidato', 'vacante', 'mensaje'):
                del self.fields[campo]
