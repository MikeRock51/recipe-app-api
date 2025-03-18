from django.contrib.auth import get_user_model

from core.models import Recipe, Tag, Ingredient
from decimal import Decimal

TEST_RECIPE = {
    "title": "Pounded Yam and Efo Riro",
    "time_minutes": 45,
    "price": Decimal("99.99"),
    "description": "Delicious meal",
    "link": "https://www.youtube.com/watch?v=8hMuhCKyhuA",
}

TEST_USER = {
    "email": "test@email.com",
    "password": "TestPassword123"
}


def create_recipe(user, **params):
    """Creates a test recipe with default or given params"""
    default = TEST_RECIPE.copy()  # Create a copy to avoid modifying the original
    default.update(params)

    # Remove tags and ingredients if present since we can't directly assign them
    tags = default.pop('tags', [])
    ingredients = default.pop('ingredients', [])
    recipe = Recipe.objects.create(user=user, **default)

    # Add tags if any were provided
    for tag in tags:
        tag_obj, _ = Tag.objects.get_or_create(user=user, **tag)
        recipe.tags.add(tag_obj)

    # Add ingredients if any were provided
    for ingredient in ingredients:
        ingredient_obj, _ = Ingredient.objects.get_or_create(user=user, **ingredient)
        recipe.ingredients.add(ingredient_obj)

    return recipe

def create_tag(**params):
    """Creates and returns a new tag"""
    return Tag.objects.create(**params)

def create_ingredient(**params):
    """Create and return a new ingredient"""
    return Ingredient.objects.create(**params)

def create_user(**params):
    """Creates a test user"""
    default = TEST_USER.copy()
    default.update(params)

    return get_user_model().objects.create_user(**default)