import factory
from django.contrib.auth.hashers import make_password
from uuid import uuid4

from core.models import Roles, Usuarios


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuarios

    nombre = factory.Faker("first_name", locale="es_ES")
    primer_apellido = factory.Faker("last_name", locale="es_ES")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password_hash = factory.LazyFunction(lambda: make_password("TestPassword123!"))
    activo = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        rol = Roles.objects.first()
        if rol is None:
            rol = Roles.objects.create(nombre="director", descripcion="")
        kwargs["rol"] = rol
        return super()._create(model_class, *args, **kwargs)
