import json
from typing import Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import ChatRoom, CallSession, CallParticipant, BlockedUser
from .tasks import send_call_invite_task


class CallSignalingConsumer(AsyncWebsocketConsumer):
    """
    Consumer لإدارة إشارة WebRTC (offer/answer/ICE) للمكالمات الصوتية والفيديو.
    """

    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close(code=4401)
            return

        self.call_type = self.scope['url_route']['kwargs'].get('call_type', 'audio')
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = f'call_{self.call_type}_{self.room_id}'

        room = await self._get_user_room()
        if room is None:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self._ensure_participant_record()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'call.participant_event',
                'payload': {
                    'event': 'joined',
                    'user_id': self.user.id,
                    'username': self.user.username,
                }
            }
        )

    async def disconnect(self, close_code):
        await self._mark_disconnected()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'call.participant_event',
                'payload': {
                    'event': 'left',
                    'user_id': self.user.id,
                    'username': self.user.username,
                }
            }
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = payload.get('action')
        if action == 'invite':
            await self._handle_invite(payload)
            return

        if action == 'end':
            await self._handle_end(payload)
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'call.message',
                'payload': {
                    'from': self.user.id,
                    'action': action,
                    'data': payload.get('data'),
                    'metadata': payload.get('metadata', {}),
                }
            }
        )

    async def call_message(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    async def call_participant_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    async def _handle_invite(self, payload: dict):
        participant_ids = payload.get('participants', [])
        if isinstance(participant_ids, int):
            participant_ids = [participant_ids]

        if not participant_ids:
            return

        session = await self._get_or_create_active_session()
        recipients = await self._add_participants(session, participant_ids)
        for recipient_id in recipients:
            send_call_invite_task.delay(session.id, recipient_id)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'call.message',
                'payload': {
                    'from': self.user.id,
                    'action': 'invite-sent',
                    'data': {'participants': recipients},
                }
            }
        )

    async def _handle_end(self, payload: dict):
        reason = payload.get('reason') or CallSession.EndReason.NORMAL
        session = await self._get_active_session()
        if session:
            await database_sync_to_async(session.end)(reason=reason)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'call.message',
                'payload': {
                    'from': self.user.id,
                    'action': 'ended',
                    'data': {'reason': reason},
                }
            }
        )

    @database_sync_to_async
    def _get_user_room(self) -> Optional[ChatRoom]:
        try:
            return ChatRoom.objects.filter(id=self.room_id, members=self.user).first()
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_active_session(self) -> Optional[CallSession]:
        return (
            CallSession.objects.filter(
                room_id=self.room_id,
                call_type=self.call_type,
                status__in=[CallSession.Status.ACTIVE, CallSession.Status.PENDING]
            )
            .order_by('-created_at')
            .first()
        )

    @database_sync_to_async
    def _create_session(self) -> CallSession:
        session = CallSession.objects.create(
            room_id=self.room_id,
            initiator=self.user,
            call_type=self.call_type,
        )
        session.activate()
        CallParticipant.objects.get_or_create(
            session=session,
            user=self.user,
            defaults={'role': CallParticipant.Role.CALLER, 'is_connected': True}
        )
        return session

    async def _get_or_create_active_session(self) -> CallSession:
        session = await self._get_active_session()
        if session:
            return session
        return await self._create_session()

    @database_sync_to_async
    def _add_participants(self, session: CallSession, participant_ids) -> list[int]:
        if not participant_ids:
            return []

        room_member_ids = set(
            session.room.members.filter(id__in=participant_ids).values_list('id', flat=True)
        )
        # استبعاد المرسل وأي مستخدم غير عضو في الغرفة
        allowed_ids = [pid for pid in room_member_ids if pid != self.user.id]
        if not allowed_ids:
            return []

        blocked_ids = set(
            BlockedUser.objects.filter(
                Q(user_id=self.user.id, blocked_user_id__in=allowed_ids) |
                Q(user_id__in=allowed_ids, blocked_user_id=self.user.id)
            ).values_list('blocked_user_id', flat=True)
        )
        allowed_ids = [pid for pid in allowed_ids if pid not in blocked_ids]
        if not allowed_ids:
            return []

        users = User.objects.filter(id__in=allowed_ids, is_active=True)
        invited = []
        for participant_user in users:
            participant, _ = CallParticipant.objects.get_or_create(
                session=session,
                user=participant_user,
                defaults={'role': CallParticipant.Role.RECEIVER}
            )
            invited.append(participant.user_id)
        return invited

    @database_sync_to_async
    def _ensure_participant_record(self):
        session = CallSession.objects.filter(
            room_id=self.room_id,
            call_type=self.call_type,
            status__in=[CallSession.Status.ACTIVE, CallSession.Status.PENDING]
        ).order_by('-created_at').first()

        if not session:
            session = CallSession.objects.create(
                room_id=self.room_id,
                initiator=self.user,
                call_type=self.call_type,
            )
            session.activate()

        participant, _ = CallParticipant.objects.get_or_create(
            session=session,
            user=self.user,
            defaults={'role': CallParticipant.Role.RECEIVER}
        )
        participant.mark_connected()

    @database_sync_to_async
    def _mark_disconnected(self):
        participants = CallParticipant.objects.filter(
            session__room_id=self.room_id,
            user=self.user,
            session__call_type=self.call_type,
            session__status__in=[CallSession.Status.ACTIVE, CallSession.Status.PENDING]
        )
        sessions = list(participants.values_list('session_id', flat=True))
        participants.update(is_connected=False, left_at=timezone.now())
        for session_id in sessions:
            if session_id and not CallParticipant.objects.filter(session_id=session_id, is_connected=True).exists():
                try:
                    session = CallSession.objects.get(id=session_id)
                    session.end(reason=CallSession.EndReason.NO_PARTICIPANTS)
                except CallSession.DoesNotExist:
                    continue

