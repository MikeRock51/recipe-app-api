"""Test module for the recipe API"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from decimal import Decimal

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse("recipe:recipe-list")

TEST_RECIPE = {
    "title": "Pounded Yam and Efo Riro",
    "time_minutes": 45,
    "price": Decimal("99.99"),
    "description": "Delicious meal",
    "link": "https://www.youtube.com/watch?v=8hMuhCKyhuA",
}


def get_recipe_detail_url(id):
    """Creates and returns a recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[id])


def create_recipe(user, **params):
    """Creates a test recipe with default or given params"""
    default = TEST_RECIPE
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
        other_user = get_user_model().objects.create_user(
            email="other@email.com", password="testPassword"
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=self.user)
        url = get_recipe_detail_url(recipe.id)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test that recipe gets created successfully"""
        payload = TEST_RECIPE

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)
