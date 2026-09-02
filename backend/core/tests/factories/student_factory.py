import factory

from core.models import Estudiantes


class EstudianteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Estudiantes

    nombres = factory.Faker("first_name", locale="es_ES")
    primer_apellido = factory.Faker("last_name", locale="es_ES")
    segundo_apellido = factory.Faker("last_name", locale="es_ES")
    rude = factory.Sequence(lambda n: f"RUDE{1000000 + n}")
    ci = factory.Sequence(lambda n: f"{1000000 + n}")
    estado = "activo"
