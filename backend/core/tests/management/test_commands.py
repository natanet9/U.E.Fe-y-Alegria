from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class TestSeedDataCommand(TestCase):
    def test_seed_data_runs_without_errors(self):
        out = StringIO()
        err = StringIO()
        try:
            call_command('seed_data', stdout=out, stderr=err)
            output = out.getvalue().lower()
            self.assertTrue(
                'ok' in output
                or 'exitosamente' in output
                or 'creado' in output
                or len(output) > 0
            )
        except Exception as e:
            self.fail(f"seed_data raised an exception: {e}")

    def test_seed_grading_dimensions_runs_without_errors(self):
        out = StringIO()
        err = StringIO()
        try:
            call_command('seed_grading_dimensions', stdout=out, stderr=err)
            output = out.getvalue().lower()
            self.assertTrue(
                'ok' in output
                or 'exitosamente' in output
                or 'creado' in output
                or len(output) > 0
            )
        except Exception as e:
            self.fail(f"seed_grading_dimensions raised an exception: {e}")
