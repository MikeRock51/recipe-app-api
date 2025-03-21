"""Module to test the user API"""

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")

TEST_USER_DETAILS = {
    "email": "test@email.com",
    "password": "testpass",
    "name": "Test name",
}


def create_user(**params):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = TEST_USER_DETAILS

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", res.data)

        user = get_user_model().objects.get(
            email=payload["email"]
        )  # Fix the get method call
        self.assertTrue(user.check_password(payload["password"]))

    def test_user_email_exists_fails(self):
        """Test creating a user that already exists fails"""
        payload = TEST_USER_DETAILS

        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertNotEqual(res.status_code, status.HTTP_201_CREATED)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters"""
        payload = TEST_USER_DETAILS
        payload["password"] = "pass"

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()

        self.assertFalse(user_exists)

    def test_user_successful_login_creates_token(self):
        """Test that a token is created for the user"""
        create_user(**TEST_USER_DETAILS)

        payload = {
            "email": TEST_USER_DETAILS["email"],
            "password": TEST_USER_DETAILS["password"]
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_bad_credentials(self):
        """Tests that user login with bad credentials does not create token"""
        create_user(**TEST_USER_DETAILS)

        payload = {
            "email": TEST_USER_DETAILS["email"],
            "password": "badpass"
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user does not exist"""
        payload = {
            "email": TEST_USER_DETAILS["email"],
            "password": TEST_USER_DETAILS["password"]
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test that token is not created if password is blank"""
        create_user(**TEST_USER_DETAILS)

        payload = {
            "email": TEST_USER_DETAILS["email"],
            "password": ""
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access_of_user_data(self):
        """Test that unauthorized access to user data is not allowed"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITest(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(**TEST_USER_DETAILS)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            "name": self.user.name,
            "email": self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me url"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {
            "name": "new name",
            "password": "newpassword123"
        }

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
