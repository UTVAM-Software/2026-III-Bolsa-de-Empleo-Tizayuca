from django import template
from django.db.models import Manager

register = template.Library()


@register.filter
def atributo(obj, ruta):
    """{{ obj|atributo:'empresa__nombre' }} -> obj.empresa.nombre
    Usa get_<campo>_display para campos con choices y muestra Sí/No en booleanos."""
    valor = obj
    for parte in ruta.split('__'):
        if valor is None:
            return ''
        display = getattr(valor, f'get_{parte}_display', None)
        valor = display() if display else getattr(valor, parte, '')
        if isinstance(valor, Manager):
            valor = ', '.join(str(x) for x in valor.all()) or '—'
        elif callable(valor):
            valor = valor()
    if valor is True:
        return 'Sí'
    if valor is False:
        return 'No'
    return '—' if valor in (None, '') else valor
