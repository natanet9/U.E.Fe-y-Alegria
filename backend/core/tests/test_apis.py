import pytest
from core.tests.qa_audit_roles import ENDPOINTS
from core.tests.helpers import assert_ok, assert_unauthorized


class TestApiEndpoints:

    def test_dashboard_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["dashboard"])
        assert_unauthorized(r)

    def test_dashboard_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["dashboard"])
        assert_ok(r)

    def test_courses_detail_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["courses_detail"])
        assert_unauthorized(r)

    def test_courses_detail_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["courses_detail"])
        assert_ok(r)

    def test_courses_asignaciones_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["courses_asignaciones"])
        assert_unauthorized(r)

    def test_courses_asignaciones_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["courses_asignaciones"])
        assert_ok(r)

    def test_grades_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["grades"])
        assert_unauthorized(r)

    def test_grades_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["grades"])
        assert_ok(r)

    def test_activities_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["activities"])
        assert_unauthorized(r)

    def test_activities_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["activities"])
        assert_ok(r)

    def test_attendance_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["attendance"])
        assert_unauthorized(r)

    def test_attendance_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["attendance"])
        assert_ok(r)

    def test_reports_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["reports"])
        assert_unauthorized(r)

    def test_reports_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["reports"])
        assert_ok(r)

    def test_periods_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["periods"])
        assert_unauthorized(r)

    def test_periods_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["periods"])
        assert_ok(r)

    def test_enrollment_search_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["enrollment_search"])
        assert_unauthorized(r)

    def test_enrollment_search_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["enrollment_search"])
        assert_ok(r)

    def test_enrollment_catalogs_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["enrollment_catalogs"])
        assert_unauthorized(r)

    def test_enrollment_catalogs_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["enrollment_catalogs"])
        assert_ok(r)

    def test_students_list_requires_auth(self, api_client):
        r = api_client.get(ENDPOINTS["students_list"])
        assert_unauthorized(r)

    def test_students_list_authenticated(self, director_client):
        r = director_client.get(ENDPOINTS["students_list"])
        assert_ok(r)
