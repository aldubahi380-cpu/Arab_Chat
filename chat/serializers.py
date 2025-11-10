from rest_framework import serializers
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import (
    UserProfile, ChatRoom, Message, MessageRead,
    OTPVerification, FriendRequest, Friend, BlockedUser,
    Story, StoryView, Contact, DeviceToken, RecentContact,
    SessionDevice, CallSession, CallParticipant
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer للمستخدم"""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'phone': profile.phone,
                'avatar': profile.avatar.url if profile.avatar else None,
                'cover_image': profile.cover_image.url if profile.cover_image else None,
                'bio': profile.bio,
                'is_online': profile.is_online,
                'last_seen': profile.last_seen,
            }
        except UserProfile.DoesNotExist:
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer لملف المستخدم"""
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    cover_image = serializers.ImageField(required=False, allow_null=True)
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'username', 'phone', 'avatar', 'cover_image', 'cover_image_url', 'bio', 'is_online', 'last_seen', 'created_at']
        read_only_fields = ['id', 'created_at', 'cover_image_url']

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            url = obj.cover_image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer لغرفة الدردشة"""
    created_by = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'description', 'is_private', 'created_by', 'members', 
                  'member_count', 'last_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.first()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content[:100],
                'sender': last_msg.sender.username,
                'created_at': last_msg.created_at,
            }
        return None


class MessageSerializer(serializers.ModelSerializer):
    """Serializer للرسائل"""
    sender = UserSerializer(read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    read_by = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    original_available = serializers.SerializerMethodField()
    original_download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'content', 'message_type', 'file', 
                  'file_url', 'file_name', 'file_size', 'original_available', 'original_download_url',
                  'is_read', 'read_by', 'is_edited', 'edited_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_read', 'is_edited', 'edited_at', 'created_at', 'updated_at']
    
    def get_read_by(self, obj):
        return [mr.user.username for mr in obj.read_by.all()]
    
    def get_file_url(self, obj):
        """الحصول على رابط الملف"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_name(self, obj):
        """الحصول على اسم الملف"""
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None
    
    def get_file_size(self, obj):
        """الحصول على حجم الملف بالبايت"""
        if obj.file:
            try:
                return obj.file.size
            except:
                return None
        return None

    def get_original_available(self, obj):
        return bool(getattr(obj, 'original_file', None))

    def get_original_download_url(self, obj):
        if not getattr(obj, 'original_file', None):
            return None
        request = self.context.get('request')
        if not request:
            return None
        try:
            return reverse('message-download-original', kwargs={'pk': obj.pk}, request=request)
        except Exception:
            return None


class MessageReadSerializer(serializers.ModelSerializer):
    """Serializer لتتبع قراءة الرسائل"""
    user = UserSerializer(read_only=True)
    message = MessageSerializer(read_only=True)
    
    class Meta:
        model = MessageRead
        fields = ['id', 'message', 'user', 'read_at']
        read_only_fields = ['id', 'read_at']


class OTPVerificationSerializer(serializers.ModelSerializer):
    """Serializer لرمز التحقق OTP"""
    
    class Meta:
        model = OTPVerification
        fields = ['id', 'phone', 'otp_code', 'is_verified', 'expires_at', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at', 'expires_at']


class FriendRequestSerializer(serializers.ModelSerializer):
    """Serializer لطلبات الصداقة"""
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FriendSerializer(serializers.ModelSerializer):
    """Serializer للصداقات"""
    user = UserSerializer(read_only=True)
    friend = UserSerializer(read_only=True)
    
    class Meta:
        model = Friend
        fields = ['id', 'user', 'friend', 'created_at']
        read_only_fields = ['id', 'created_at']


class BlockedUserSerializer(serializers.ModelSerializer):
    """Serializer للمستخدمين المحظورين"""
    user = UserSerializer(read_only=True)
    blocked_user = UserSerializer(read_only=True)
    
    class Meta:
        model = BlockedUser
        fields = ['id', 'user', 'blocked_user', 'created_at']
        read_only_fields = ['id', 'created_at']


class StorySerializer(serializers.ModelSerializer):
    """Serializer للاستوريات"""
    user = UserSerializer(read_only=True)
    is_viewed = serializers.SerializerMethodField()
    viewers_count = serializers.SerializerMethodField()
    content_url = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'user', 'content_type', 'content', 'content_url',
            'text_content', 'background_color', 'font_color',
            'caption', 'expires_at', 'time_remaining',
            'views_count', 'viewers_count', 'is_viewed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'views_count', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        content_type = attrs.get('content_type') or getattr(self.instance, 'content_type', None)
        content = attrs.get('content', getattr(self.instance, 'content', None))
        text_content = attrs.get('text_content') or getattr(self.instance, 'text_content', None)

        if not content_type:
            content_type = 'image'

        if content_type == 'text':
            if not text_content or not text_content.strip():
                raise serializers.ValidationError({'text_content': 'المحتوى النصي مطلوب للاستوري النصي.'})
            # في الاستوري النصي، لا نحتاج إلى ملف
            attrs['content'] = None
        else:
            if not content:
                raise serializers.ValidationError({'content': 'يجب إرفاق صورة أو فيديو للاستوري.'})
            file_obj = attrs.get('content')
            if file_obj and hasattr(file_obj, 'content_type'):
                content_type_header = file_obj.content_type or ''
                if content_type == 'image' and not content_type_header.startswith('image/'):
                    raise serializers.ValidationError({'content': 'يجب أن يكون الملف صورة صالحة.'})
                if content_type == 'video' and not content_type_header.startswith('video/'):
                    raise serializers.ValidationError({'content': 'يجب أن يكون الملف فيديو صالح.'})

        return super().validate(attrs)
    
    def get_is_viewed(self, obj):
        viewed_story_ids = self.context.get('viewed_story_ids')
        if viewed_story_ids is not None:
            return obj.id in viewed_story_ids

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryView.objects.filter(story=obj, user=request.user).exists()
        return False
    
    def get_viewers_count(self, obj):
        return obj.views.count()

    def get_content_url(self, obj):
        if not obj.content:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.content.url)
        return obj.content.url

    def get_time_remaining(self, obj):
        return obj.seconds_until_expiry()


class StoryViewSerializer(serializers.ModelSerializer):
    """Serializer لمشاهدات الاستوريات"""
    story = StorySerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StoryView
        fields = ['id', 'story', 'user', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer لجهات الاتصال"""
    user = UserSerializer(read_only=True)
    registered_user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = ['id', 'user', 'phone', 'name', 'is_registered', 
                  'registered_user', 'registered_user_info', 'synced_at', 'created_at']
        read_only_fields = ['id', 'synced_at', 'created_at']
    
    def get_registered_user_info(self, obj):
        if obj.registered_user:
            return UserSerializer(obj.registered_user).data
        return None


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer لرموز الأجهزة (FCM Tokens)"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DeviceToken
        fields = ['id', 'user', 'token', 'device_type', 'device_id', 
                  'device_name', 'is_active', 'last_used', 'created_at']
        read_only_fields = ['id', 'user', 'last_used', 'created_at']
    
    def create(self, validated_data):
        # تعيين المستخدم من request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SessionDeviceSerializer(serializers.ModelSerializer):
    """Serializer لجلسات الأجهزة"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = SessionDevice
        fields = [
            'id', 'user', 'session_token', 'device_id', 'device_name',
            'platform', 'user_agent', 'ip_address', 'is_active',
            'expires_at', 'last_seen', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'session_token', 'device_id', 'user_agent',
            'ip_address', 'expires_at', 'last_seen', 'created_at'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        device_name = validated_data.get('device_name') or (request.META.get('HTTP_X_DEVICE_NAME') if request else None)
        platform = validated_data.get('platform') or (request.META.get('HTTP_X_DEVICE_PLATFORM') if request else None)

        session_device = SessionDevice.issue_for_request(
            user=request.user,
            request=request,
            device_id=self.initial_data.get('device_id'),
            device_name=device_name,
            platform=platform
        )

        return session_device

class RecentContactSerializer(serializers.ModelSerializer):
    """Serializer للمستخدمين المتواصل معهم"""
    contact_user = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RecentContact
        fields = ['id', 'user', 'contact_user', 'last_message_time', 
                  'message_count', 'last_message', 'unread_count', 'created_at']
        read_only_fields = ['id', 'user', 'last_message_time', 'message_count', 'created_at']
    
    def get_last_message(self, obj):
        """الحصول على آخر رسالة بين المستخدمين"""
        from .models import ChatRoom, Message
        try:
            # البحث عن غرفة محادثة خاصة بين المستخدمين
            room = ChatRoom.objects.filter(
                is_private=True,
                members=obj.user
            ).filter(members=obj.contact_user).annotate(
                member_count=Count('members')
            ).filter(member_count=2).first()
            
            if room:
                last_message = Message.objects.filter(room=room).order_by('-created_at').first()
                if last_message:
                    return {
                        'id': last_message.id,
                        'content': last_message.content[:100],
                        'sender_id': last_message.sender.id,
                        'sender_username': last_message.sender.username,
                        'created_at': last_message.created_at.isoformat(),
                    }
        except:
            pass
        return None
    
    def get_unread_count(self, obj):
        """حساب عدد الرسائل غير المقروءة"""
        from .models import ChatRoom, Message
        room = ChatRoom.objects.filter(
            is_private=True,
            members=obj.user
        ).filter(members=obj.contact_user).annotate(
            member_count=Count('members')
        ).filter(member_count=2).first()

        if room:
            return Message.objects.filter(
                room=room
            ).exclude(
                read_by__user=obj.user
            ).count()


class CallParticipantSerializer(serializers.ModelSerializer):
    """Serializer لمشاركي جلسة المكالمة"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = CallParticipant
        fields = [
            'id',
            'user',
            'role',
            'peer_id',
            'is_connected',
            'joined_at',
            'left_at',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'joined_at', 'left_at', 'created_at']


class CallSessionSerializer(serializers.ModelSerializer):
    """Serializer لجلسة المكالمة"""
    room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    initiator = UserSerializer(read_only=True)
    participants = CallParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = CallSession
        fields = [
            'id',
            'room',
            'initiator',
            'call_type',
            'status',
            'end_reason',
            'started_at',
            'ended_at',
            'created_at',
            'updated_at',
            'participants',
        ]
        read_only_fields = [
            'id',
            'initiator',
            'status',
            'end_reason',
            'started_at',
            'ended_at',
            'created_at',
            'updated_at',
            'participants',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError('يجب تسجيل الدخول لبدء المكالمة.')

        call_session = CallSession.objects.create(
            initiator=user,
            **validated_data
        )

        # إضافة المنشئ كمشارك
        CallParticipant.objects.create(
            session=call_session,
            user=user,
            role=CallParticipant.Role.CALLER,
            is_connected=False,
        )
        return call_session

