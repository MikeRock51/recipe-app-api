"""Test module for the tags api"""

from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

from core.tests.test_models import create_user


TAGS_URL = reverse('recipe:tag-list')


def get_detail_url(tag_id):
    """Constructs and returns the tag detail url"""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_tag(**params):
    """Creates and returns a new tag"""
    return Tag.objects.create(**params)


class PublicTagTests(TestCase):
    """Tests unauthenticated tags API requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_to_retrieve_tags(self):
        """Tests that retrieving tags unauthenticated fails"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagTests(TestCase):
    """Tests authenticated tags API requests"""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Tests retrieving tags is successful"""
        create_tag(user=self.user, name='Swallow')
        create_tag(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_list_limited_to_auth_user(self):
        """Tests that the retrieved recipes is limited to the authenticated user"""
        new_user = create_user(email='test2@email.com', password='test12345')
        create_tag(user=new_user, name='Dessert')
        tag = create_tag(user=self.user, name='Swallow')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Tests updating a tag"""
        tag = create_tag(user=self.user, name="Delicious")
        tag_url = get_detail_url(tag.id)

        payload = {'name': 'Delicioso'}

        res = self.client.patch(tag_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = create_tag(user=self.user, name='Snacky')

        tag_url = get_detail_url(tag.id)

        res = self.client.delete(tag_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tag_exists = Tag.objects.filter(id=tag.id).exists()
        self.assertFalse(tag_exists)
