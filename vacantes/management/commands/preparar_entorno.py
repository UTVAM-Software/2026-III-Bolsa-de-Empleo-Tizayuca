"""Deja un ambiente local listo para usar con un solo comando.

Uso (después de `migrate`):
    python manage.py preparar_entorno
    python manage.py preparar_entorno --password OtraClave.123

Crea los grupos, las categorías, una cuenta de administrador (`admin_muni`) y una cuenta
de consulta (`profesor`, grupo 'Solo lectura'). Se puede correr varias veces sin duplicar.
"""
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from vacantes.models import Categoria

CATEGORIAS = ['Industrial', 'Logística', 'Comercio', 'Servicios', 'Oficina', 'Alimentos']
CUENTAS = [
    ('admin_muni', 'Administradores', True),
    ('profesor', 'Solo lectura', False),
]


class Command(BaseCommand):
    help = 'Crea grupos, categorías y las cuentas admin_muni y profesor para un ambiente local'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='Tizayuca.2026',
                            help='Contraseña de las cuentas creadas (solo para ambientes locales)')

    def handle(self, *args, **options):
        call_command('crear_grupos', stdout=self.stdout)
        for nombre in CATEGORIAS:
            Categoria.objects.get_or_create(nombre=nombre)

        for username, grupo, es_staff in CUENTAS:
            usuario, creado = User.objects.get_or_create(username=username)
            if creado:
                usuario.set_password(options['password'])
            usuario.is_staff = es_staff
            usuario.save()
            usuario.groups.add(Group.objects.get(name=grupo))
            estado = 'creada' if creado else 'ya existía'
            self.stdout.write(self.style.SUCCESS(f'{username} ({grupo}): {estado}'))
        self.stdout.write(f'Contraseña de las cuentas nuevas: {options["password"]}')
