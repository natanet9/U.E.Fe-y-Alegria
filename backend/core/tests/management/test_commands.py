from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class TestSeedCommand(TestCase):
    def test_seed_runs_without_errors(self):
        out = StringIO()
        err = StringIO()
        try:
            call_command('seed', stdout=out, stderr=err)
            output = out.getvalue().lower()
            self.assertTrue(
                'ok' in output
                or 'éxito' in output
                or 'exito' in output
                or 'finalizado' in output
                or len(output) > 0
            )
        except Exception as e:
            self.fail(f"seed raised an exception: {e}")
