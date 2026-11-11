"""Deja un ambiente local listo para usar con un solo comando.

Uso (después de `migrate`):
    python manage.py preparar_entorno
    python manage.py preparar_entorno --password OtraClave.123

Crea los grupos, las categorías, una cuenta de administrador (admin@example.com) y una cuenta
de consulta (profesor@example.com, grupo 'Solo lectura'). Se entra con el correo. Se puede correr varias veces sin duplicar.
"""
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from cuentas.backends import username_desde_correo
from vacantes.models import Categoria

CATEGORIAS = ['Industrial', 'Logística', 'Comercio', 'Servicios', 'Oficina', 'Alimentos']
# (correo, nombre, grupo, acceso a /admin, nombre de usuario que tenía antes)
CUENTAS = [
    ('admin@example.com', 'Administrador', 'Administradores', True, 'admin_muni'),
    ('profesor@example.com', 'Profesor', 'Solo lectura', False, 'profesor'),
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

        for correo, nombre, grupo, es_staff, antiguo in CUENTAS:
            usuario = (User.objects.filter(email__iexact=correo).first()
                       or User.objects.filter(username=antiguo, email='').first())
            creado = usuario is None
            if creado:
                usuario = User(username=username_desde_correo(correo))
                usuario.set_password(options['password'])
            usuario.email = correo
            usuario.first_name = usuario.first_name or nombre
            usuario.is_staff = es_staff
            usuario.save()
            usuario.groups.add(Group.objects.get(name=grupo))
            estado = 'creada' if creado else 'ya existía'
            self.stdout.write(self.style.SUCCESS(f'{correo} ({grupo}, matrícula {usuario.matricula}): {estado}'))
        self.stdout.write(f'Contraseña de las cuentas nuevas: {options["password"]}')
