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


def create_user(**params):
    """Creates a test user"""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(email="test@email.com", password="testPassword")

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
        other_user = create_user(email="other@email.com", password="testPassword")

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

        recipe = Recipe.objects.get(id=res.data["id"])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Tests partial update of a recipe works correctly"""
        original_link = "www.mikerock.tech"
        recipe = create_recipe(
            title="Test Recipe 101", time_minutes=3, link=original_link, user=self.user
        )

        update_payload = {"title": "Mike Rocks Right?"}
        url = get_recipe_detail_url(recipe.id)
        res = self.client.patch(url, update_payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, update_payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full recipe update works correctly"""
        recipe = create_recipe(**TEST_RECIPE, user=self.user)

        payload = {
            "title": "Ewedu and Gbegiri with Amala",
            "time_minutes": 50,
            "link": "testlink.com",
            "price": Decimal("59.99"),
            "description": "Very delicious meal",
        }

        url = get_recipe_detail_url(id=recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

    def test_no_update_recipe_user(self):
        """Test that a recipe's user can't be updated"""
        new_user = create_user(email="tester@email.com", password="pass1234")
        recipe = create_recipe(user=self.user)

        url = get_recipe_detail_url(recipe.id)
        payload = {"user": new_user}

        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test that deleting a recipe is successful"""
        recipe = create_recipe(user=self.user)

        url = get_recipe_detail_url(id=recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        recipe_exists = Recipe.objects.filter(id=recipe.id).exists()

        self.assertFalse(recipe_exists)

    def test_delete_other_user_recipe_not_possible(self):
        """Test that a different user can't delete other user's recipe"""
        new_user = create_user(email="tester@email.com", password="pass1234")
        recipe = create_recipe(user=new_user)

        url = get_recipe_detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        recipeExists = Recipe.objects.filter(id=recipe.id)

        self.assertTrue(recipeExists)
