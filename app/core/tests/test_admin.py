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

    def test_edit_user_page(self):
        """Tests that the edit user page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_add_user_page(self):
        """Tests that the add user page is working"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
