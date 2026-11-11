"""Validación y nombre seguro para los currículums subidos (OWASP A04/A08)."""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError


def ruta_cv(instance, filename):
    """Nombre aleatorio: el nombre original (que controla el usuario) nunca llega al disco."""
    return f'cv/{uuid.uuid4().hex}.pdf'


def validar_cv(archivo):
    if archivo.size > settings.CV_MAX_BYTES:
        raise ValidationError(f'El archivo pesa demasiado (máximo {settings.CV_MAX_BYTES // (1024 * 1024)} MB).')
    if not archivo.name.lower().endswith('.pdf'):
        raise ValidationError('Solo se aceptan archivos PDF.')
    cabecera = archivo.read(5)
    archivo.seek(0)
    if cabecera != b'%PDF-':
        raise ValidationError('El archivo no es un PDF válido.')
