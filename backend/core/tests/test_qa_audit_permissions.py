import pytest
from core.tests.qa_audit_roles import ENDPOINTS, PERMISSIONS, ROLES
from core.tests.helpers import login, assert_ok, assert_forbidden


class TestPermissionMatrix:

    @pytest.fixture(params=list(ROLES.keys()))
    def role(self, request):
        return request.param

    def test_role_can_access_allowed_endpoints(self, role):
        from rest_framework.test import APIClient
        client = APIClient()
        cfg = ROLES[role]
        login(client, cfg["email"], cfg["password"])
        allowed = PERMISSIONS.get(role, [])
        for ep_name in allowed:
            r = client.get(ENDPOINTS[ep_name])
            assert_ok(r)

    def test_role_denied_restricted_endpoints(self, role):
        from rest_framework.test import APIClient
        client = APIClient()
        cfg = ROLES[role]
        login(client, cfg["email"], cfg["password"])
        allowed = set(PERMISSIONS.get(role, []))
        all_eps = set(ENDPOINTS.keys())
        restricted = all_eps - allowed
        for ep_name in restricted:
            r = client.get(ENDPOINTS[ep_name])
            assert_forbidden(r)
