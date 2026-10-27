from django.db import models
from django.urls import reverse


class Postulacion(models.Model):
    ESTADOS = [
        ('enviada', 'Enviada'),
        ('vista', 'Vista'),
        ('entrevista', 'Entrevista'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    candidato = models.ForeignKey('candidatos.Candidato', on_delete=models.CASCADE, related_name='postulaciones')
    vacante = models.ForeignKey('vacantes.Vacante', on_delete=models.CASCADE, related_name='postulaciones')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='enviada')
    mensaje = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'postulaciones'
        constraints = [
            models.UniqueConstraint(fields=['candidato', 'vacante'], name='postulacion_unica'),
        ]

    def __str__(self):
        return f'{self.candidato} -> {self.vacante}'

    def get_absolute_url(self):
        return reverse('postulaciones:editar', args=[self.pk])

    @property
    def esta_abierta(self):
        """Sigue en proceso mientras no haya sido aceptada o rechazada."""
        return self.estado not in ('aceptada', 'rechazada')

    def marcar_vista(self):
        if self.estado == 'enviada':
            self.estado = 'vista'
            self.save(update_fields=['estado'])
