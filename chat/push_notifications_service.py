"""
Service لإرسال إشعارات Push عبر Firebase Cloud Messaging (FCM)
"""
import logging
from django.conf import settings
from django.utils import timezone
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
    
    def send_notification(self, device_token, title, body, data=None, sound="default"):
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
            result = self.push_service.notify_single_device(
                registration_id=device_token,
                message_title=title,
                message_body=body,
                data_message=data or {},
                sound=sound,
                badge=1
            )
            
            if result.get('success', 0) == 1:
                logger.info(f"تم إرسال الإشعار بنجاح إلى {device_token[:20]}...")
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
    
    def send_notification_to_user(self, user, title, body, data=None, sound="default"):
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
            if self.send_notification(token, title, body, data, sound):
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
        
        # بيانات إضافية للإشعار
        data = {
            'type': 'new_message',
            'message_id': str(message.id),
            'room_id': str(room.id),
            'sender_id': str(message.sender.id),
            'sender_username': sender_name,
            'message_type': message.message_type,
            'timestamp': message.created_at.isoformat(),
        }
        
        # إرسال الإشعار
        self.send_notification_to_user(
            user=recipient_user,
            title=title,
            body=message_preview,
            data=data,
            sound="default"
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
        
        data = {
            'type': 'friend_request',
            'friend_request_id': str(friend_request.id),
            'from_user_id': str(friend_request.from_user.id),
            'from_username': sender_name,
        }
        
        self.send_notification_to_user(
            user=friend_request.to_user,
            title=title,
            body=body,
            data=data
        )

    def send_call_invitation(self, call_session, recipient_user):
        """
        إرسال إشعار دعوة مكالمة صوتية/فيديو.
        """
        if not self.fcm_available:
            return

        initiator = call_session.initiator
        room = call_session.room

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
        }

        self.send_notification_to_user(
            user=recipient_user,
            title=title,
            body=body,
            data=data,
            sound='call_incoming'
        )
    
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


# إنشاء instance عام للخدمة
push_notification_service = PushNotificationService()

