"""
Service لإرسال إشعارات Push عبر Firebase Cloud Messaging (FCM)
"""
import logging
from typing import Dict, Iterable, Optional
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse

from .models import DeviceToken, Message, ChatRoom

logger = logging.getLogger(__name__)

try:
    from pyfcm import FCMNotification

    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False
    logger.warning("pyfcm غير مثبت. إشعارات Push لن تعمل. قم بتثبيته: pip install pyfcm")


class PushNotificationService:
    """خدمة إرسال إشعارات Push"""
    
    def __init__(self):
        """تهيئة خدمة FCM"""
        self.fcm_available = FCM_AVAILABLE
        self.base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        self.default_icon = None  # للتطبيق الأصلي فقط - لا حاجة لـ icon URL

        if self.fcm_available:
            # الحصول على FCM Server Key من الإعدادات
            # يمكن إضافتها في settings.py: FCM_SERVER_KEY = "your-server-key"
            self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
            
            if self.fcm_server_key:
                try:
                    self.push_service = FCMNotification(api_key=self.fcm_server_key)
                    logger.info("تم تهيئة خدمة FCM بنجاح")
                except Exception as e:
                    logger.error(f"خطأ في تهيئة خدمة FCM: {e}")
                    self.fcm_available = False
            else:
                logger.warning("FCM_SERVER_KEY غير موجود في الإعدادات. إشعارات Push لن تعمل.")
                self.fcm_available = False
        else:
            self.push_service = None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def build_absolute_url(self, path: Optional[str]) -> str:
        """تحويل المسار إلى رابط مطلق بناءً على الإعدادات."""
        if not path:
            return ''

        path = str(path)
        if path.startswith('http://') or path.startswith('https://'):
            return path

        base = self.base_url
        if not base:
            return path

        return urljoin(f"{base.rstrip('/')}/", path.lstrip('/'))

    def _prepare_data_payload(self, data: Optional[Dict]) -> Dict:
        """تحويل البيانات إلى صيغ نصية للتوافق مع FCM."""
        prepared: Dict[str, str] = {}
        if not data:
            return prepared

        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, bool):
                prepared[key] = 'true' if value else 'false'
            elif isinstance(value, (int, float)):
                prepared[key] = str(value)
            else:
                prepared[key] = str(value)
        return prepared

    def _deactivate_token(self, token):
        """تعطيل token غير صالح"""
        try:
            device_token = DeviceToken.objects.get(token=token)
            device_token.is_active = False
            device_token.save()
            logger.info(f"تم تعطيل token غير صالح: {token[:20]}...")
        except DeviceToken.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"خطأ في تعطيل token: {e}")

    def _update_token(self, old_token: str, new_token: str) -> None:
        """تحديث token إذا أعادت FCM رمزاً بديلاً (canonical id)."""
        if not new_token or new_token == old_token:
            return
        try:
            device_token = DeviceToken.objects.get(token=old_token)
            # إذا كان الرمز الجديد موجوداً، نعطل القديم
            existing = DeviceToken.objects.filter(token=new_token).exclude(pk=device_token.pk).first()
            if existing:
                device_token.is_active = False
                device_token.save(update_fields=['is_active'])
                logger.info("تم تعطيل الرمز القديم بسبب وجود رمز مطابق جديد.")
                return

            device_token.token = new_token
            device_token.save(update_fields=['token', 'last_used'])
            logger.info("تم تحديث رمز الجهاز إلى canonical id الجديد.")
        except DeviceToken.DoesNotExist:
            logger.debug("محاولة تحديث رمز غير موجود بعد استجابة canonical id من FCM.")
        except Exception as exc:
            logger.warning("تعذر تحديث رمز الجهاز بعد canonical id: %s", exc)

    # ------------------------------------------------------------------ #
    # إرسال الإشعارات
    # ------------------------------------------------------------------ #

    def send_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        sound: str = "default",
        *,
        click_action: Optional[str] = None,
        android_channel_id: Optional[str] = None,
        priority: str = "high",
        icon: Optional[str] = None,
    ):
        """
        إرسال إشعار لجهاز واحد
        
        Args:
            device_token: FCM token للجهاز
            title: عنوان الإشعار
            body: نص الإشعار
            data: بيانات إضافية (dict)
            sound: صوت الإشعار
        
        Returns:
            bool: True إذا نجح الإرسال، False إذا فشل
        """
        if not self.fcm_available or not self.push_service:
            logger.warning("خدمة FCM غير متاحة")
            return False
        
        try:
            payload = self._prepare_data_payload(data)
            payload.setdefault('title', title)
            payload.setdefault('body', body)

            badge_value = payload.get('badge', 1)
            try:
                badge = int(badge_value)
            except (TypeError, ValueError):
                badge = 1

            result = self.push_service.notify_single_device(
                registration_id=device_token,
                message_title=title,
                message_body=body,
                data_message=payload,
                sound=sound,
                badge=badge,
                click_action=click_action or payload.get('url'),
                android_channel_id=android_channel_id,
                android_priority=priority,
                extra_notification_kwargs={
                    'sound': sound,
                    'icon': icon or self.default_icon,
                    'tag': payload.get('type', 'arab-chat'),
                },
            )
            
            if result.get('success', 0) == 1:
                logger.info(f"تم إرسال الإشعار بنجاح إلى {device_token[:20]}...")
                canonical = result.get('results', [{}])[0].get('registration_id')
                if canonical:
                    self._update_token(device_token, canonical)
                return True
            else:
                error = result.get('results', [{}])[0].get('error')
                logger.warning(f"فشل إرسال الإشعار: {error}")
                
                # إذا كان الخطأ بسبب token غير صالح، تعطيله
                if error in ['InvalidRegistration', 'NotRegistered']:
                    self._deactivate_token(device_token)
                
                return False
        except Exception as e:
            logger.error(f"خطأ في إرسال الإشعار: {e}")
            return False
    
    def send_notification_to_user(
        self,
        user,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        sound: str = "default",
        **kwargs,
    ):
        """
        إرسال إشعار لجميع أجهزة المستخدم
        
        Args:
            user: المستخدم
            title: عنوان الإشعار
            body: نص الإشعار
            data: بيانات إضافية (dict)
            sound: صوت الإشعار
        
        Returns:
            int: عدد الأجهزة التي تم إرسال الإشعار لها بنجاح
        """
        if not self.fcm_available:
            return 0
        
        # الحصول على جميع الأجهزة النشطة للمستخدم
        device_tokens = DeviceToken.objects.filter(
            user=user,
            is_active=True
        ).values_list('token', flat=True)
        
        success_count = 0
        for token in device_tokens:
            if self.send_notification(token, title, body, data, sound, **kwargs):
                success_count += 1
        
        return success_count
    
    def send_message_notification(self, message, recipient_user):
        """
        إرسال إشعار عند استقبال رسالة جديدة
        
        Args:
            message: كائن Message
            recipient_user: المستخدم المستقبل
        """
        if not self.fcm_available:
            return
        
        # التحقق من أن المستخدم غير متصل (لا حاجة لإشعار إذا كان متصلاً)
        try:
            if recipient_user.profile.is_online:
                # يمكن إرسال الإشعار حتى لو كان متصلاً (اختياري)
                pass
        except:
            pass
        
        # الحصول على معلومات المرسل
        sender_name = message.sender.username
        room = message.room
        
        # تحديد نوع المحتوى
        message_preview = message.content[:100]
        if message.message_type == 'image':
            message_preview = "📷 صورة"
        elif message.message_type == 'file':
            message_preview = "📎 ملف"
        elif message.message_type == 'audio':
            message_preview = "🎤 رسالة صوتية"
        
        # تحديد عنوان الإشعار
        if room.is_private:
            title = sender_name
        else:
            title = f"{room.name}"
            message_preview = f"{sender_name}: {message_preview}"
        
        try:
            chat_path = reverse('chat_room', args=[room.id])
        except Exception:
            chat_path = f'/chats/{room.id}/'
        message_url = self.build_absolute_url(f"{chat_path}?message={message.id}")

        # بيانات إضافية للإشعار
        data = {
            'type': 'new_message',
            'message_id': str(message.id),
            'room_id': str(room.id),
            'sender_id': str(message.sender.id),
            'sender_username': sender_name,
            'message_type': message.message_type,
            'timestamp': message.created_at.isoformat(),
            'url': message_url,
            'sound': 'message_chime',
            'category': 'chat_message',
        }
        
        # إرسال الإشعار
        self.send_notification_to_user(
            user=recipient_user,
            title=title,
            body=message_preview,
            data=data,
            sound="message_chime",
            android_channel_id='arab_chat_messages',
            priority='high',
        )
    
    def send_friend_request_notification(self, friend_request):
        """
        إرسال إشعار عند استقبال طلب صداقة
        
        Args:
            friend_request: كائن FriendRequest
        """
        if not self.fcm_available:
            return
        
        sender_name = friend_request.from_user.username
        title = "طلب صداقة جديد"
        body = f"{sender_name} أرسل لك طلب صداقة"
        try:
            request_path = reverse('search')
        except Exception:
            request_path = '/search/'
        request_url = self.build_absolute_url(request_path)
        
        data = {
            'type': 'friend_request',
            'friend_request_id': str(friend_request.id),
            'from_user_id': str(friend_request.from_user.id),
            'from_username': sender_name,
            'url': request_url,
            'sound': 'message_chime',
            'category': 'friend_request',
        }
        
        self.send_notification_to_user(
            user=friend_request.to_user,
            title=title,
            body=body,
            data=data,
            sound='message_chime',
            android_channel_id='arab_chat_messages',
            priority='high',
        )

    def send_call_invitation(self, call_session, recipient_user):
        """
        إرسال إشعار دعوة مكالمة صوتية/فيديو.
        """
        if not self.fcm_available:
            return

        initiator = call_session.initiator
        room = call_session.room
        try:
            room_path = reverse('chat_room', args=[room.id])
        except Exception:
            room_path = f'/chats/{room.id}/'
        call_url = self.build_absolute_url(f"{room_path}?call_session={call_session.id}&type={call_session.call_type}")
        title = f"مكالمة {'فيديو' if call_session.call_type == 'video' else 'صوتية'} واردة"
        if room.is_private:
            body = f"{initiator.username} يتصل بك الآن"
        else:
            body = f"{initiator.username} بدأ مكالمة في {room.name}"

        data = {
            'type': 'call_invite',
            'call_id': str(call_session.id),
            'room_id': str(room.id),
            'call_type': call_session.call_type,
            'initiator_id': str(initiator.id),
            'initiator_username': initiator.username,
            'timestamp': call_session.created_at.isoformat(),
            'url': call_url,
            'sound': 'call_incoming',
            'category': 'call_invite',
            'requireInteraction': 'true',
        }

        self.send_notification_to_user(
            user=recipient_user,
            title=title,
            body=body,
            data=data,
            sound='call_incoming',
            android_channel_id='arab_chat_calls',
            priority='high',
        )
    
    def send_story_notification(self, story, recipient_user):
        """
        إرسال إشعار عند نشر استوري جديد.
        """
        if not self.fcm_available:
            return

        story_owner = story.user
        try:
            stories_path = reverse('stories')
        except Exception:
            stories_path = '/stories/'

        query = f"story_user={story_owner.id}&story={story.id}"
        story_url = self.build_absolute_url(f"{stories_path}?{query}")

        title = f"استوري جديد من {story_owner.username}"
        caption = getattr(story, 'caption', None) or getattr(story, 'text_content', None)
        body = (caption or "قام بنشر قصة جديدة.").strip()[:120]

        data = {
            'type': 'story_update',
            'story_id': str(story.id),
            'story_user_id': str(story_owner.id),
            'url': story_url,
            'sound': 'story_ping',
            'category': 'stories',
        }

        self.send_notification_to_user(
            user=recipient_user,
            title=title,
            body=body,
            data=data,
            sound='story_ping',
            android_channel_id='arab_chat_stories',
            priority='normal',
        )

# إنشاء instance عام للخدمة
push_notification_service = PushNotificationService()
