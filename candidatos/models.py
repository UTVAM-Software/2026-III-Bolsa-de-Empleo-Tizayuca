from datetime import date

from django.conf import settings
from django.db import models
from django.urls import reverse


class Habilidad(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name_plural = 'habilidades'

    def __str__(self):
        return self.nombre


class Candidato(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=15, blank=True)
    colonia = models.CharField(max_length=100, blank=True)
    escolaridad = models.CharField(max_length=100, blank=True)
    resumen = models.TextField(blank=True)
    cv = models.FileField(upload_to='cv/', blank=True)
    habilidades = models.ManyToManyField(Habilidad, blank=True)

    def __str__(self):
        return self.nombre_completo

    def get_absolute_url(self):
        return reverse('candidatos:editar', args=[self.pk])

    @property
    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def anios_experiencia(self):
        """Suma la duración de todas sus experiencias laborales (en años, 1 decimal)."""
        meses = sum(e.duracion_meses for e in self.experiencias.all())
        return round(meses / 12, 1)


class Experiencia(models.Model):
    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE, related_name='experiencias')
    puesto = models.CharField(max_length=100)
    empresa = models.CharField(max_length=150)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.puesto} en {self.empresa}'

    def get_absolute_url(self):
        return reverse('candidatos:experiencia_editar', args=[self.pk])

    @property
    def es_actual(self):
        return self.fecha_fin is None

    @property
    def duracion_meses(self):
        fin = self.fecha_fin or date.today()
        return max(0, (fin.year - self.fecha_inicio.year) * 12 + fin.month - self.fecha_inicio.month)