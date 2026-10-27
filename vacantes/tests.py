from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from empresas.models import Empresa

from .models import Categoria, Vacante


class PermisosVacantesTest(TestCase):
    """Pruebas de control de acceso (OWASP A01) y de carga con 1000 registros."""

    @classmethod
    def setUpTestData(cls):
        call_command('crear_grupos', verbosity=0)
        cls.cat = Categoria.objects.create(nombre='Industrial')

        cls.admin = User.objects.create_user('admin_muni', password='x')
        cls.admin.groups.add(Group.objects.get(name='Administradores'))

        cls.u1 = User.objects.create_user('empresa1', password='x')
        cls.u1.groups.add(Group.objects.get(name='Empresas'))
        cls.e1 = Empresa.objects.create(usuario=cls.u1, nombre='Empresa Uno', tipo='local',
                                        giro='x', direccion='x', telefono='1')

        cls.u2 = User.objects.create_user('empresa2', password='x')
        cls.u2.groups.add(Group.objects.get(name='Empresas'))
        cls.e2 = Empresa.objects.create(usuario=cls.u2, nombre='Empresa Dos', tipo='local',
                                        giro='x', direccion='x', telefono='2')

        cls.cand = User.objects.create_user('candidato1', password='x')
        cls.cand.groups.add(Group.objects.get(name='Candidatos'))

        datos = dict(categoria=cls.cat, descripcion='d', horario='h', ubicacion='u')
        cls.v1 = Vacante.objects.create(empresa=cls.e1, titulo='Vacante de Uno', **datos)
        cls.v2 = Vacante.objects.create(empresa=cls.e2, titulo='Vacante de Dos', **datos)

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(reverse('vacantes:lista'))
        self.assertRedirects(r, reverse('login') + '?next=' + reverse('vacantes:lista'))

    def test_candidato_no_puede_gestionar(self):
        self.client.login(username='candidato1', password='x')
        self.assertEqual(self.client.get(reverse('vacantes:lista')).status_code, 403)
        self.assertEqual(self.client.get(reverse('vacantes:crear')).status_code, 403)

    def test_empresa_solo_ve_sus_vacantes(self):
        self.client.login(username='empresa1', password='x')
        r = self.client.get(reverse('vacantes:lista'))
        self.assertContains(r, 'Vacante de Uno')
        self.assertNotContains(r, 'Vacante de Dos')

    def test_empresa_no_edita_ni_borra_ajenas(self):
        self.client.login(username='empresa1', password='x')
        self.assertEqual(self.client.get(reverse('vacantes:editar', args=[self.v2.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('vacantes:eliminar', args=[self.v2.pk])).status_code, 404)
        self.assertTrue(Vacante.objects.filter(pk=self.v2.pk).exists())

    def test_empresa_crea_y_queda_como_suya(self):
        self.client.login(username='empresa1', password='x')
        r = self.client.post(reverse('vacantes:crear'), {
            'categoria': self.cat.pk, 'titulo': 'Nueva', 'descripcion': 'd',
            'horario': 'h', 'ubicacion': 'u', 'activa': 'on',
        })
        self.assertRedirects(r, reverse('vacantes:lista'))
        self.assertEqual(Vacante.objects.get(titulo='Nueva').empresa, self.e1)

    def test_admin_ve_y_borra_todo(self):
        self.client.login(username='admin_muni', password='x')
        r = self.client.get(reverse('vacantes:lista'))
        self.assertContains(r, 'Vacante de Uno')
        self.assertContains(r, 'Vacante de Dos')
        self.client.post(reverse('vacantes:eliminar', args=[self.v2.pk]))
        self.assertFalse(Vacante.objects.filter(pk=self.v2.pk).exists())

    def test_carga_1000_vacantes_paginadas_y_filtradas(self):
        call_command('poblar_vacantes', cantidad=1000, verbosity=0)
        self.assertEqual(Vacante.objects.filter(titulo__startswith='Prueba ').count(), 1000)

        # La página pública solo manda 12, no 1000
        r = self.client.get(reverse('vacantes:inicio'))
        self.assertEqual(len(r.context['vacantes']), 12)

        # El filtro por texto funciona sobre los 1000 registros
        r = self.client.get(reverse('vacantes:inicio'), {'q': 'Prueba 0010 -'})
        self.assertEqual(r.context['total'], 1)

        # Consultas acotadas aunque haya 1000 registros (sin N+1)
        self.client.login(username='admin_muni', password='x')
        with self.assertNumQueries(7):
            self.client.get(reverse('vacantes:lista'))
