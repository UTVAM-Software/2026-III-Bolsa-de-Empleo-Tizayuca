from django.db import models
from django.urls import reverse
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nombre

    @property
    def vacantes_activas(self):
        return self.vacantes.filter(activa=True).count()


class Vacante(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE, related_name='vacantes')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='vacantes')
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    requisitos = models.TextField(blank=True)
    sueldo_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sueldo_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    horario = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)
    destacada = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.titulo} - {self.empresa}'

    def get_absolute_url(self):
        return reverse('vacantes:editar', args=[self.pk])

    @property
    def rango_sueldo(self):
        """Texto listo para mostrar: '$8,000 - $11,000', 'Desde $8,000' o 'A convenir'."""
        if self.sueldo_min and self.sueldo_max:
            return f'${self.sueldo_min:,.0f} - ${self.sueldo_max:,.0f}'
        if self.sueldo_min:
            return f'Desde ${self.sueldo_min:,.0f}'
        if self.sueldo_max:
            return f'Hasta ${self.sueldo_max:,.0f}'
        return 'A convenir'

    @property
    def dias_publicada(self):
        return (timezone.now() - self.fecha_publicacion).days

    @property
    def total_postulaciones(self):
        return self.postulaciones.count()

    def desactivar(self):
        """Cierra la vacante sin borrarla (conserva sus postulaciones)."""
        self.activa = False
        self.save(update_fields=['activa'])
