"""Recipe API Views module"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from core.models import Recipe
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset to manage the recipe API"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Overwrites the get method to only return auth user's recipes"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Returns the appropriate serializer class for a request"""
        if (self.action == 'list'):
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Creates a new recipe"""
        serializer.save(user=self.request.user)
