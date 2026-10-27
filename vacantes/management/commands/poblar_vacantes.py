"""Prueba de carga: crea muchas vacantes de prueba (por defecto 1000).

Uso:
    python manage.py poblar_vacantes              # 1000 vacantes
    python manage.py poblar_vacantes --cantidad 5000
    python manage.py poblar_vacantes --borrar     # elimina las de prueba

Las vacantes de prueba se identifican porque su título empieza con "Prueba ".
"""
import random
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from empresas.models import Empresa
from vacantes.models import Categoria, Vacante

CATEGORIAS = ['Industrial', 'Logística', 'Comercio', 'Servicios', 'Oficina', 'Alimentos']
PUESTOS = ['Operador de producción', 'Almacenista', 'Montacarguista', 'Cajero', 'Barbero',
           'Panadero', 'Auxiliar administrativo', 'Chofer repartidor', 'Mesero', 'Supervisor']
HORARIOS = ['Lunes a viernes 8:00 - 17:00', 'Turno nocturno 22:00 - 6:00', 'Rotativo', 'Medio tiempo']
COLONIAS = ['Centro', 'Huitzila', 'El Carmen', 'Parque Industrial Tizayuca', 'Haciendas de Tizayuca']


class Command(BaseCommand):
    help = 'Crea vacantes de prueba para probar el sistema con muchos registros'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=1000)
        parser.add_argument('--borrar', action='store_true', help='Borra las vacantes de prueba')

    def handle(self, *args, **options):
        if options['borrar']:
            borradas, _ = Vacante.objects.filter(titulo__startswith='Prueba ').delete()
            self.stdout.write(self.style.WARNING(f'Se borraron {borradas} registros de prueba'))
            return

        # Catálogo de categorías
        categorias = [Categoria.objects.get_or_create(nombre=n)[0] for n in CATEGORIAS]

        # Una empresa de prueba (necesita un usuario dueño)
        usuario, _ = User.objects.get_or_create(username='empresa_prueba')
        empresa, _ = Empresa.objects.get_or_create(
            usuario=usuario,
            defaults={'nombre': 'Empresa de Prueba S.A.', 'tipo': 'industrial', 'giro': 'Manufactura',
                      'direccion': 'Parque Industrial Tizayuca', 'telefono': '7790000000'},
        )

        n = options['cantidad']
        inicio = time.perf_counter()
        nuevas = []
        for x in range(n):
            minimo = random.randrange(7000, 15000, 500)
            nuevas.append(Vacante(
                empresa=empresa,
                categoria=random.choice(categorias),
                titulo=f'Prueba {x:04} - {random.choice(PUESTOS)}',
                descripcion=f'Descripción de la vacante de prueba {x:05}',
                sueldo_min=minimo,
                sueldo_max=minimo + 3000,
                horario=random.choice(HORARIOS),
                ubicacion=random.choice(COLONIAS),
            ))
        # bulk_create inserta todo en pocas consultas en vez de 1000 consultas sueltas
        Vacante.objects.bulk_create(nuevas, batch_size=500)
        segundos = time.perf_counter() - inicio

        self.stdout.write(self.style.SUCCESS(f'Se crearon {n} vacantes en {segundos:.2f} s'))
        self.stdout.write(f'Total de vacantes en la base: {Vacante.objects.count()}')
