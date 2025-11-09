"""
Consumer للإشعارات العامة - تحديث قائمة الدردشات في الوقت الفعلي
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message, MessageRead


class NotificationsConsumer(AsyncWebsocketConsumer):
    """Consumer للإشعارات العامة - مثل تحديث قائمة الدردشات"""
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        # مجموعة المستخدم للإشعارات
        self.user_group_name = f'user_{self.user.id}_notifications'
        
        # الانضمام إلى مجموعة المستخدم
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # مغادرة مجموعة المستخدم
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """استقبال رسائل من WebSocket"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'ping':
            # للتحقق من الاتصال
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': text_data_json.get('timestamp')
            }))
    
    async def new_message_notification(self, event):
        """إشعار برسالة جديدة - تحديث قائمة الدردشات"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'room_id': event.get('room_id'),
            'message': event.get('message'),
            'sender_id': event.get('sender_id'),
            'sender_username': event.get('sender_username'),
            'timestamp': event.get('timestamp'),
            'message_id': event.get('message_id'),
        }))
    
    async def chat_list_update(self, event):
        """تحديث قائمة الدردشات"""
        await self.send(text_data=json.dumps({
            'type': 'chat_list_update',
            'room_id': event.get('room_id'),
            'last_message': event.get('last_message'),
            'unread_count': event.get('unread_count'),
            'updated_at': event.get('updated_at'),
        }))

    async def stories_refresh(self, event):
        """تحديث الاستوريات في الوقت الحقيقي"""
        await self.send(text_data=json.dumps({
            'type': 'stories_refresh',
            'story': event.get('story'),
        }))

