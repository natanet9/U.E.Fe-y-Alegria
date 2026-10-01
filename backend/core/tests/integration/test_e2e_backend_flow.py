"""Tests de integración para flujos clave"""
import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient


@pytest.mark.django_db
class TestIntegrationFlows:

    def test_health_endpoint(self):
        client = APIClient()
        response = client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'

    def test_login_requires_fields(self):
        client = APIClient()
        response = client.post('/api/auth/login/', {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
