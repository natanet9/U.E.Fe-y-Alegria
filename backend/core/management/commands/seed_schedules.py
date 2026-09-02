from django.core.management.base import BaseCommand
from core.models import Horarios, DocenteAsignacion


class Command(BaseCommand):
    help = 'Seed simple Horarios for existing DocenteAsignacion entries'

    def handle(self, *args, **options):
        asignaciones = DocenteAsignacion.objects.filter(activo=True)
        created = 0
        for i, da in enumerate(asignaciones, start=1):
            # assign day 1-5 and times based on index to avoid collisions
            dia = (i % 5) + 1
            hora_inicio = '08:00:00'
            hora_fin = '09:00:00'
            obj, was_created = Horarios.objects.update_or_create(
                docente_asignacion=da,
                dia_semana=dia,
                hora_inicio=hora_inicio,
                defaults={
                    'hora_fin': hora_fin,
                    'aula': f'Aula {i%10 + 1}',
                    'activo': True,
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Horarios creados/actualizados: {created}'))
