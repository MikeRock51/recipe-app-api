"""Tests the health check API endpoint"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTest(TestCase):
    """Tests the health check API endpoint"""

    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        """Tests the health check API endpoint"""
        url = reverse('core:health-check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
