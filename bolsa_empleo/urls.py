"""
URL configuration for bolsa_empleo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('cuentas.urls_auth')),
    path('panel/', include('cuentas.urls')),
    path('empresas/', include('empresas.urls')),
    path('candidatos/', include('candidatos.urls')),
    path('postulaciones/', include('postulaciones.urls')),
    path('', include('vacantes.urls')),
]

handler403 = 'cuentas.views.error_403'
handler404 = 'cuentas.views.error_404'
handler500 = 'cuentas.views.error_500'
