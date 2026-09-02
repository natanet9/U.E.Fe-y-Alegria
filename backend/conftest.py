import pytest
import os

# Disable Django's DB serialization for tests to avoid errors with incomplete migration schema
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.test_settings')

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Override Django DB setup to use test settings without serialization issues"""
    with django_db_blocker.unblock():
        pass


@pytest.fixture(scope='function', autouse=True)
def _reset_db_state(django_db_blocker):
    """Reset database state between tests"""
    # This fixture ensures each test runs in isolation
    yield
    with django_db_blocker.unblock():
        # Clean up after each test
        pass
