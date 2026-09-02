import json
import os
import pytest

from core import tracing


@pytest.fixture(scope="session", autouse=True)
def collect_traces():
    """Collect traces during the test session and write a summary JSON on finish."""
    # clear any prior traces
    tracing.get_trace_records(clear=True)
    yield
    records = tracing.get_trace_records(clear=True)
    try:
        # derive backend folder relative to this conftest file
        here = os.path.dirname(__file__)
        backend_dir = os.path.abspath(os.path.join(here, os.pardir))
        out_path = os.path.join(backend_dir, "test_traces_summary.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"traces": records}, f, indent=2)
        # emit a short summary to pytest stdout
        total = len(records)
        avg = (sum(r.get("elapsed_ms", 0) for r in records) / total) if total else 0
        print(f"\n[TRACE SUMMARY] records={total} avg_elapsed_ms={avg:.2f} -> {out_path}")
    except Exception as e:
        print(f"[TRACE SUMMARY] could not write traces: {e}")
from types import SimpleNamespace
from uuid import uuid4

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Cliente API REST para pruebas"""
    return APIClient()


@pytest.fixture
def admin_user():
    """Crea un usuario administrador para pruebas"""
    return SimpleNamespace(
        id=uuid4(),
        nombre="Admin",
        apellido="Test",
        email="admin@test.com",
        password_hash="pbkdf2_sha256$dummy",
        ci="CI00000001",
        telefono="",
        activo=True,
    )


@pytest.fixture
def teacher_user():
    """Crea un usuario docente para pruebas"""
    return SimpleNamespace(
        id=uuid4(),
        nombre="Docente",
        apellido="Test",
        email="teacher@test.com",
        password_hash="pbkdf2_sha256$dummy",
        ci="CI00000002",
        telefono="",
        activo=True,
    )


@pytest.fixture
def student_user():
    """Crea un usuario estudiante para pruebas"""
    return SimpleNamespace(
        id=uuid4(),
        nombre="Estudiante",
        apellido="Test",
        email="student@test.com",
        password_hash="pbkdf2_sha256$dummy",
        ci="CI00000003",
        telefono="",
        activo=True,
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Cliente API autenticado como admin"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def teacher_client(api_client, teacher_user):
    """Cliente API autenticado como docente"""
    api_client.force_authenticate(user=teacher_user)
    return api_client


@pytest.fixture
def student_client(api_client, student_user):
    """Cliente API autenticado como estudiante"""
    api_client.force_authenticate(user=student_user)
    return api_client


class DummyCursor:
    """Minimal fake DB cursor that behaves like a real cursor for tests.

    Provides `__enter__`/`__exit__`, `execute`, `fetchone`, `fetchmany` and
    `fetchall` so Django ORM iteration and raw SQL helpers don't hang when
    tests patch `connection.cursor`.
    """
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return (0,)

    def fetchmany(self, size=None):
        return []

    def fetchall(self):
        return []


@pytest.fixture
def dummy_cursor():
    """Fixture that returns a `DummyCursor` instance for tests to use."""
    return DummyCursor()
