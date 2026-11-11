from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cuentas'
    verbose_name = 'Cuentas, grupos y permisos'

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save

        from .models import Matricula, generar_numero

        def asignar_matricula(sender, instance, created, raw=False, **kwargs):
            if created and not raw:
                Matricula.objects.get_or_create(usuario=instance, defaults={'numero': generar_numero(instance)})

        post_save.connect(asignar_matricula, sender=get_user_model(),
                          dispatch_uid='cuentas.asignar_matricula')
