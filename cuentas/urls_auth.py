"""Login, logout y cambio de contraseña (en lugar de django.contrib.auth.urls completo)."""
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .seguridad import LoginProtegido

urlpatterns = [
    path('login/', LoginProtegido.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('contrasena/', auth_views.PasswordChangeView.as_view(
        template_name='registration/cambiar_contrasena.html',
        success_url=reverse_lazy('cuentas:panel')), name='password_change'),
]
