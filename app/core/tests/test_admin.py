"""Django admin modification tests module"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Admin site tests class"""

    def setUp(self):
        """Set up method"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@email.com',
            password='Password123'
        )
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email='user@email.com',
            password='Password123',
        )

    def test_users_listed(self):
        """Tests that users are listed on user page"""
        url = reverse('admin:core_user_changelist')
        print(url)
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.admin_user.email)
