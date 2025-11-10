from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from unittest import mock
from PIL import Image
import io
import json

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator

from .models import Story, ChatRoom, CallSession, BlockedUser, CallParticipant
from .call_consumers import CallSignalingConsumer


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


@override_settings(SECURE_SSL_REDIRECT=False)
class CallSessionValidationTests(TestCase):
    def setUp(self):
        self.initiator = User.objects.create_user(username='caller', password='pass12345')
        self.participant = User.objects.create_user(username='friend', password='pass12345')
        self.outsider = User.objects.create_user(username='outsider', password='pass12345')

        self.room = ChatRoom.objects.create(
            name='Private room',
            created_by=self.initiator,
            is_private=True,
        )
        self.room.members.add(self.initiator, self.participant)

        self.client = APIClient()

    @mock.patch('chat.views.send_call_invite_task.delay')
    def test_non_member_cannot_start_call(self, mock_delay):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(
            reverse('call-list'),
            {'room': self.room.id, 'participants': [self.participant.id]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CallSession.objects.count(), 0)
        mock_delay.assert_not_called()

    @mock.patch('chat.views.send_call_invite_task.delay')
    def test_cannot_invite_user_outside_room(self, mock_delay):
        self.client.force_authenticate(user=self.initiator)
        create_response = self.client.post(
            reverse('call-list'),
            {'room': self.room.id},
            format='json'
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        call_id = create_response.data['id']

        invite_response = self.client.post(
            reverse('call-invite', kwargs={'pk': call_id}),
            {'participants': [self.outsider.id]},
            format='json'
        )
        self.assertEqual(invite_response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_delay.assert_not_called()

    @mock.patch('chat.views.send_call_invite_task.delay')
    def test_blocked_user_cannot_be_invited(self, mock_delay):
        BlockedUser.objects.create(user=self.initiator, blocked_user=self.participant)
        self.client.force_authenticate(user=self.initiator)

        response = self.client.post(
            reverse('call-list'),
            {'room': self.room.id, 'participants': [self.participant.id]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CallSession.objects.count(), 0)
        mock_delay.assert_not_called()

    @mock.patch('chat.views.send_call_invite_task.delay')
    def test_user_who_blocked_initiator_is_not_invited(self, mock_delay):
        BlockedUser.objects.create(user=self.participant, blocked_user=self.initiator)
        self.client.force_authenticate(user=self.initiator)

        response = self.client.post(
            reverse('call-list'),
            {'room': self.room.id, 'participants': [self.participant.id]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CallSession.objects.count(), 0)
        mock_delay.assert_not_called()


@override_settings(SECURE_SSL_REDIRECT=False, DEBUG=True)
class CallSessionWebsocketTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.initiator = User.objects.create_user(username='caller_ws', password='pass12345')
        self.allowed_member = User.objects.create_user(username='friend_ws', password='pass12345')
        self.blocked_member = User.objects.create_user(username='blocked_ws', password='pass12345')
        self.outsider = User.objects.create_user(username='outsider_ws', password='pass12345')

        self.room = ChatRoom.objects.create(
            name='WS room',
            created_by=self.initiator,
            is_private=True,
        )
        self.room.members.add(self.initiator, self.allowed_member, self.blocked_member)

    def _communicator(self, user, call_type='audio'):
        communicator = WebsocketCommunicator(
            CallSignalingConsumer.as_asgi(),
            f"/ws/call/{call_type}/{self.room.id}/"
        )
        communicator.scope['user'] = user
        communicator.scope.setdefault('url_route', {}).setdefault('kwargs', {})
        communicator.scope['url_route']['kwargs'].update({
            'room_id': str(self.room.id),
            'call_type': call_type,
        })
        return communicator

    def test_non_member_connection_rejected(self):
        async def scenario():
            communicator = self._communicator(self.outsider)
            connected, _ = await communicator.connect()
            self.assertFalse(connected)
            await communicator.disconnect()
        async_to_sync(scenario)()

    @mock.patch('chat.call_consumers.send_call_invite_task.delay')
    def test_invite_skips_non_members(self, mock_delay):
        async def scenario():
            communicator = self._communicator(self.initiator)
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            join_raw = await communicator.receive_from()
            join_event = json.loads(join_raw)
            self.assertEqual(join_event.get('event'), 'joined')

            await communicator.send_json_to({
                'action': 'invite',
                'participants': [self.allowed_member.id, self.outsider.id]
            })
            raw = await communicator.receive_from()
            response = json.loads(raw)
            self.assertEqual(response.get('action'), 'invite-sent')
            self.assertEqual(response.get('data', {}).get('participants'), [self.allowed_member.id])

            await communicator.disconnect()
        async_to_sync(scenario)()

        self.assertTrue(
            CallParticipant.objects.filter(session__room=self.room, user=self.allowed_member).exists()
        )
        self.assertFalse(
            CallParticipant.objects.filter(session__room=self.room, user=self.outsider).exists()
        )
        self.assertEqual(mock_delay.call_count, 1)
        self.assertEqual(mock_delay.call_args[0][1], self.allowed_member.id)

    @mock.patch('chat.call_consumers.send_call_invite_task.delay')
    def test_invite_skips_blocked_users(self, mock_delay):
        BlockedUser.objects.create(user=self.initiator, blocked_user=self.blocked_member)

        async def scenario():
            communicator = self._communicator(self.initiator)
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            join_raw = await communicator.receive_from()
            join_event = json.loads(join_raw)
            self.assertEqual(join_event.get('event'), 'joined')

            await communicator.send_json_to({
                'action': 'invite',
                'participants': [self.blocked_member.id]
            })
            raw = await communicator.receive_from()
            response = json.loads(raw)
            self.assertEqual(response.get('action'), 'invite-sent')
            self.assertEqual(response.get('data', {}).get('participants'), [])

            await communicator.disconnect()
        async_to_sync(scenario)()

        self.assertFalse(
            CallParticipant.objects.filter(session__room=self.room, user=self.blocked_member).exists()
        )
        mock_delay.assert_not_called()
