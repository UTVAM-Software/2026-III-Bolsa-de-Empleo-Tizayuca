"""Inicio de sesión con correo electrónico (sin distinguir mayúsculas)."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


def username_desde_correo(correo):
    """El campo `username` de Django es interno: se deriva del correo y nadie lo escribe.
    Si ya estuviera ocupado se agrega un número."""
    User = get_user_model()
    base = correo.strip().lower()[:140]
    candidato, n = base, 1
    while User.objects.filter(username__iexact=candidato).exists():
        n += 1
        candidato = f'{base}-{n}'
    return candidato


class CorreoBackend(ModelBackend):
    """Entra con el correo. Las cuentas antiguas sin correo (por ejemplo el superusuario
    de `createsuperuser`) todavía pueden entrar con su nombre de usuario."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None
        username = username.strip()
        coincidencias = list(User._default_manager.filter(email__iexact=username)[:2])
        usuario = coincidencias[0] if len(coincidencias) == 1 else None
        if usuario is None:
            usuario = User._default_manager.filter(username=username).first()
        if usuario is None:
            User().set_password(password)      # mismo tiempo de respuesta: no revela qué cuentas existen
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
