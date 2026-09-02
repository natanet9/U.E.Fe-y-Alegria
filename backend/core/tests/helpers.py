import pytest
from rest_framework import status
from rest_framework.test import APIClient


def login(client, email, password):
    r = client.post("/api/auth/login/", {"email": email, "password": password}, format="json")
    if r.status_code == 200:
        token = r.data.get("access")
        if token:
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            return True
    return False


def assert_ok(response):
    assert response.status_code == status.HTTP_200_OK, (
        f"Expected 200, got {response.status_code}: {response.data}"
    )


def assert_created(response):
    assert response.status_code == status.HTTP_201_CREATED, (
        f"Expected 201, got {response.status_code}: {response.data}"
    )


def assert_forbidden(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, (
        f"Expected 403, got {response.status_code}: {response.data}"
    )


def assert_unauthorized(response):
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        f"Expected 401, got {response.status_code}: {response.data}"
    )


def assert_bad_request(response):
    assert response.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Expected 400, got {response.status_code}: {response.data}"
    )


def endpoint(path):
    return path if path.startswith("/api/") else f"/api/{path.lstrip('/')}"


def get_ids_from_dashboard(client):
    r = client.get("/api/dashboard/")
    if r.status_code != 200:
        return None, None
    data = r.data
    asig_id = None
    try:
        cursos = data.get("cursos", []) or data.get("asignaciones", [])
        if cursos:
            asig_id = cursos[0].get("id") or cursos[0].get("docente_asignacion_id")
    except (IndexError, TypeError, AttributeError):
        pass
    return asig_id, None
