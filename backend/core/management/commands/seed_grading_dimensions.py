import argparse

from django.core.management.base import BaseCommand

from core.models import DimensionesEvaluacion


class Command(BaseCommand):
    help = "Seed the grading dimensions used by the grade grid"

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2026, help='Gestion (year) for the dimensions')

    def handle(self, *args, **options):
        gestion = options['gestion']
        dimensions = [
            {"nombre": "SER", "orden": 1},
            {"nombre": "SABER", "orden": 2},
            {"nombre": "HACER", "orden": 3},
            {"nombre": "AUTOEVALUACION", "orden": 4},
        ]

        created = 0
        updated = 0

        for data in dimensions:
            obj, was_created = DimensionesEvaluacion.objects.get_or_create(
                nombre=data["nombre"],
                gestion=gestion,
                defaults={"orden": data["orden"]},
            )
            if not was_created:
                obj.orden = data["orden"]
                obj.save()
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Dimensiones para gestion {gestion}: {created} creadas, {updated} actualizadas"
        ))
