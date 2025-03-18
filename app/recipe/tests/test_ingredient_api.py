"""Ingredient testing module"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from decimal import Decimal

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

from recipe.tests.test_recipe_api import create_user, create_recipe

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_ingredient(**params):
    """Create and return a new ingredient"""
    return Ingredient.objects.create(**params)


def detail_url(ingredient_id):
    """Return ingredient detail URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


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

    def test_update_ingredient(self):
        """Test updating an ingredient"""
        ingredient = create_ingredient(user=self.user, name='Maggi')
        payload = {'name': 'Curry'}

        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        ingredient.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting an ingredient"""
        ingredient = create_ingredient(user=self.user, name='Maggi')
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.filter(id=ingredient.id).count(), 0)

    def test_filter_assigned(self):
        """Test filtering ingeridients by those assigned to a recipe"""
        ing1 = create_ingredient(user=self.user, name='Onion')
        ing2 = create_ingredient(user=self.user, name='Locust Beans')
        recipe = create_recipe(user=self.user, title='Noodles')
        params = {'assigned_only': 1}

        recipe.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, params)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_unique_filtered_ingredients(self):
        """Test filtered ingredients are unique"""
        ing1 = create_ingredient(user=self.user, name='Onion')
        create_ingredient(user=self.user, name='Ponmo')
        recipe1 = create_recipe(user=self.user, title='Noodles')
        recipe2 = create_recipe(user=self.user, title='Rice')

        recipe1.ingredients.add(ing1)
        recipe2.ingredients.add(ing1)
        params = {'assigned_only': 1}

        res = self.client.get(INGREDIENTS_URL, params)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)


