import pytest
from rest_framework.test import APIClient
from core.tests.qa_audit_roles import ROLES
from core.tests.helpers import login


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def director_client(api_client):
    cfg = ROLES["director"]
    login(api_client, cfg["email"], cfg["password"])
    return api_client


@pytest.fixture
def secretaria_client(api_client):
    cfg = ROLES["secretaria"]
    login(api_client, cfg["email"], cfg["password"])
    return api_client


@pytest.fixture
def docente_client(api_client):
    cfg = ROLES["docente"]
    login(api_client, cfg["email"], cfg["password"])
    return api_client


@pytest.fixture
def regente_client(api_client):
    cfg = ROLES["regente"]
    login(api_client, cfg["email"], cfg["password"])
    return api_client


@pytest.fixture
def tutor_client(api_client):
    cfg = ROLES["tutor"]
    login(api_client, cfg["email"], cfg["password"])
    return api_client
