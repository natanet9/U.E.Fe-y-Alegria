from django.core.management.base import BaseCommand

from core.services.license_service import LicenseService


class Command(BaseCommand):
    help = "Elimina de la base de datos las licencias con mas de 30 dias de antiguedad."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=LicenseService.RETENCION_DIAS,
            help="Dias de retencion antes de borrar licencias (por defecto 30).",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        eliminadas = LicenseService.limpiar_expiradas(dias=dias)
        self.stdout.write(
            self.style.SUCCESS(
                f"Se eliminaron {eliminadas} licencia(s) con mas de {dias} dias."
            )
        )
