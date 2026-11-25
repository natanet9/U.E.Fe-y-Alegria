from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import assistant_chat_view


def test_tutor_cannot_use_staff_assistant():
    request = APIRequestFactory().post(
        "/api/assistant/chat/",
        {"question": "¿Cómo consulto el portal?"},
        format="json",
    )
    usuario = SimpleNamespace(rol=SimpleNamespace(nombre="tutor"))

    with patch("core.views._get_usuario", return_value=usuario):
        response = assistant_chat_view(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_user_cannot_use_staff_assistant():
    request = APIRequestFactory().post(
        "/api/assistant/chat/",
        {"question": "¿Cómo consulto el portal?"},
        format="json",
    )

    with patch("core.views._get_usuario", return_value=None):
        response = assistant_chat_view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_student_can_use_staff_assistant():
    request = APIRequestFactory().post(
        "/api/assistant/chat/",
        {"question": "¿Cómo consulto el portal?"},
        format="json",
    )
    usuario = SimpleNamespace(rol=SimpleNamespace(nombre="estudiante"))

    with patch("core.views._get_usuario", return_value=usuario):
        with patch("core.views._assistant_context", return_value={"rol": "estudiante"}):
            with patch("core.views.urlopen") as mock_urlopen:
                mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                    b'{"answer":"Consulta las secciones de tu panel.","source":"local"}'
                )
                response = assistant_chat_view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["answer"] == "Consulta las secciones de tu panel."
