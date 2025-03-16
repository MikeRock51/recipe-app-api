"""Test module for the recipe API"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from decimal import Decimal

import tempfile
import os
from PIL import Image

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

from recipe.tests.test_tag_api import create_tag

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


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """Creates a test recipe with default or given params"""
    default = TEST_RECIPE.copy()  # Create a copy to avoid modifying the original
    default.update(params)

    # Remove tags if present since we can't directly assign them
    tags = default.pop('tags', [])
    recipe = Recipe.objects.create(user=user, **default)

    # Add tags if any were provided
    for tag in tags:
        tag_obj, _ = Tag.objects.get_or_create(user=user, **tag)
        recipe.tags.add(tag_obj)

    return recipe


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

    def test_create_recipe_recipe_with_new_tags(self):
        """Test creating a reciper with new tags (Nested Serializer)"""
        payload = TEST_RECIPE
        payload['tags'] = [
            {"name": "Lunch"},
            {"name": "Heavy"}
        ]

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes.first()

        self.assertEqual(recipe.tags.count(), 2)

        tags = recipe.tags.all()

        for tag in payload['tags']:
            self.assertIn(Tag.objects.get(name=tag['name'], user=self.user), tags)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag1 = create_tag(user=self.user, name="Breakfast")
        payload = TEST_RECIPE
        payload['tags'] = [
            {"name": tag1.name},
            {"name": "Heavy"}
        ]

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes.first()
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())

        for tag in payload['tags']:
            self.assertIn(Tag.objects.get(name=tag['name'], user=self.user), recipe.tags.all())

    def test_create_tag_on_update(self):
        """Test new tags gets created on update"""
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        url = get_recipe_detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name=payload['tags'][0]['name'])
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_replace_tags(self):
        """Test replacing the existing tags on a recipe during update"""
        breakfast_tag = create_tag(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(breakfast_tag)

        lunch_tag = create_tag(user=self.user, name="Lunch")
        payload = {'tags': [{'name': lunch_tag.name}]}
        url = get_recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        recipe_tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(lunch_tag, recipe_tags)
        self.assertNotIn(breakfast_tag, recipe_tags)

    def test_update_clear_tags(self):
        """Tests clearing all tags on a recipe during update"""
        breakfast_tag = create_tag(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(breakfast_tag)

        payload = {'tags': []}
        url = get_recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(breakfast_tag, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients creates the ingredients"""
        payload = TEST_RECIPE.copy()
        payload['ingredients'] = [{"name": "Yam"}, {"name": "Locust Beans"}]

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists())
            self.assertIn(Ingredient.objects.get(name=ingredient['name'], user=self.user), recipe.ingredients.all())

    def test_create_recipe_with_exisiting_ingredients(self):
        """Test creating recipe with existing ingredient assigns the ingredient"""
        ingredient1 = Ingredient.objects.create(name='Maggi', user=self.user)
        payload = TEST_RECIPE.copy()
        payload['ingredients'] = [{'name': 'Maggi'}, {'name': 'Salt'}]

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        ingredients = recipe.ingredients.all()

        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)

        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists())
            self.assertIn(Ingredient.objects.get(name=ingredient['name'], user=self.user), ingredients)

    def test_create_ingredient_on_update(self):
        """Test that new ingredients are created on update"""
        recipe = create_recipe(user=self.user)
        url = get_recipe_detail_url(recipe.id)
        payload = {'ingredients': [{'name': 'Gbegiri'}, {'name': 'Locust Beans'}]}

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 2)

        ingredients = recipe.ingredients.all()

        for ingredient in payload['ingredients']:
            self.assertIn(Ingredient.objects.get(name=ingredient['name'], user=self.user), ingredients)

    def test_assign_ingredients_on_update(self):
        """Test assigning existing ingredient to a recipe on update"""
        recipe = create_recipe(user=self.user)
        oilIngredient = Ingredient.objects.create(name='Palm Oil', user=self.user)
        recipe.ingredients.add(oilIngredient)

        beafIngredient = Ingredient.objects.create(name='Beaf', user=self.user)
        url = get_recipe_detail_url(recipe.id)
        payload = {'ingredients': [{'name': oilIngredient.name}, {'name': beafIngredient.name}]}

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            self.assertIn(Ingredient.objects.get(name=ingredient['name'], user=self.user), ingredients)

    def test_clear_recipe_ingredients(self):
        """Test clearing recipe ingredients"""
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(name='Pepper', user=self.user)
        recipe.ingredients.add(ingredient)

        url = get_recipe_detail_url(recipe.id)
        payload = {'ingredients': []}

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertNotIn(ingredient, recipe.ingredients.all())


class RecipeImageUploadTest(TestCase):
    """Test image upload for recipes"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="example@email.com", password="testPassword")
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)


    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test sucessful image upload for a recipe"""
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_invalid_image_upload(self):
        """Test uploading invalid image is handled"""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "InavlidImage.png"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
