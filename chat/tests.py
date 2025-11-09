from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from PIL import Image
import io

from .models import Story


# Create your tests here.


class StoryCreationTests(TestCase):
    def test_create_image_story(self):
        user = User.objects.create_user(username='story_test_user', password='pass12345')
        client = APIClient()
        self.assertTrue(client.login(username='story_test_user', password='pass12345'))

        buffer = io.BytesIO()
        Image.new('RGB', (640, 480), 'blue').save(buffer, format='JPEG')
        buffer.seek(0)
        upload = SimpleUploadedFile('story.jpg', buffer.getvalue(), content_type='image/jpeg')

        url = reverse('story-list')
        response = client.post(url, {'content_type': 'image', 'content': upload}, format='multipart')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Story.objects.count(), 1)
        story = Story.objects.first()
        self.assertEqual(story.user, user)
        self.assertEqual(story.content_type, 'image')
        self.assertTrue(story.content.name.endswith(('.jpg', '.jpeg', '.webp')))
