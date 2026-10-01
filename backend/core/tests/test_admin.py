"""Pruebas del panel de administracion (/admin/).

Verifican que todas las tablas de la app `core` estan registradas y que las
paginas de listado, alta y edicion responden correctamente, ademas del cifrado
de la contrasena de `Usuarios` al crear o editar desde el panel.
"""
from datetime import date

import pytest
from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.test import Client, RequestFactory
from django.urls import reverse

from core.models import (
    Actividades,
    Areas,
    ConfiguracionEscuela,
    Cursos,
    DimensionesEvaluacion,
    DocenteAsignacion,
    Docentes,
    Estudiantes,
    Grados,
    Niveles,
    Paralelos,
    Periodos,
    Roles,
    Tutores,
    Usuarios,
)


def modelos_core():
    """Modelos declarados en la app `core`."""
    return list(apps.get_app_config('core').get_models())


@pytest.fixture
def superusuario(db):
    """Superusuario de Django (autenticacion propia del admin)."""
    return get_user_model().objects.create_superuser(
        username='admin_panel',
        email='admin_panel@test.com',
        password='Admin.12345',
    )


@pytest.fixture
def cliente_admin(superusuario):
    client = Client()
    client.force_login(superusuario)
    return client


@pytest.mark.django_db
class TestRegistroDeTablas:

    def test_todos_los_modelos_de_core_estan_registrados(self):
        registrados = {m for m in admin.site._registry if m._meta.app_label == 'core'}
        faltantes = sorted(m.__name__ for m in modelos_core() if m not in registrados)
        assert faltantes == []
        assert len(registrados) == len(modelos_core())

    def test_el_panel_esta_montado_en_admin(self):
        assert reverse('admin:index') == '/admin/'


@pytest.mark.django_db
class TestPaginasDelPanel:

    def test_login_anonimo_responde_200(self):
        assert Client().get(reverse('admin:login')).status_code == 200

    def test_index_responde_200(self, cliente_admin):
        assert cliente_admin.get(reverse('admin:index')).status_code == 200

    def test_listado_de_cada_tabla(self, cliente_admin):
        for model in modelos_core():
            url = reverse(f'admin:core_{model._meta.model_name}_changelist')
            response = cliente_admin.get(url)
            assert response.status_code == 200, f'{model.__name__}: {url} -> {response.status_code}'

    def test_alta_de_cada_tabla(self, cliente_admin, superusuario):
        request = RequestFactory().get('/admin/')
        request.user = superusuario
        for model in modelos_core():
            adm = admin.site._registry[model]
            esperado = 200 if adm.has_add_permission(request) else 403
            url = reverse(f'admin:core_{model._meta.model_name}_add')
            response = cliente_admin.get(url)
            assert response.status_code == esperado, f'{model.__name__}: {url} -> {response.status_code}'

    def test_edicion_de_las_tablas_con_inlines(self, cliente_admin):
        nivel = Niveles.objects.create(nombre='Primaria')
        grado = Grados.objects.create(nivel=nivel, nombre='1ro de primaria', numero=1)
        paralelo = Paralelos.objects.create(nombre='A')
        curso = Cursos.objects.create(grado=grado, paralelo=paralelo, gestion=2026)
        area = Areas.objects.create(nombre='Matematica')
        periodo = Periodos.objects.create(nombre='1er Trimestre', numero=1, gestion=2026,
                                          fecha_inicio=date(2026, 2, 1), fecha_fin=date(2026, 4, 30))
        dimension = DimensionesEvaluacion.objects.create(nombre='Saber', orden=1, gestion=2026)
        rol = Roles.objects.create(nombre='docente')
        usuario = Usuarios.objects.create(email='doc@test.com', rol=rol,
                                          password_hash=make_password('123456'))
        docente = Docentes.objects.create(usuario=usuario)
        asignacion = DocenteAsignacion.objects.create(docente=docente, curso=curso, area=area, gestion=2026)
        Actividades.objects.create(docente_asignacion=asignacion, periodo=periodo, dimension=dimension,
                                   nombre='Practica 1', puntaje_maximo=50, fecha_actividad=date(2026, 3, 1))
        Estudiantes.objects.create(rude='RUDE-1', ci='CI-1', primer_apellido='Perez', nombres='Ana')
        Tutores.objects.create(ci='CI-TUT-1', primer_apellido='Perez', nombres='Juan')

        for model in (Estudiantes, Tutores, Periodos, DocenteAsignacion, Actividades):
            obj = model.objects.order_by('-pk').first()
            url = reverse(f'admin:core_{model._meta.model_name}_change', args=[obj.pk])
            response = cliente_admin.get(url)
            assert response.status_code == 200, f'{model.__name__}: {url} -> {response.status_code}'

    def test_configuracion_escuela_no_admite_mas_de_un_registro(self, cliente_admin):
        ConfiguracionEscuela.objects.create(nombre='U.E. Test')
        url = reverse('admin:core_configuracionescuela_add')
        assert cliente_admin.get(url).status_code == 403


@pytest.mark.django_db
class TestUsuariosDesdeElPanel:

    CAMPOS_BASE = {
        'ci': '1234567',
        'nombre': 'Ana',
        'primer_apellido': 'Perez',
        'segundo_apellido': '',
        'activo': 'on',
        'otp_metodo': 'email',
        'intentos_otp_fallidos': 0,
    }

    def test_alta_cifra_la_contrasena_en_password_hash(self, cliente_admin):
        rol = Roles.objects.create(nombre='secretaria')
        response = cliente_admin.post(
            reverse('admin:core_usuarios_add'),
            {**self.CAMPOS_BASE, 'email': 'ana@test.com', 'rol': rol.pk, 'password_plano': 'Secreta123'},
        )
        assert response.status_code == 302
        usuario = Usuarios.objects.get(email='ana@test.com')
        assert usuario.password_hash.startswith('pbkdf2_')
        assert check_password('Secreta123', usuario.password_hash)

    def test_alta_sin_contrasena_no_guarda_el_usuario(self, cliente_admin):
        rol = Roles.objects.create(nombre='secretaria')
        response = cliente_admin.post(
            reverse('admin:core_usuarios_add'),
            {**self.CAMPOS_BASE, 'email': 'ana2@test.com', 'rol': rol.pk, 'password_plano': ''},
        )
        assert response.status_code == 200
        assert not Usuarios.objects.filter(email='ana2@test.com').exists()

    def test_contrasena_corta_es_rechazada(self, cliente_admin):
        rol = Roles.objects.create(nombre='secretaria')
        response = cliente_admin.post(
            reverse('admin:core_usuarios_add'),
            {**self.CAMPOS_BASE, 'email': 'ana3@test.com', 'rol': rol.pk, 'password_plano': 'corta'},
        )
        assert response.status_code == 200
        assert not Usuarios.objects.filter(email='ana3@test.com').exists()

    def test_edicion_sin_contrasena_conserva_el_hash(self, cliente_admin):
        rol = Roles.objects.create(nombre='secretaria')
        usuario = Usuarios.objects.create(email='sec@test.com', rol=rol,
                                          password_hash=make_password('Original123'))
        hash_previo = usuario.password_hash
        response = cliente_admin.post(
            reverse('admin:core_usuarios_change', args=[usuario.pk]),
            {**self.CAMPOS_BASE, 'nombre': 'Editado', 'email': 'sec@test.com',
             'rol': rol.pk, 'password_plano': ''},
        )
        assert response.status_code == 302
        usuario.refresh_from_db()
        assert usuario.nombre == 'Editado'
        assert usuario.password_hash == hash_previo