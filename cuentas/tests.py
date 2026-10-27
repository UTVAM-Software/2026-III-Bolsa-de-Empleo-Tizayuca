"""Pruebas del Entregable 03-B: login/logout, CRUD de todo y control de accesos (OWASP A01).

Correr con:  python manage.py test
"""
from datetime import date

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from candidatos.models import Candidato, Experiencia, Habilidad
from empresas.models import Empresa
from postulaciones.models import Postulacion
from vacantes.models import Categoria, Vacante


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('crear_grupos', verbosity=0)
        g = {n: Group.objects.get(name=n) for n in ('Administradores', 'Empresas', 'Candidatos')}

        def usuario(nombre, grupo):
            u = User.objects.create_user(nombre, password='Clave.Segura.123')
            u.groups.add(g[grupo])
            return u

        cls.admin = usuario('admin_muni', 'Administradores')
        cls.u_emp1, cls.u_emp2 = usuario('empresa1', 'Empresas'), usuario('empresa2', 'Empresas')
        cls.u_cand1, cls.u_cand2 = usuario('cand1', 'Candidatos'), usuario('cand2', 'Candidatos')
        cls.root = User.objects.create_superuser('root', password='Clave.Segura.123')

        datos = dict(tipo='local', giro='g', direccion='d', telefono='1')
        cls.emp1 = Empresa.objects.create(usuario=cls.u_emp1, nombre='Panadería Uno', **datos)
        cls.emp2 = Empresa.objects.create(usuario=cls.u_emp2, nombre='Barbería Dos', **datos)
        cls.cand1 = Candidato.objects.create(usuario=cls.u_cand1, colonia='Centro')
        cls.cand2 = Candidato.objects.create(usuario=cls.u_cand2, colonia='Huitzila')
        cls.hab = Habilidad.objects.create(nombre='Atención al cliente')
        cls.exp1 = Experiencia.objects.create(candidato=cls.cand1, puesto='Cajero', empresa='Oxxo',
                                              fecha_inicio=date(2023, 1, 1), fecha_fin=date(2024, 7, 1))
        cls.exp2 = Experiencia.objects.create(candidato=cls.cand2, puesto='Mesero', empresa='X',
                                              fecha_inicio=date(2022, 1, 1))
        cls.cat = Categoria.objects.create(nombre='Comercio')
        v = dict(categoria=cls.cat, descripcion='d', horario='h', ubicacion='u')
        cls.vac1 = Vacante.objects.create(empresa=cls.emp1, titulo='Panadero', sueldo_min=8000, sueldo_max=10000, **v)
        cls.vac2 = Vacante.objects.create(empresa=cls.emp2, titulo='Barbero', **v)
        cls.post1 = Postulacion.objects.create(candidato=cls.cand1, vacante=cls.vac1)
        cls.post2 = Postulacion.objects.create(candidato=cls.cand2, vacante=cls.vac2)

    def entrar(self, user):
        self.client.force_login(user)

    def todas_las_urls(self):
        pk = {
            'vacantes': self.vac1.pk, 'categoria': self.cat.pk, 'empresas': self.emp1.pk,
            'candidatos': self.cand1.pk, 'habilidad': self.hab.pk, 'experiencia': self.exp1.pk,
            'postulaciones': self.post1.pk, 'usuario': self.u_cand1.pk,
            'grupo': Group.objects.get(name='Candidatos').pk, 'permiso': Permission.objects.first().pk,
        }
        urls = [reverse('cuentas:panel')]
        modulos = [('vacantes', '', 'vacantes'), ('vacantes', 'categoria_', 'categoria'),
                   ('empresas', '', 'empresas'), ('candidatos', '', 'candidatos'),
                   ('candidatos', 'habilidad_', 'habilidad'), ('candidatos', 'experiencia_', 'experiencia'),
                   ('postulaciones', '', 'postulaciones'), ('cuentas', 'usuario_', 'usuario'),
                   ('cuentas', 'grupo_', 'grupo'), ('cuentas', 'permiso_', 'permiso')]
        for app, prefijo, clave in modulos:
            urls += [reverse(f'{app}:{prefijo}lista'), reverse(f'{app}:{prefijo}crear'),
                     reverse(f'{app}:{prefijo}editar', args=[pk[clave]]),
                     reverse(f'{app}:{prefijo}eliminar', args=[pk[clave]])]
        urls.append(reverse('cuentas:usuario_password', args=[self.u_cand1.pk]))
        return urls


class LoginLogoutTest(Base):
    def test_login_redirige_al_panel(self):
        r = self.client.post(reverse('login'), {'username': 'admin_muni', 'password': 'Clave.Segura.123'})
        self.assertRedirects(r, reverse('cuentas:panel'))

    def test_login_incorrecto(self):
        r = self.client.post(reverse('login'), {'username': 'admin_muni', 'password': 'mala'})
        self.assertContains(r, 'Usuario o contraseña incorrectos')

    def test_logout_regresa_al_inicio(self):
        self.entrar(self.admin)
        r = self.client.post(reverse('logout'))
        self.assertRedirects(r, reverse('vacantes:inicio'))
        self.assertRedirects(self.client.get(reverse('cuentas:panel')),
                             reverse('login') + '?next=' + reverse('cuentas:panel'))


class AccesoPorURLTest(Base):
    """Lo que revisará el profe: escribir la URL directo en el navegador."""

    def test_sin_sesion_todo_redirige_al_login(self):
        for url in self.todas_las_urls():
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertTrue(r.url.startswith(reverse('login')), url)

    def test_admin_abre_todas_las_pantallas(self):
        self.entrar(self.admin)
        for url in self.todas_las_urls():
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_candidato_no_entra_a_gestion_de_usuarios_ni_vacantes(self):
        self.entrar(self.u_cand1)
        prohibidas = [u for u in self.todas_las_urls()
                      if '/panel/usuarios' in u or '/panel/grupos' in u or '/panel/permisos' in u
                      or ('/gestion/' in u and u != reverse('vacantes:categoria_lista')) or '/empresas/' in u or '/habilidades/nueva' in u]
        self.assertTrue(prohibidas)
        for url in prohibidas:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_post_directo_tambien_se_bloquea(self):
        self.entrar(self.u_cand1)
        r = self.client.post(reverse('cuentas:usuario_eliminar', args=[self.u_cand2.pk]))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.u_cand2.pk).exists())


class RegistrosAjenosTest(Base):
    """OWASP A01 horizontal: cambiar el número de la URL no da acceso a datos de otro."""

    def test_empresa_no_ve_otra_empresa(self):
        self.entrar(self.u_emp1)
        r = self.client.get(reverse('empresas:lista'))
        self.assertContains(r, 'Panadería Uno')
        self.assertNotContains(r, 'Barbería Dos')
        self.assertEqual(self.client.get(reverse('empresas:editar', args=[self.emp2.pk])).status_code, 404)

    def test_candidato_no_ve_perfil_ni_experiencia_ajena(self):
        self.entrar(self.u_cand1)
        self.assertEqual(self.client.get(reverse('candidatos:editar', args=[self.cand2.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('candidatos:experiencia_editar', args=[self.exp2.pk])).status_code, 404)
        r = self.client.get(reverse('candidatos:experiencia_lista'))
        self.assertContains(r, 'Cajero')
        self.assertNotContains(r, 'Mesero')

    def test_postulaciones_solo_las_propias(self):
        self.entrar(self.u_emp1)   # empresa 1 solo ve las que llegaron a su vacante
        r = self.client.get(reverse('postulaciones:lista'))
        self.assertContains(r, 'Panadero')
        self.assertNotContains(r, 'Barbero')
        self.assertEqual(self.client.get(reverse('postulaciones:editar', args=[self.post2.pk])).status_code, 404)

    def test_empresa_cambia_estado_de_su_postulacion(self):
        self.entrar(self.u_emp1)
        self.client.post(reverse('postulaciones:editar', args=[self.post1.pk]), {'estado': 'entrevista'})
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.estado, 'entrevista')

    def test_candidato_se_postula_una_sola_vez(self):
        self.entrar(self.u_cand2)
        url = reverse('postulaciones:crear')
        r = self.client.post(url, {'vacante': self.vac1.pk, 'mensaje': 'Hola'})
        self.assertRedirects(r, reverse('postulaciones:lista'))
        self.assertTrue(Postulacion.objects.filter(candidato=self.cand2, vacante=self.vac1).exists())
        r = self.client.post(url, {'vacante': self.vac1.pk})
        self.assertContains(r, 'Ya te postulaste')

    def test_empresa_nueva_registra_solo_su_empresa(self):
        nuevo = User.objects.create_user('tortilleria')
        nuevo.groups.add(Group.objects.get(name='Empresas'))
        self.entrar(nuevo)
        self.client.post(reverse('empresas:crear'), {
            'nombre': 'Tortillería', 'tipo': 'local', 'giro': 'Alimentos',
            'direccion': 'Centro', 'telefono': '7791234567', 'verificada': 'on',
        })
        e = Empresa.objects.get(nombre='Tortillería')
        self.assertEqual(e.usuario, nuevo)
        self.assertFalse(e.verificada)   # no se puede auto-verificar


class GestionAuthTest(Base):
    """Usuarios, grupos y permisos desde la app (sin /admin)."""

    def test_crear_usuario_con_grupo_y_permiso(self):
        self.entrar(self.admin)
        permiso = Permission.objects.get(codename='view_vacante')
        r = self.client.post(reverse('cuentas:usuario_crear'), {
            'username': 'nuevo', 'first_name': 'Ana', 'last_name': 'López', 'email': 'ana@x.com',
            'password1': 'Clave.Segura.123', 'password2': 'Clave.Segura.123',
            'is_active': 'on', 'groups': [Group.objects.get(name='Empresas').pk],
            'user_permissions': [permiso.pk],
        })
        self.assertRedirects(r, reverse('cuentas:usuario_lista'))
        u = User.objects.get(username='nuevo')
        self.assertTrue(u.check_password('Clave.Segura.123'))
        self.assertTrue(u.groups.filter(name='Empresas').exists())
        self.assertIn(permiso, u.user_permissions.all())

    def test_admin_no_superusuario_no_puede_crear_superusuarios(self):
        self.entrar(self.admin)
        r = self.client.get(reverse('cuentas:usuario_crear'))
        self.assertNotIn('is_superuser', r.context['form'].fields)
        self.assertEqual(self.client.get(reverse('cuentas:usuario_editar', args=[self.root.pk])).status_code, 404)

    def test_cambiar_contrasena(self):
        self.entrar(self.admin)
        self.client.post(reverse('cuentas:usuario_password', args=[self.u_cand1.pk]),
                         {'new_password1': 'Otra.Clave.456', 'new_password2': 'Otra.Clave.456'})
        self.u_cand1.refresh_from_db()
        self.assertTrue(self.u_cand1.check_password('Otra.Clave.456'))

    def test_no_puede_borrarse_a_si_mismo(self):
        self.entrar(self.admin)
        self.client.post(reverse('cuentas:usuario_eliminar', args=[self.admin.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_crear_grupo_con_permisos(self):
        self.entrar(self.admin)
        perms = Permission.objects.filter(codename__in=['view_empresa', 'change_empresa'])
        self.client.post(reverse('cuentas:grupo_crear'), {'name': 'Verificadores', 'permissions': [p.pk for p in perms]})
        self.assertEqual(Group.objects.get(name='Verificadores').permissions.count(), 2)

    def test_crear_permiso_personalizado(self):
        self.entrar(self.admin)
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Empresa)
        self.client.post(reverse('cuentas:permiso_crear'),
                         {'name': 'Puede verificar empresa', 'content_type': ct.pk, 'codename': 'verificar_empresa'})
        self.assertTrue(Permission.objects.filter(codename='verificar_empresa').exists())


class PropiedadesModeloTest(Base):
    def test_propiedades(self):
        self.assertEqual(self.vac1.rango_sueldo, '$8,000 - $10,000')
        self.assertEqual(self.vac2.rango_sueldo, 'A convenir')
        self.assertEqual(self.exp1.duracion_meses, 18)
        self.assertTrue(self.exp2.es_actual)
        self.assertEqual(self.emp1.vacantes_activas, 1)
        self.assertTrue(self.post1.esta_abierta)
        self.assertEqual(self.vac1.get_absolute_url(), reverse('vacantes:editar', args=[self.vac1.pk]))
