from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import (
    enrollment_search_view,
    enrollment_new_view,
    enrollment_re_enroll_view,
    enrollment_catalogs_view,
    search_tutor_by_ci_view,
)


class TestEnrollmentViews:

    usuario = SimpleNamespace(
        id=1, activo=True, nombre_completo="Sec", email="sec@test.com",
        rol=SimpleNamespace(nombre="secretaria"),
    )

    def test_search_view_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/search/")
        response = enrollment_search_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_view_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/search/", {"rude": "R001"})
        request.usuario = self.usuario
        payload = {"id": 1, "nombres": "Juan"}
        with patch("core.views.EnrollmentService.search_existing_student", return_value=payload):
            response = enrollment_search_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"encontrado": True, "estudiante": payload}

    def test_search_view_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/search/", {"rude": "R999"})
        request.usuario = self.usuario
        with patch("core.views.EnrollmentService.search_existing_student", return_value=None):
            response = enrollment_search_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"encontrado": False}

    def test_enroll_new_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/new/", {}, format="json")
        response = enrollment_new_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_enroll_new_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/new/", {"rude": "R001"}, format="json")
        request.usuario = self.usuario
        payload = {"id": 1, "rude": "R001"}
        with patch("core.views.EnrollmentService.enroll_new_student", return_value=payload):
            response = enrollment_new_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == payload

    def test_enroll_new_permision(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/new/", {}, format="json")
        request.usuario = self.usuario
        with patch("core.views.EnrollmentService.enroll_new_student", side_effect=PermissionError("sin permisos")):
            response = enrollment_new_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_enroll_new_validation(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/new/", {}, format="json")
        request.usuario = self.usuario
        with patch("core.views.EnrollmentService.enroll_new_student", side_effect=ValueError("invalido")):
            response = enrollment_new_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_re_enroll_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.post("/api/enrollment/re-enroll/", {}, format="json")
        response = enrollment_re_enroll_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_re_enroll_success(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/enrollment/re-enroll/",
            {"rude": "R001", "curso_id": 1, "gestion": "2025"},
            format="json",
        )
        request.usuario = self.usuario
        payload = {"id": 1, "rude": "R001"}
        with patch("core.views.EnrollmentService.re_enroll_existing_student", return_value=payload):
            response = enrollment_re_enroll_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload

    def test_re_enroll_validation(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/enrollment/re-enroll/",
            {"rude": "R001", "curso_id": 1},
            format="json",
        )
        request.usuario = self.usuario
        with patch("core.views.EnrollmentService.re_enroll_existing_student", side_effect=ValueError("invalido")):
            response = enrollment_re_enroll_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_enroll_catalogs_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/catalogs/")
        response = enrollment_catalogs_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_enroll_catalogs_success(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/catalogs/")
        request.usuario = self.usuario
        payload = {"gestiones": [2025], "cursos": []}
        with patch("core.views.EnrollmentService.get_enrollment_catalogs", return_value=payload):
            response = enrollment_catalogs_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload

    def test_enroll_catalogs_permision(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/catalogs/")
        request.usuario = self.usuario
        with patch("core.views.EnrollmentService.get_enrollment_catalogs", side_effect=PermissionError("sin permisos")):
            response = enrollment_catalogs_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_tutor_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/search-tutor/")
        response = search_tutor_by_ci_view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_tutor_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/search-tutor/", {"ci": "123456"})
        request.usuario = self.usuario
        payload = {"id": 1, "nombre": "Tutor"}
        with patch("core.views.EnrollmentService.search_tutor_by_ci", return_value=payload):
            response = search_tutor_by_ci_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"encontrado": True, "tutor": payload}

    def test_search_tutor_not_found(self):
        factory = APIRequestFactory()
        request = factory.get("/api/enrollment/search-tutor/", {"ci": "999999"})
        request.usuario = self.usuario
        with patch("core.views.EnrollmentService.search_tutor_by_ci", return_value=None):
            response = search_tutor_by_ci_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"encontrado": False}
