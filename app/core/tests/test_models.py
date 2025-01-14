"""App models testing module"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Model testing class"""

    def test_create_user_with_email_successful(self):
        """Tests that creating a new user with an email is successful"""
        email = 'test@email.com'
        password = 'Password1'

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
            user = get_user_model().objects.create_user(email, 'Password1')
            self.assertEqual(user.email, normalized_email)
