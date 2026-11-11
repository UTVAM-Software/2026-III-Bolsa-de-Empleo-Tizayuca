from django.conf import settings
from django.db import models
from django.utils import timezone


def generar_numero(usuario):
    """TZY-2026-00012: año de alta + id del usuario. El id es único y consecutivo,
    así que dos personas nunca comparten matrícula."""
    anio = (usuario.date_joined or timezone.now()).year
    return f'TZY-{anio}-{usuario.pk:05d}'


class Matricula(models.Model):
    """Identificador de control de cada cuenta. Se genera sola al crear el usuario."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='matricula')
    numero = models.CharField(max_length=20, unique=True, editable=False)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'matrículas'

    def __str__(self):
        return self.numero
