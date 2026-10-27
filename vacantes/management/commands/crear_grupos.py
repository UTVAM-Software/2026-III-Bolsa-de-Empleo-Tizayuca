"""Crea los 3 roles del sistema con sus permisos.

Uso:  python manage.py crear_grupos
Se puede correr las veces que quieras; no duplica nada.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# permiso -> codename de Django (app_label.accion_modelo)
ROLES = {
    # El municipio: control total de todo, incluidos usuarios y grupos
    'Administradores': '__todos__',

    # Empresas / negocios: registran su empresa, publican y administran SUS vacantes
    # y cambian el estado de las postulaciones que les llegan
    'Empresas': [
        'vacantes.view_vacante', 'vacantes.add_vacante',
        'vacantes.change_vacante', 'vacantes.delete_vacante',
        'vacantes.view_categoria',
        'postulaciones.view_postulacion', 'postulaciones.change_postulacion',
        'empresas.view_empresa', 'empresas.add_empresa', 'empresas.change_empresa',
    ],

    # Buscadores de empleo: llenan su perfil y experiencia y se postulan a vacantes
    'Candidatos': [
        'vacantes.view_categoria',
        'postulaciones.view_postulacion', 'postulaciones.add_postulacion',
        'candidatos.view_candidato', 'candidatos.add_candidato', 'candidatos.change_candidato',
        'candidatos.view_habilidad',
        'candidatos.view_experiencia', 'candidatos.add_experiencia',
        'candidatos.change_experiencia', 'candidatos.delete_experiencia',
    ],
}


class Command(BaseCommand):
    help = 'Crea los grupos Administradores, Empresas y Candidatos con sus permisos'

    def handle(self, *args, **options):
        for nombre, permisos in ROLES.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            if permisos == '__todos__':
                qs = Permission.objects.all()
            else:
                qs = Permission.objects.none()
                for p in permisos:
                    app, codename = p.split('.')
                    qs |= Permission.objects.filter(content_type__app_label=app, codename=codename)
            grupo.permissions.set(qs)
            self.stdout.write(self.style.SUCCESS(f'{nombre}: {qs.count()} permisos'))
