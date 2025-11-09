import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message, MessageRead
from .tasks import send_message_notification_task


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer للدردشة المباشرة عبر WebSocket"""
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # التحقق من الأمان - المستخدم يجب أن يكون عضواً في الغرفة
        is_member = await self.check_user_is_member()
        if not is_member:
            await self.close()
            return
        
        # الانضمام إلى مجموعة الغرفة
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # تحديث حالة الاتصال
        await self.update_user_status(True)
    
    async def disconnect(self, close_code):
        # تحديث حالة عدم الاتصال
        await self.update_user_status(False)
        
        # مغادرة مجموعة الغرفة
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """استقبال رسالة من WebSocket"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            message_content = text_data_json.get('message', '')
            msg_type = text_data_json.get('message_type', 'text')
            file_url = text_data_json.get('file_url', None)
            file_name = text_data_json.get('file_name', None)
            
            # التحقق من الأمان - التأكد من وجود المستخدمين
            is_valid = await self.verify_users_exist(self.user.id, self.room_id)
            if not is_valid:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'خطأ في التحقق من المستخدمين'
                }))
                return
            
            # التحقق من طول الرسالة (للرسائل النصية فقط)
            if msg_type == 'text' and len(message_content) > 1000:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'الرسالة طويلة جداً'
                }))
                return
            
            # حفظ الرسالة (يدعم الملفات عبر API)
            message_obj = await self.save_message(message_content, msg_type, file_url, file_name)
            
            # إرسال الرسالة إلى مجموعة الغرفة
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'message_type': msg_type,
                    'file_url': file_url,
                    'file_name': file_name,
                    'timestamp': message_obj.created_at.isoformat(),
                    'message_id': message_obj.id,
                }
            )
            
            # إرسال إشعار للمستخدمين الآخرين (تحديث قائمة الدردشات)
            await self.notify_other_users(message_obj)
        elif message_type == 'typing':
            # إرسال إشعار الكتابة
            is_typing = text_data_json.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing',
                    'user': self.user.username,
                    'user_id': self.user.id,
                    'is_typing': is_typing,
                }
            )
    
    async def chat_message(self, event):
        """إرسال رسالة إلى WebSocket"""
        # تحديد حالة الرسالة بناءً على المرسل
        is_sent_by_me = event['sender_id'] == self.user.id
        
        # إذا كانت الرسالة من شخص آخر، تحديث حالة القراءة
        read_info = None
        if not is_sent_by_me:
            read_info = await self.mark_message_as_read(event.get('message_id'))
            
            # إذا تمت القراءة من قبل جميع الأعضاء، إرسال إشعار للمرسل
            if read_info and read_info['should_notify']:
                await self.channel_layer.group_send(
                    f'chat_{read_info["message"].room.id}',
                    {
                        'type': 'message_read',
                        'message_id': event.get('message_id'),
                        'read_by': self.user.username,
                    }
                )
        
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'message_type': event.get('message_type', 'text'),
            'file_url': event.get('file_url'),
            'file_name': event.get('file_name'),
            'timestamp': event.get('timestamp', ''),
            'message_id': event.get('message_id', ''),
        }))
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """تحديد الرسالة كمقروءة"""
        if not message_id:
            return None
        
        try:
            message = Message.objects.get(id=message_id)
            # إنشاء سجل قراءة إذا لم يكن موجوداً
            MessageRead.objects.get_or_create(
                message=message,
                user=self.user
            )
            
            # إرجاع معلومات الرسالة للتحقق من حالة القراءة
            read_count = message.read_by.count()
            room_member_count = message.room.members.count()
            
            return {
                'message': message,
                'read_count': read_count,
                'room_member_count': room_member_count,
                'should_notify': read_count >= room_member_count - 1
            }
        except Message.DoesNotExist:
            return None
    
    async def message_read(self, event):
        """إشعار قراءة الرسالة"""
        # إرسال فقط للمرسل الأصلي
        if event.get('message_id'):
            await self.send(text_data=json.dumps({
                'type': 'message_read',
                'message_id': event['message_id'],
                'read_by': event.get('read_by', ''),
            }))
    
    async def typing(self, event):
        """إرسال إشعار الكتابة"""
        # إرسال فقط إذا كان المستخدم مختلف
        if event.get('user_id') != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'user_id': event.get('user_id'),
                'is_typing': event['is_typing'],
            }))
    
    @database_sync_to_async
    def save_message(self, content, msg_type='text', file_url=None, file_name=None):
        """حفظ الرسالة في قاعدة البيانات"""
        from django.utils import timezone
        from .models import RecentContact
        
        room = ChatRoom.objects.get(id=self.room_id)
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
            message_type=msg_type
        )
        # تحديث updated_at للغرفة لتحديث ترتيب القائمة
        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])
        MessageRead.objects.create(message=message, user=self.user)
        
        # تحديث RecentContact للمستخدمين في المحادثة الخاصة
        if room.is_private and room.members.count() == 2:
            other_members = room.members.exclude(id=self.user.id)
            for other_user in other_members:
                # تحديث RecentContact للمرسل
                recent_contact, created = RecentContact.objects.get_or_create(
                    user=self.user,
                    contact_user=other_user
                )
                recent_contact.last_message_time = timezone.now()
                recent_contact.message_count += 1
                recent_contact.save(update_fields=['last_message_time', 'message_count'])
                
                # تحديث RecentContact للمستقبل أيضاً
                RecentContact.objects.update_or_create(
                    user=other_user,
                    contact_user=self.user,
                    defaults={
                        'last_message_time': timezone.now(),
                    }
                )
        
        return message
    
    @database_sync_to_async
    def check_user_is_member(self):
        """التحقق من أن المستخدم عضو في الغرفة"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return self.user in room.members.all()
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        """تحديث حالة المستخدم"""
        try:
            profile = self.user.profile
            profile.is_online = is_online
            profile.save()
        except:
            pass
    
    @database_sync_to_async
    def verify_users_exist(self, sender_id, room_id):
        """التحقق من وجود المرسل والمستقبل في قاعدة البيانات"""
        try:
            sender = User.objects.get(id=sender_id)
            room = ChatRoom.objects.get(id=room_id)
            return sender.is_active and room.members.filter(id=sender_id).exists()
        except (User.DoesNotExist, ChatRoom.DoesNotExist):
            return False
    
    async def notify_other_users(self, message_obj):
        """إرسال إشعار للمستخدمين الآخرين عند استقبال رسالة جديدة"""
        try:
            # الحصول على جميع الأعضاء الآخرين في الغرفة
            other_members = await self.get_other_members()
            
            for member in other_members:
                user_group_name = f'user_{member.id}_notifications'
                
                # حساب الرسائل غير المقروءة
                unread_count = await self.get_unread_count(member.id, message_obj.room.id)
                
                # إرسال إشعار WebSocket
                await self.channel_layer.group_send(
                    user_group_name,
                    {
                        'type': 'new_message_notification',
                        'room_id': message_obj.room.id,
                        'message': message_obj.content[:100],
                        'sender_id': message_obj.sender.id,
                        'sender_username': message_obj.sender.username,
                        'timestamp': message_obj.created_at.isoformat(),
                        'message_id': message_obj.id,
                    }
                )
                
                # إرسال تحديث قائمة الدردشات
                await self.channel_layer.group_send(
                    user_group_name,
                    {
                        'type': 'chat_list_update',
                        'room_id': message_obj.room.id,
                        'last_message': {
                            'id': message_obj.id,
                            'content': message_obj.content[:100],
                            'sender_id': message_obj.sender.id,
                            'sender_username': message_obj.sender.username,
                            'created_at': message_obj.created_at.isoformat(),
                        },
                        'unread_count': unread_count,
                        'updated_at': message_obj.room.updated_at.isoformat(),
                    }
                )
                
                # إرسال إشعار Push (في الخلفية عبر Celery)
                send_message_notification_task.delay(message_obj.id, member.id)
        except Exception as e:
            # في حالة فشل إرسال الإشعار، لا نوقف العملية
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"خطأ في إرسال الإشعارات: {e}")
    
    @database_sync_to_async
    def get_other_members(self):
        """الحصول على الأعضاء الآخرين في الغرفة"""
        room = ChatRoom.objects.get(id=self.room_id)
        return list(room.members.exclude(id=self.user.id))
    
    @database_sync_to_async
    def get_unread_count(self, user_id, room_id):
        """حساب الرسائل غير المقروءة"""
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=room_id)
        return Message.objects.filter(
            room=room
        ).exclude(
            read_by__user=user
        ).count()

