"""Ingredient testing module"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

from recipe.tests.test_recipe_api import create_user

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_ingredient(**params):
    """Create and return a new ingredient"""
    return Ingredient.objects.create(**params)


class PublicIngredientAPITest(TestCase):
    """Test unathenticated ingredients requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required for access"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    """Test authenticated ingredients requests"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@email.com', password='Password1234')

        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients"""
        create_ingredient(user=self.user, name='Curry')
        create_ingredient(user=self.user, name='Maggi')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_auth_user(self):
        """Test user can only get ingredients they authored"""
        new_user = create_user(email='tempuser@email.com', password='Password1234')
        create_ingredient(user=new_user, name='Maggi')
        ingredient = create_ingredient(user=self.user, name='Thyme')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)
