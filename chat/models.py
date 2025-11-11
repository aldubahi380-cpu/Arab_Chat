import logging
from datetime import timedelta
import secrets

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """ملف المستخدم الممتد"""
    # في مرحلة التطوير: قبول أي رقم حتى غير حقيقي
    # phone_validator = RegexValidator(
    #     regex=r'^\+?1?\d{9,15}$',
    #     message="يجب أن يكون رقم الهاتف بتنسيق صحيح"
    # )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='المستخدم')
    phone = models.CharField(
        max_length=50,  # زيادة الطول لقبول أي رقم
        unique=True,
        verbose_name='رقم الهاتف',
        blank=False,  # مطلوب
        null=False,
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='الصورة الشخصية')
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name='صورة الغلاف')
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name='نبذة عني')
    is_online = models.BooleanField(default=False, verbose_name='متصل')
    last_seen = models.DateTimeField(default=timezone.now, verbose_name='آخر ظهور')
    is_verified = models.BooleanField(default=False, verbose_name='حساب موثق')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.phone}"


class ChatRoom(models.Model):
    """غرفة الدردشة"""
    ROOM_TYPE_COMMUNITY = 'community'
    ROOM_TYPE_GROUP = 'group'
    ROOM_TYPE_CHOICES = [
        (ROOM_TYPE_COMMUNITY, 'مجتمع'),
        (ROOM_TYPE_GROUP, 'مجموعة'),
    ]
    name = models.CharField(max_length=100, verbose_name='اسم الغرفة')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default=ROOM_TYPE_COMMUNITY, verbose_name='نوع الغرفة')
    is_private = models.BooleanField(default=False, verbose_name='خاصة')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', verbose_name='أنشأها')
    members = models.ManyToManyField(User, related_name='chat_rooms', verbose_name='الأعضاء')
    invite_code = models.CharField(max_length=32, unique=True, blank=True, null=True, verbose_name='رمز الدعوة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'غرفة دردشة'
        verbose_name_plural = 'غرف الدردشة'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.room_type == self.ROOM_TYPE_GROUP:
            self.is_private = True
            if not self.invite_code:
                self.invite_code = self.generate_invite_code()
        elif self.room_type == self.ROOM_TYPE_COMMUNITY:
            self.is_private = False
        super().save(*args, **kwargs)

    def generate_invite_code(self):
        """إنشاء رمز دعوة فريد"""
        for _ in range(10):
            candidate = secrets.token_urlsafe(8).replace('-', '').replace('_', '')[:10]
            if not self.__class__.objects.filter(invite_code=candidate).exists():
                return candidate
        return secrets.token_hex(8)

    def get_invite_link(self, request=None):
        if not self.invite_code:
            return None
        from django.urls import reverse
        path = reverse('join_group_by_code', kwargs={'invite_code': self.invite_code})
        if request:
            return request.build_absolute_uri(path)
        return path


class Message(models.Model):
    """الرسائل"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name='الغرفة')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='المرسل')
    content = models.TextField(verbose_name='المحتوى')
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'نص'),
            ('image', 'صورة'),
            ('video', 'فيديو'),
            ('file', 'ملف'),
            ('audio', 'صوت'),
        ],
        default='text',
        verbose_name='نوع الرسالة'
    )
    file = models.FileField(upload_to='messages/', blank=True, null=True, verbose_name='الملف')
    original_file = models.FileField(upload_to='messages/original/', blank=True, null=True, verbose_name='الملف الأصلي')
    is_read = models.BooleanField(default=False, verbose_name='مقروءة')
    is_deleted = models.BooleanField(default=False, verbose_name='محذوفة')  # حذف ناعم
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الحذف')
    is_edited = models.BooleanField(default=False, verbose_name='تم التعديل')
    edited_at = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f"{self.sender.username} - {self.content[:50]}"

    def delete(self, using=None, keep_parents=False):
        file_refs = []
        if self.file:
            file_refs.append((self.file.storage, self.file.name))
        if self.original_file:
            file_refs.append((self.original_file.storage, self.original_file.name))

        result = super().delete(using=using, keep_parents=keep_parents)

        for storage, name in file_refs:
            try:
                if storage and name:
                    storage.delete(name)
            except Exception as exc:
                logger.warning(
                    "Failed to delete file %s for message %s during cleanup: %s",
                    name,
                    self.pk,
                    exc,
                    exc_info=True,
                )
        return result


class MessageRead(models.Model):
    """تتبع قراءة الرسائل"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by', verbose_name='الرسالة')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages', verbose_name='المستخدم')
    read_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ القراءة')

    class Meta:
        verbose_name = 'رسالة مقروءة'
        verbose_name_plural = 'الرسائل المقروءة'
        unique_together = ['message', 'user']
        ordering = ['-read_at']

    def __str__(self):
        return f"{self.user.username} قرأ رسالة {self.message.id}"


class OTPVerification(models.Model):
    """نموذج التحقق برمز OTP"""
    phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    otp_code = models.CharField(max_length=6, verbose_name='رمز التحقق')
    is_verified = models.BooleanField(default=False, verbose_name='تم التحقق')
    expires_at = models.DateTimeField(verbose_name='ينتهي في')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'رمز التحقق'
        verbose_name_plural = 'رموز التحقق'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone} - {self.otp_code}"


class FriendRequest(models.Model):
    """طلبات الصداقة"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
    ]
    
    from_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_friend_requests',
        verbose_name='من'
    )
    to_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_friend_requests',
        verbose_name='إلى'
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='الحالة'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'طلب صداقة'
        verbose_name_plural = 'طلبات الصداقة'
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


class Friend(models.Model):
    """الصداقات"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friends',
        verbose_name='المستخدم'
    )
    friend = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friend_of',
        verbose_name='الصديق'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')
    
    class Meta:
        verbose_name = 'صديق'
        verbose_name_plural = 'الأصدقاء'
        unique_together = ['user', 'friend']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} <-> {self.friend.username}"


class BlockedUser(models.Model):
    """المستخدمون المحظورون"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blocked_users',
        verbose_name='المستخدم'
    )
    blocked_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blocked_by',
        verbose_name='المحظور'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحظر')
    
    class Meta:
        verbose_name = 'مستخدم محظور'
        verbose_name_plural = 'المستخدمون المحظورون'
        unique_together = ['user', 'blocked_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} حظر {self.blocked_user.username}"


class StoryQuerySet(models.QuerySet):
    """استعلامات مخصصة للاستوريات"""

    def active(self):
        return self.filter(expires_at__gt=timezone.now())

    def purge_expired(self):
        expired_stories = list(self.filter(expires_at__lte=timezone.now()))
        for story in expired_stories:
            story.delete()
        return len(expired_stories)


class StoryManager(models.Manager):
    """مدير للاستوريات مع وظائف مساعدة"""

    def get_queryset(self):
        return StoryQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def purge_expired(self):
        return self.get_queryset().purge_expired()


class Story(models.Model):
    """الاستوريات"""
    CONTENT_TYPE_CHOICES = [
        ('image', 'صورة'),
        ('video', 'فيديو'),
        ('text', 'نص'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='stories',
        verbose_name='المستخدم'
    )
    content_type = models.CharField(
        max_length=10, 
        choices=CONTENT_TYPE_CHOICES,
        default='image',
        verbose_name='نوع المحتوى'
    )
    content = models.FileField(upload_to='stories/', verbose_name='المحتوى', blank=True, null=True)
    text_content = models.TextField(blank=True, null=True, verbose_name='المحتوى النصي')
    background_color = models.CharField(max_length=30, blank=True, null=True, verbose_name='لون الخلفية')
    font_color = models.CharField(max_length=30, blank=True, null=True, verbose_name='لون الخط')
    caption = models.TextField(max_length=500, blank=True, null=True, verbose_name='النص التوضيحي')
    expires_at = models.DateTimeField(verbose_name='ينتهي في')
    views_count = models.IntegerField(default=0, verbose_name='عدد المشاهدات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    objects = StoryManager()
    
    class Meta:
        verbose_name = 'استوري'
        verbose_name_plural = 'الاستوريات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"استوري {self.user.username} - {self.content_type}"

    @property
    def is_active(self):
        return self.expires_at > timezone.now()

    def seconds_until_expiry(self):
        remaining = (self.expires_at - timezone.now()).total_seconds()
        return max(0, int(remaining))

    def delete(self, using=None, keep_parents=False):
        content_storage = None
        content_name = None
        if self.content:
            content_storage = self.content.storage
            content_name = self.content.name
        result = super().delete(using=using, keep_parents=keep_parents)
        if content_storage and content_name:
            try:
                content_storage.delete(content_name)
            except Exception:
                pass
        return result


class StoryView(models.Model):
    """مشاهدات الاستوريات"""
    story = models.ForeignKey(
        Story, 
        on_delete=models.CASCADE, 
        related_name='views',
        verbose_name='الاستوري'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='viewed_stories',
        verbose_name='المشاهد'
    )
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ المشاهدة')
    
    class Meta:
        verbose_name = 'مشاهدة استوري'
        verbose_name_plural = 'مشاهدات الاستوريات'
        unique_together = ['story', 'user']
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user.username} شاهد استوري {self.story.id}"


class Contact(models.Model):
    """مزامنة جهات الاتصال"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contacts',
        verbose_name='المستخدم'
    )
    phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name='الاسم')
    is_registered = models.BooleanField(default=False, verbose_name='مسجل في التطبيق')
    registered_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='contact_entries',
        verbose_name='المستخدم المسجل'
    )
    synced_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ المزامنة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')
    
    class Meta:
        verbose_name = 'جهة اتصال'
        verbose_name_plural = 'جهات الاتصال'
        unique_together = ['user', 'phone']
        ordering = ['-synced_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.phone}"


class DeviceToken(models.Model):
    """نموذج لتخزين FCM tokens للأجهزة"""
    DEVICE_TYPE_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name='المستخدم'
    )
    token = models.CharField(max_length=500, unique=True, verbose_name='رمز الجهاز (FCM Token)')
    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE_CHOICES,
        default='android',
        verbose_name='نوع الجهاز'
    )
    device_id = models.CharField(max_length=200, blank=True, null=True, verbose_name='معرف الجهاز')
    device_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم الجهاز')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    last_used = models.DateTimeField(auto_now=True, verbose_name='آخر استخدام')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'رمز جهاز'
        verbose_name_plural = 'رموز الأجهزة'
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.token[:20]}..."


class SessionDevice(models.Model):
    """جلسات الأجهزة المعتمدة لتخطي تسجيل الدخول"""

    DEFAULT_TTL_DAYS = 90

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='session_devices',
        verbose_name='المستخدم'
    )
    session_token = models.CharField(max_length=128, unique=True, verbose_name='رمز الجلسة')
    device_id = models.CharField(max_length=128, unique=True, verbose_name='معرف الجهاز')
    device_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='اسم الجهاز')
    platform = models.CharField(max_length=50, blank=True, null=True, verbose_name='نظام التشغيل')
    user_agent = models.CharField(max_length=512, blank=True, null=True, verbose_name='معلومات المتصفح')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='عنوان IP')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    expires_at = models.DateTimeField(verbose_name='تاريخ انتهاء الصلاحية')
    last_seen = models.DateTimeField(auto_now=True, verbose_name='آخر استخدام')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'جلسة جهاز'
        verbose_name_plural = 'جلسات الأجهزة'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_token']),
            models.Index(fields=['device_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.device_name or self.platform or 'Unknown device'}"

    @classmethod
    def _generate_token(cls):
        return secrets.token_urlsafe(48)

    @classmethod
    def _generate_device_id(cls):
        return secrets.token_urlsafe(24)

    @classmethod
    def issue_for_request(cls, user, request=None, device_id=None, device_name=None, platform=None, ttl_days=None):
        """إنشاء أو تحديث جلسة لجهاز محدد"""
        ttl_days = ttl_days or cls.DEFAULT_TTL_DAYS
        expires_at = timezone.now() + timedelta(days=ttl_days)

        resolved_device_id = device_id or cls._generate_device_id()
        session_token = cls._generate_token()

        defaults = {
            'session_token': session_token,
            'device_name': device_name,
            'platform': platform,
            'expires_at': expires_at,
            'is_active': True,
        }

        if request is not None:
            defaults['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:512]
            ip = request.META.get('REMOTE_ADDR')
            if not ip:
                forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
                if forwarded:
                    ip = forwarded.split(',')[0].strip()
            defaults['ip_address'] = ip

        session_device, created = cls.objects.update_or_create(
            user=user,
            device_id=resolved_device_id,
            defaults=defaults
        )

        if not created:
            session_device.last_seen = timezone.now()
            session_device.save(update_fields=[
                'session_token', 'device_name', 'platform', 'expires_at',
                'is_active', 'user_agent', 'ip_address', 'last_seen'
            ])

        return session_device

    def mark_inactive(self):
        if not self.is_active:
            return
        self.is_active = False
        self.expires_at = timezone.now()
        self.save(update_fields=['is_active', 'expires_at'])

    def is_valid(self):
        return self.is_active and self.expires_at >= timezone.now()

    def touch(self):
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class RecentContact(models.Model):
    """نموذج لحفظ المستخدمين الذين تواصل معهم المستخدم"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recent_contacts',
        verbose_name='المستخدم'
    )
    contact_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recent_contacts_of',
        verbose_name='المستخدم المتواصل معه'
    )
    last_message_time = models.DateTimeField(auto_now=True, verbose_name='آخر رسالة')
    message_count = models.IntegerField(default=0, verbose_name='عدد الرسائل')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'مستخدم متواصل معه'
        verbose_name_plural = 'المستخدمون المتواصل معهم'
        unique_together = ['user', 'contact_user']
        ordering = ['-last_message_time']
        indexes = [
            models.Index(fields=['user', '-last_message_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} <-> {self.contact_user.username}"


class CallSession(models.Model):
    """تمثيل جلسة مكالمة صوتية أو فيديو بين مجموعة من المستخدمين."""

    class CallType(models.TextChoices):
        AUDIO = 'audio', 'صوتية'
        VIDEO = 'video', 'فيديو'

    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد الإنشاء'
        ACTIVE = 'active', 'نشطة'
        ENDED = 'ended', 'منتهية'
        CANCELLED = 'cancelled', 'ملغاة'

    class EndReason(models.TextChoices):
        NORMAL = 'normal', 'انتهت بشكل طبيعي'
        CANCELLED = 'cancelled', 'ألغيت من أحد الأطراف'
        TIMEOUT = 'timeout', 'انتهت لانتهاء الوقت'
        NO_PARTICIPANTS = 'no_participants', 'انتهت لانقطاع الجميع'

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='call_sessions',
        verbose_name='غرفة الدردشة'
    )
    initiator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='initiated_calls',
        verbose_name='المنشئ'
    )
    call_type = models.CharField(
        max_length=10,
        choices=CallType.choices,
        default=CallType.AUDIO,
        verbose_name='نوع المكالمة'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='الحالة'
    )
    end_reason = models.CharField(
        max_length=20,
        choices=EndReason.choices,
        blank=True,
        null=True,
        verbose_name='سبب الانتهاء'
    )
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ بدء المكالمة')
    ended_at = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ انتهاء المكالمة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'جلسة مكالمة'
        verbose_name_plural = 'جلسات المكالمات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['room', 'status']),
        ]

    def __str__(self) -> str:
        return f"Call #{self.pk} - {self.call_type} - {self.status}"

    def activate(self):
        if self.status == self.Status.ACTIVE:
            return
        self.status = self.Status.ACTIVE
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def end(self, reason: str = EndReason.NORMAL):
        if self.status in (self.Status.ENDED, self.Status.CANCELLED):
            return
        self.status = self.Status.CANCELLED if reason == self.EndReason.CANCELLED else self.Status.ENDED
        self.end_reason = reason
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'end_reason', 'ended_at', 'updated_at'])
        self.participants.update(is_connected=False, left_at=timezone.now())


class CallParticipant(models.Model):
    """مشاركة مستخدم في جلسة مكالمة."""

    class Role(models.TextChoices):
        CALLER = 'caller', 'المتصل'
        RECEIVER = 'receiver', 'المستقبل'

    session = models.ForeignKey(
        CallSession,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='جلسة المكالمة'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='call_participations',
        verbose_name='المستخدم'
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.RECEIVER,
        verbose_name='الدور'
    )
    peer_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='معرف الPeer')
    is_connected = models.BooleanField(default=False, verbose_name='متصل حالياً')
    joined_at = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الانضمام')
    left_at = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ المغادرة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'مشارك في المكالمة'
        verbose_name_plural = 'مشاركو المكالمات'
        unique_together = ['session', 'user']
        indexes = [
            models.Index(fields=['session', 'user']),
            models.Index(fields=['user', 'is_connected']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} in call #{self.session_id}"

    def mark_connected(self, peer_id: str | None = None):
        self.is_connected = True
        self.joined_at = timezone.now()
        if peer_id:
            self.peer_id = peer_id
        self.save(update_fields=['is_connected', 'joined_at', 'peer_id'])

    def mark_disconnected(self):
        self.is_connected = False
        self.left_at = timezone.now()
        self.save(update_fields=['is_connected', 'left_at'])