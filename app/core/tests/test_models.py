"""App models testing module"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Model testing class"""

    def test_create_user_with_email_successful(self):
        """Tests that creating a new user with an email is successful"""
        email = 'test@email.com'
        password = 'Password123'

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Tests the email for a new user is normalized"""
        sample_emails = [
            ['test@Example.com', 'test@example.com'],
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['test3@Example.COM', 'test3@example.com'],
            ['TEST4@EXAMPLE.COM', 'TEST4@example.com']
        ]

        for email, normalized_email in sample_emails:
            user = get_user_model().objects.create_user(email, 'Password123')
            self.assertEqual(user.email, normalized_email)

    def test_new_user_without_email_raise_value_error(self):
        """Tests that creating a user without an email raises ValeError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'Password123')

    def test_create_super_user(self):
        """Tests that super users are created correctly"""
        user = get_user_model().objects.create_superuser('super@email.com', 'Password123')

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
