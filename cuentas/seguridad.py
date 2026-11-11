"""Protección contra fuerza bruta en el inicio de sesión (OWASP A07)."""
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm


def _ip(request):
    return request.META.get('REMOTE_ADDR', '')


def _clave(request, username):
    return f'login-fallos:{username.strip().lower()}:{_ip(request)}'


class FormLoginProtegido(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        # mismo mensaje para usuario inexistente y contraseña mala: no revela qué cuentas existen
        'invalid_login': 'Correo o contraseña incorrectos.',
        'bloqueado': 'Demasiados intentos fallidos. Intenta de nuevo en unos minutos.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Correo electrónico'

    def clean(self):
        username = self.data.get('username', '')
        if cache.get(_clave(self.request, username), 0) >= settings.LOGIN_MAX_INTENTOS:
            raise ValidationError(self.error_messages['bloqueado'], code='bloqueado')
        try:
            return super().clean()
        except ValidationError:
            clave = _clave(self.request, username)
            cache.set(clave, cache.get(clave, 0) + 1, settings.LOGIN_BLOQUEO_SEGUNDOS)
            raise


class LoginProtegido(LoginView):
    authentication_form = FormLoginProtegido

    def form_valid(self, form):
        cache.delete(_clave(self.request, form.cleaned_data['username']))
        return super().form_valid(form)
