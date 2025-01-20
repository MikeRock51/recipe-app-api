"""Test module for the recipe API"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from decimal import Decimal

from recipe.serializers import RecipeSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def create_recipe(user, **params):
    """Creates a test recipe with default or given params"""
    default = {
        "title": "Pounded Yam and Efo Riro",
        "time_minutes": 45,
        "price": Decimal("99.99"),
        "description": "Delicious meal",
        "link": "https://www.youtube.com/watch?v=8hMuhCKyhuA",
    }

    default.update(params)

    return Recipe.objects.create(user=user, **default)


class PublicRecipeAPITest(TestCase):
    """Test unauthenticated requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to make a request"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    """Test authenticated requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email="test@email.com", password="testPassword"
        )

        self.client.force_authenticate(self.user)

    def test_retrive_recipe(self):
        """Test that authenticated users can retrieve a list of recipes"""
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_current_user(self):
        """Tests that recipes list only retrieves for current user"""
        other_user = get_user_model().objects.create(
            {"email": "other@email.com", "password": "testPassword"}
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
