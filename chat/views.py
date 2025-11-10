import logging
from pathlib import Path

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.db import transaction
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.conf import settings
from django.http import FileResponse
from .models import (
    UserProfile, ChatRoom, Message, MessageRead, SessionDevice,
    CallSession, CallParticipant, BlockedUser
)
from .serializers import (
    UserSerializer, UserProfileSerializer, ChatRoomSerializer,
    MessageSerializer, MessageReadSerializer,
    CallSessionSerializer
)
from .media_utils import (
    compress_image,
    compress_video,
    ImageCompressionConfig,
    VideoCompressionConfig,
    IMAGE_CONFIG,
    VIDEO_CONFIG,
)
from .tasks import send_message_notification_task
from .tasks import send_call_invite_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet للمستخدمين"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def me(self, request):
        """الحصول على معلومات المستخدم الحالي"""
        # التحقق من token إذا كان موجود
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            # محاولة التحقق من token في header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Token '):
                token = auth_header.split(' ')[1]
                try:
                    token_obj = Token.objects.get(key=token)
                    serializer = self.get_serializer(token_obj.user)
                    return Response(serializer.data)
                except Token.DoesNotExist:
                    return Response({'error': 'Token غير صالح'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'error': 'يجب تسجيل الدخول'}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['get'])
    def auth_token(self, request):
        """الحصول على أو إنشاء auth token للمستخدم الحالي"""
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({
            'token': token.key,
            'created': created
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """تسجيل خروج الجهاز الحالي مع تعطيل session token"""
        session_token = request.data.get('session_token') or request.COOKIES.get('session_token')
        device_id = request.data.get('device_id') or request.COOKIES.get('session_device_id')

        if session_token and device_id:
            SessionDevice.objects.filter(
                user=request.user,
                session_token=session_token,
                device_id=device_id
            ).update(is_active=False, expires_at=timezone.now())

        logout(request)

        response = Response({'success': True})
        response.delete_cookie('session_token')
        response.delete_cookie('session_device_id')
        response.delete_cookie('auth_token')
        return response

    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """حذف حساب المستخدم بالكامل من السيرفر وقاعدة البيانات"""
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'success': False, 'error': 'يجب تسجيل الدخول'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        username = user.username
        import logging
        logger = logging.getLogger(__name__)

        try:
            with transaction.atomic():
                # حذف الرسائل وسجلات القراءة
                Message.objects.filter(sender=user).delete()
                MessageRead.objects.filter(user=user).delete()

                # تنظيف الغرف المرتبطة بالمستخدم
                from .models import ChatRoom
                rooms_created = ChatRoom.objects.filter(created_by=user)
                for room in rooms_created:
                    if room.is_private and room.members.count() == 2:
                        room.delete()
                    else:
                        room.members.remove(user)
                        if room.members.count() == 0:
                            room.delete()

                rooms_member = ChatRoom.objects.filter(members=user).exclude(created_by=user)
                for room in rooms_member:
                    room.members.remove(user)
                    if room.is_private and room.members.count() <= 1:
                        room.delete()

                # حذف العلاقات الاجتماعية وسجلات القبول
                from .models import (
                    FriendRequest, Friend, BlockedUser,
                    Story, StoryView, Contact, RecentContact,
                    DeviceToken, OTPVerification
                )

                FriendRequest.objects.filter(from_user=user).delete()
                FriendRequest.objects.filter(to_user=user).delete()
                Friend.objects.filter(user=user).delete()
                Friend.objects.filter(friend=user).delete()
                BlockedUser.objects.filter(user=user).delete()
                BlockedUser.objects.filter(blocked_user=user).delete()

                Story.objects.filter(user=user).delete()
                StoryView.objects.filter(user=user).delete()

                Contact.objects.filter(user=user).delete()
                Contact.objects.filter(registered_user=user).update(registered_user=None, is_registered=False)

                RecentContact.objects.filter(user=user).delete()
                RecentContact.objects.filter(contact_user=user).delete()

                DeviceToken.objects.filter(user=user).delete()
                SessionDevice.objects.filter(user=user).delete()

                # حذف سجلات OTP المرتبطة برقم المستخدم إن وجدت
                try:
                    profile = user.profile
                except UserProfile.DoesNotExist:  # type: ignore[attr-defined]
                    profile = None
                if profile and profile.phone:
                    OTPVerification.objects.filter(phone=profile.phone).delete()

                # إزالة رموز المصادقة وتسجيل الخروج
                Token.objects.filter(user=user).delete()
                logout(request)

                # حذف المستخدم (سيحذف UserProfile تلقائياً بفضل CASCADE)
                user.delete()

            return Response({
                'message': f'تم حذف الحساب "{username}" بنجاح من السيرفر وقاعدة البيانات',
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error('Error deleting account for %s: %s', username, exc)
            return Response({
                'error': f'حدث خطأ أثناء حذف الحساب: {exc}',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """البحث عن المستخدمين"""
        query = request.query_params.get('q', '')
        if query:
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )[:20]
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response([])
    
class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet لملفات المستخدمين"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """الحصول على أو تحديث ملف المستخدم الحالي"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if request.method == 'PUT':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            avatar_file = request.FILES.get('avatar')
            cover_file = request.FILES.get('cover_image')
            save_kwargs = {}
            if avatar_file:
                try:
                    save_kwargs['avatar'] = self._compress_avatar(avatar_file)
                except Exception as exc:
                    raise serializers.ValidationError({'avatar': f'تعذر ضغط الصورة: {exc}'})
            if cover_file:
                try:
                    save_kwargs['cover_image'] = self._compress_cover(cover_file)
                except Exception as exc:
                    raise serializers.ValidationError({'cover_image': f'تعذر معالجة صورة الغلاف: {exc}'})
            serializer.save(**save_kwargs)
            return Response(serializer.data)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def perform_update(self, serializer):
        avatar_file = self.request.FILES.get('avatar')
        cover_file = self.request.FILES.get('cover_image')
        save_kwargs = {}
        if avatar_file:
            try:
                save_kwargs['avatar'] = self._compress_avatar(avatar_file)
            except Exception as exc:
                raise serializers.ValidationError({'avatar': f'تعذر ضغط الصورة: {exc}'})
        if cover_file:
            try:
                save_kwargs['cover_image'] = self._compress_cover(cover_file)
            except Exception as exc:
                raise serializers.ValidationError({'cover_image': f'تعذر معالجة صورة الغلاف: {exc}'})
        serializer.save(**save_kwargs)

    def perform_create(self, serializer):
        avatar_file = self.request.FILES.get('avatar')
        cover_file = self.request.FILES.get('cover_image')
        save_kwargs = {'user': self.request.user}
        if avatar_file:
            try:
                save_kwargs['avatar'] = self._compress_avatar(avatar_file)
            except Exception as exc:
                raise serializers.ValidationError({'avatar': f'تعذر ضغط الصورة: {exc}'})
        if cover_file:
            try:
                save_kwargs['cover_image'] = self._compress_cover(cover_file)
            except Exception as exc:
                raise serializers.ValidationError({'cover_image': f'تعذر معالجة صورة الغلاف: {exc}'})
        serializer.save(**save_kwargs)

    @staticmethod
    def _compress_avatar(avatar_file):
        avatar_config = ImageCompressionConfig(
            max_edge=min(IMAGE_CONFIG.max_edge, 1080),
            quality=min(IMAGE_CONFIG.quality + 2, 92),
            min_quality=max(IMAGE_CONFIG.min_quality, 78),
            target_max_kb=min(IMAGE_CONFIG.target_max_kb, 450),
            target_min_kb=IMAGE_CONFIG.target_min_kb,
            allow_webp=IMAGE_CONFIG.allow_webp,
        )
        compressed_avatar, _ = compress_image(avatar_file, config=avatar_config)
        return compressed_avatar

    @staticmethod
    def _compress_cover(cover_file):
        cover_config = ImageCompressionConfig(
            max_edge=min(IMAGE_CONFIG.max_edge * 2, 2048),
            quality=min(IMAGE_CONFIG.quality + 4, 94),
            min_quality=max(IMAGE_CONFIG.min_quality, 75),
            target_max_kb=min(IMAGE_CONFIG.target_max_kb * 2, 900),
            target_min_kb=IMAGE_CONFIG.target_min_kb,
            allow_webp=True,
        )
        compressed_cover, _ = compress_image(cover_file, config=cover_config)
        return compressed_cover
    
    @action(detail=True, methods=['post'])
    def set_online(self, request, pk=None):
        """تحديد حالة الاتصال"""
        profile = self.get_object()
        profile.is_online = True
        profile.last_seen = timezone.now()
        profile.save()
        return Response({'status': 'online'})
    
    @action(detail=True, methods=['post'])
    def set_offline(self, request, pk=None):
        """تحديد حالة عدم الاتصال"""
        profile = self.get_object()
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save()
        return Response({'status': 'offline'})


class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet لغرف الدردشة"""
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على غرف المستخدم والمجموعات العامة"""
        user = self.request.user
        
        # غرف المستخدم (خاصة وعامة)
        user_rooms = ChatRoom.objects.filter(members=user).distinct()
        
        # المجتمعات العامة (للعرض فقط)
        public_groups = ChatRoom.objects.filter(room_type=ChatRoom.ROOM_TYPE_COMMUNITY).distinct()
        
        # دمج النتائج
        return (user_rooms | public_groups).distinct()
    
    def perform_create(self, serializer):
        """إنشاء غرفة جديدة"""
        room_type = serializer.validated_data.get('room_type', ChatRoom.ROOM_TYPE_COMMUNITY)
        room = serializer.save(created_by=self.request.user, room_type=room_type)
        room.members.add(self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """إضافة عضو إلى الغرفة"""
        room = self.get_object()
        if room.created_by != request.user:
            return Response({'error': 'فقط المنشئ يمكنه إضافة الأعضاء'}, status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                room.members.add(user)
                return Response({'status': 'member added'})
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_members(self, request, pk=None):
        """إضافة عدة أعضاء دفعة واحدة (للمجموعات)"""
        room = self.get_object()
        if room.created_by != request.user:
            return Response({'error': 'فقط المنشئ يمكنه إدارة الأعضاء'}, status=status.HTTP_403_FORBIDDEN)
        user_ids = request.data.get('user_ids') or []
        if isinstance(user_ids, str):
            user_ids = [uid for uid in user_ids.split(',') if uid]
        added = []
        errors = []
        for uid in user_ids:
            try:
                user = User.objects.get(id=uid)
                room.members.add(user)
                added.append(user.id)
            except User.DoesNotExist:
                errors.append(uid)
        return Response({'added': added, 'errors': errors})

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """إزالة عضو من الغرفة"""
        room = self.get_object()
        if room.created_by != request.user:
            return Response({'error': 'فقط المنشئ يمكنه إزالة الأعضاء'}, status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                room.members.remove(user)
                return Response({'status': 'member removed'})
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def regenerate_invite(self, request, pk=None):
        """إعادة توليد رابط الدعوة"""
        room = self.get_object()
        if room.created_by != request.user or room.room_type != ChatRoom.ROOM_TYPE_GROUP:
            return Response({'error': 'لا تملك صلاحية هذا الإجراء'}, status=status.HTTP_403_FORBIDDEN)
        room.invite_code = None
        room.save(update_fields=['invite_code', 'is_private', 'updated_at'])
        serializer = self.get_serializer(room)
        return Response({'invite_code': room.invite_code, 'invite_link': serializer.data.get('invite_link')})

    @action(detail=False, methods=['get'])
    def my_rooms(self, request):
        """الحصول على غرف المستخدم"""
        rooms = self.get_queryset()
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def chat_list_updates(self, request):
        """الحصول على تحديثات قائمة الدردشات - للاستدعاء الفوري"""
        from django.db.models import Max
        user = request.user
        
        # الحصول على جميع الغرف الخاصة مع آخر رسالة
        private_rooms = ChatRoom.objects.filter(
            members=user,
            is_private=True
        ).annotate(
            member_count=Count('members'),
            last_message_time=Max('messages__created_at')
        ).filter(
            member_count=2
        ).prefetch_related('members')
        
        rooms_data = []
        for room in private_rooms:
            other_member = room.members.exclude(id=user.id).first()
            if not other_member:
                continue
            
            last_message = Message.objects.filter(room=room).order_by('-created_at').first()
            unread_count = Message.objects.filter(
                room=room
            ).exclude(
                read_by__user=user
            ).count()
            
            rooms_data.append({
                'room_id': room.id,
                'other_member_id': other_member.id,
                'other_member_username': other_member.username,
                'other_member_avatar': other_member.profile.avatar.url if hasattr(other_member, 'profile') and other_member.profile.avatar else None,
                'is_online': other_member.profile.is_online if hasattr(other_member, 'profile') else False,
                'last_message': {
                    'id': last_message.id if last_message else None,
                    'content': last_message.content[:100] if last_message else None,
                    'sender_id': last_message.sender.id if last_message else None,
                    'sender_username': last_message.sender.username if last_message else None,
                    'created_at': last_message.created_at.isoformat() if last_message else None,
                },
                'unread_count': unread_count,
                'updated_at': room.updated_at.isoformat(),
                'sort_time': last_message.created_at.isoformat() if last_message else room.updated_at.isoformat()
            })
        
        # ترتيب حسب آخر رسالة
        rooms_data.sort(key=lambda x: x['sort_time'], reverse=True)
        
        return Response({
            'rooms': rooms_data,
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def public_groups(self, request):
        """الحصول على جميع المجموعات العامة"""
        groups = ChatRoom.objects.filter(room_type=ChatRoom.ROOM_TYPE_COMMUNITY).annotate(
            member_count=Count('members')
        ).order_by('-created_at')
        serializer = self.get_serializer(groups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """الانضمام إلى مجتمع عام"""
        room = self.get_object()
        
        if room.room_type != ChatRoom.ROOM_TYPE_COMMUNITY:
            return Response({'error': 'الانضمام المباشر متاح للمجتمعات العامة فقط'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user in room.members.all():
            return Response({'status': 'already_member', 'message': 'أنت عضو بالفعل في هذا المجتمع'})
        
        room.members.add(request.user)
        serializer = self.get_serializer(room)
        return Response({'status': 'joined', 'room': serializer.data})
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """مغادرة مجتمع عام"""
        room = self.get_object()
        
        if room.room_type != ChatRoom.ROOM_TYPE_COMMUNITY:
            return Response({'error': 'لا يمكن مغادرة المجموعة عبر هذا المسار'}, status=status.HTTP_400_BAD_REQUEST)
 
        if request.user not in room.members.all():
            return Response({'error': 'أنت لست عضواً في هذا المجتمع'}, status=status.HTTP_400_BAD_REQUEST)
        
        # لا يمكن للمنشئ مغادرة المجموعة إلا إذا كان آخر عضو
        if room.created_by == request.user and room.members.count() == 1:
            room.delete()
            return Response({'status': 'deleted', 'message': 'تم حذف المجموعة'})
        elif room.created_by == request.user:
            return Response({'error': 'لا يمكن للمنشئ مغادرة المجتمع. يجب تعيين منشئ جديد أولاً'}, status=status.HTTP_400_BAD_REQUEST)
        
        room.members.remove(request.user)
        return Response({'status': 'left', 'message': 'تم مغادرة المجموعة'})

    @action(detail=False, methods=['post'])
    def join_by_code(self, request):
        """الانضمام إلى مجموعة عبر رمز الدعوة"""
        code = (request.data.get('invite_code') or '').strip()
        if not code:
            return Response({'error': 'رمز الدعوة مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            room = ChatRoom.objects.get(invite_code=code, room_type=ChatRoom.ROOM_TYPE_GROUP)
        except ChatRoom.DoesNotExist:
            return Response({'error': 'رمز الدعوة غير صالح أو المجموعة غير متاحة'}, status=status.HTTP_404_NOT_FOUND)
        if request.user in room.members.all():
            serializer = self.get_serializer(room)
            return Response({'status': 'already_member', 'room': serializer.data})
        room.members.add(request.user)
        serializer = self.get_serializer(room)
        return Response({'status': 'joined', 'room': serializer.data})


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet للرسائل"""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    MIN_AUDIO_BYTES = 2048

    def get_queryset(self):
        """الحصول على رسائل المستخدم فقط (استثناء المحذوفة)"""
        user = self.request.user
        # الحصول على الغرف التي المستخدم عضو فيها
        user_rooms = ChatRoom.objects.filter(members=user)
        queryset = Message.objects.filter(
            room__in=user_rooms,
            is_deleted=False  # استثناء الرسائل المحذوفة
        ).select_related('sender', 'room')
        
        # تصفية حسب الغرفة إذا كانت موجودة
        room_id = self.request.query_params.get('room')
        if room_id:
            # التحقق من أن المستخدم عضو في الغرفة
            try:
                room = ChatRoom.objects.get(id=room_id, members=user)
                queryset = queryset.filter(room=room)
            except ChatRoom.DoesNotExist:
                return Message.objects.none()
        
        return queryset.order_by('-created_at')
    
    def destroy(self, request, *args, **kwargs):
        """حذف رسالة (فقط المرسل يمكنه الحذف) - حذف ناعم"""
        message = self.get_object()
        
        # التحقق من أن المستخدم هو المرسل
        if message.sender != request.user:
            return Response(
                {'error': '❌ يمكنك حذف رسائلك فقط', 'success': False},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # حذف ناعم (Soft Delete) - إخفاء الرسالة بدلاً من حذفها
        from django.utils import timezone
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.content = '[تم حذف هذه الرسالة]'
        message.save()
        
        # حذف الملف من السيرفر إذا كان موجوداً
        if message.file:
            try:
                message.file.delete(save=False)
                message.file = None
                message.save()
            except:
                pass
        
        return Response({
            'message': '✅ تم حذف الرسالة بنجاح',
            'message_id': message.id,
            'success': True
        })

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """تعديل رسالة نصية خاصة بالمرسل"""
        message = self.get_object()

        if message.sender != request.user:
            return Response(
                {'error': '❌ يمكنك تعديل رسائلك فقط', 'success': False},
                status=status.HTTP_403_FORBIDDEN
            )

        if message.is_deleted:
            return Response(
                {'error': 'لا يمكن تعديل رسالة محذوفة', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        if message.message_type != 'text':
            return Response(
                {'error': 'يمكن تعديل الرسائل النصية فقط', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        content = request.data.get('content')
        if content is None:
            return Response(
                {'error': 'يجب إرسال محتوى الرسالة', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        content = str(content).strip()
        if not content:
            return Response(
                {'error': 'الرسالة لا يمكن أن تكون فارغة', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(content) > 1000:
            return Response(
                {'error': 'الرسالة طويلة جداً', 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        if content == message.content:
            serializer = self.get_serializer(message)
            return Response({'success': False, 'message': serializer.data, 'warning': 'لم يتم تعديل الرسالة'})

        message.content = content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save(update_fields=['content', 'is_edited', 'edited_at', 'updated_at'])

        serializer = self.get_serializer(message)

        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{message.room.id}',
                    {
                        'type': 'message_updated',
                        'message_id': message.id,
                        'content': message.content,
                        'sender_id': message.sender_id,
                        'edited_at': message.edited_at.isoformat() if message.edited_at else '',
                        'message_type': message.message_type,
                    }
                )
            except Exception:
                logger.exception('Failed to broadcast message update for message %s', message.id)

        return Response({'success': True, 'message': serializer.data})
    
    @action(detail=True, methods=['delete'])
    def delete_message(self, request, pk=None):
        """حذف رسالة (endpoint بديل)"""
        return self.destroy(request, pk=pk)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """البحث في المحادثات"""
        query = request.query_params.get('q', '').strip()
        room_id = request.query_params.get('room')
        
        if not query:
            return Response({
                'error': 'يجب إدخال نص للبحث',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not room_id:
            return Response({
                'error': 'يجب تحديد رقم الغرفة',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
        except ChatRoom.DoesNotExist:
            return Response({
                'error': 'الغرفة غير موجودة أو ليس لديك صلاحية للوصول إليها',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # البحث في محتوى الرسائل
        messages = Message.objects.filter(
            room=room,
            content__icontains=query
        ).select_related('sender').order_by('-created_at')[:50]
        
        serializer = self.get_serializer(messages, many=True)
        
        return Response({
            'messages': serializer.data,
            'count': len(serializer.data),
            'query': query,
            'success': True
        })
    
    @action(detail=False, methods=['get'])
    def poll_new(self, request):
        """Polling للحصول على الرسائل الجديدة"""
        room_id = request.query_params.get('room_id')
        last_message_id = request.query_params.get('last_message_id', 0)
        
        try:
            last_message_id = int(last_message_id)
        except (ValueError, TypeError):
            last_message_id = 0
        
        if not room_id:
            return Response({'error': 'room_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
        except ChatRoom.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # الحصول على الرسائل الجديدة بعد last_message_id
        new_messages = Message.objects.filter(
            room=room,
            id__gt=last_message_id
        ).select_related('sender').order_by('created_at')
        
        serializer = self.get_serializer(new_messages, many=True)
        return Response({
            'messages': serializer.data,
            'count': new_messages.count()
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """الحصول على عدد الرسائل غير المقروءة في غرفة"""
        room_id = request.query_params.get('room')
        
        if not room_id:
            return Response({
                'error': 'room parameter is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
        except ChatRoom.DoesNotExist:
            return Response({
                'error': 'Room not found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        unread_count = Message.objects.filter(
            room=room
        ).exclude(
            read_by__user=request.user
        ).count()
        
        # الحصول على آخر رسالة غير مقروءة
        last_unread = Message.objects.filter(
            room=room
        ).exclude(
            read_by__user=request.user
        ).order_by('-created_at').first()
        
        return Response({
            'room_id': room_id,
            'unread_count': unread_count,
            'last_unread_message_id': last_unread.id if last_unread else None,
            'last_unread_time': last_unread.created_at.isoformat() if last_unread else None,
            'success': True
        })
    
    @action(detail=False, methods=['get'])
    def read_status(self, request):
        """الحصول على حالة قراءة الرسائل في غرفة"""
        room_id = request.query_params.get('room')
        
        if not room_id:
            return Response({
                'error': 'room parameter is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
        except ChatRoom.DoesNotExist:
            return Response({
                'error': 'Room not found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # الحصول على آخر 50 رسالة مع حالة القراءة
        messages = Message.objects.filter(
            room=room
        ).select_related('sender').prefetch_related('read_by').order_by('-created_at')[:50]
        
        messages_data = []
        for msg in messages:
            is_read_by_me = msg.read_by.filter(user=request.user).exists()
            read_by_count = msg.read_by.count()
            total_members = room.members.count()
            
            messages_data.append({
                'id': msg.id,
                'content': msg.content[:100],
                'sender_id': msg.sender.id,
                'sender_username': msg.sender.username,
                'message_type': msg.message_type,
                'is_read_by_me': is_read_by_me,
                'read_by_count': read_by_count,
                'total_members': total_members,
                'is_read_by_all': read_by_count >= total_members,
                'created_at': msg.created_at.isoformat()
            })
        
        return Response({
            'room_id': room_id,
            'messages': messages_data,
            'success': True
        })
    
    def perform_create(self, serializer):
        """إنشاء رسالة جديدة مع دعم الملفات"""
        room = serializer.validated_data.get('room')
        message_type = serializer.validated_data.get('message_type', 'text')
        file = serializer.validated_data.get('file')
        
        # التحقق من نوع الرسالة والملف
        if message_type in ['image', 'file', 'audio', 'video'] and not file:
            raise serializers.ValidationError({
                'file': f'يجب إرفاق ملف للرسائل من نوع {message_type}'
            })
        
        # تحديد نوع الرسالة تلقائياً بناءً على الملف
        if file and message_type == 'text':
            if hasattr(file, 'content_type'):
                content_type = file.content_type
                if content_type and content_type.startswith('image/'):
                    serializer.validated_data['message_type'] = 'image'
                elif content_type and content_type.startswith('video/'):
                    serializer.validated_data['message_type'] = 'video'
                elif content_type and content_type.startswith('audio/'):
                    serializer.validated_data['message_type'] = 'audio'
                else:
                    serializer.validated_data['message_type'] = 'file'
        
        # التحقق من أن الغرفة موجودة والمستخدم عضو فيها
        if isinstance(room, ChatRoom):
            # إذا كانت room كائن ChatRoom، التحقق من العضوية
            if self.request.user not in room.members.all():
                raise serializers.ValidationError({'room': 'لست عضواً في هذه الغرفة'})
            final_room = room
        else:
            # إذا كان room هو ID (int)، محاولة العثور على الغرفة
            try:
                final_room = ChatRoom.objects.get(id=room, members=self.request.user)
                serializer.validated_data['room'] = final_room
            except ChatRoom.DoesNotExist:
                # إذا لم توجد الغرفة، ربما يكون room_id هو ID مستخدم
                # إنشاء غرفة خاصة مع هذا المستخدم
                try:
                    target_user = User.objects.get(id=room)
                    if target_user == self.request.user:
                        raise serializers.ValidationError({'room': 'لا يمكنك إرسال رسالة لنفسك'})
                    final_room = self.get_or_create_private_room(self.request.user, target_user)
                    serializer.validated_data['room'] = final_room
                except User.DoesNotExist:
                    raise serializers.ValidationError({'room': 'الغرفة أو المستخدم غير موجود'})
        
        compressed_upload = None
        if file:
            try:
                if serializer.validated_data.get('message_type') == 'image':
                    compressed_upload, _ = compress_image(file)
                elif serializer.validated_data.get('message_type') == 'video':
                    compressed_upload, _ = compress_video(file)
            except RuntimeError as exc:
                raise serializers.ValidationError({'file': f'تعذر ضغط الفيديو: {exc}'})
            except Exception as exc:
                raise serializers.ValidationError({'file': f'خطأ في معالجة الملف: {exc}'})

        save_kwargs = {'sender': self.request.user}
        if compressed_upload:
            save_kwargs['file'] = compressed_upload

        with transaction.atomic():
            message = serializer.save(**save_kwargs)

            if message.message_type == 'audio' and message.file:
                if message.file.size is None or message.file.size < self.MIN_AUDIO_BYTES:
                    message.delete()
                    raise serializers.ValidationError({'file': 'الملف الصوتي قصير جداً أو لم يتم تسجيله بشكل صحيح. يرجى إعادة المحاولة.'})

            if file and serializer.validated_data.get('message_type') in ('image', 'video'):
                try:
                    file.seek(0)
                    message.original_file.save(getattr(file, 'name', f'original_{message.id}'), file, save=True)
                except Exception as exc:
                    logger.warning('Failed to store original media for message %s: %s', message.id, exc)

        # تحديث updated_at للغرفة لتحديث ترتيب القائمة
        from django.utils import timezone
        from .models import RecentContact
        
        final_room.updated_at = timezone.now()
        final_room.save(update_fields=['updated_at'])
        
        # إنشاء سجل قراءة للمرسل
        MessageRead.objects.get_or_create(message=message, user=self.request.user)
        
        # تحديث RecentContact للمستخدمين في المحادثة الخاصة
        if final_room.is_private and final_room.members.count() == 2:
            other_members = final_room.members.exclude(id=self.request.user.id)
            for other_user in other_members:
                # تحديث RecentContact للمرسل
                recent_contact, created = RecentContact.objects.get_or_create(
                    user=self.request.user,
                    contact_user=other_user
                )
                recent_contact.last_message_time = timezone.now()
                recent_contact.message_count += 1
                recent_contact.save(update_fields=['last_message_time', 'message_count'])
                
                # تحديث RecentContact للمستقبل أيضاً
                RecentContact.objects.update_or_create(
                    user=other_user,
                    contact_user=self.request.user,
                    defaults={
                        'last_message_time': timezone.now(),
                    }
                )
        
        # إرسال إشعار للمستخدمين الآخرين في الغرفة (تحديث قائمة الدردشات)
        self.send_notification_to_other_users(final_room, message)
    
    def get_serializer_context(self):
        """إضافة request إلى context للـ serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_or_create_private_room(self, user1, user2):
        """إنشاء أو العثور على غرفة محادثة خاصة بين مستخدمين"""
        from .models import RecentContact
        
        # البحث عن غرفة خاصة موجودة بين المستخدمين
        existing_rooms = ChatRoom.objects.filter(
            is_private=True,
            members=user1
        ).filter(members=user2).annotate(
            member_count=Count('members')
        ).filter(member_count=2)
        
        if existing_rooms.exists():
            return existing_rooms.first()
        
        # إنشاء غرفة جديدة
        room = ChatRoom.objects.create(
            name=f"{user1.username} - {user2.username}",
            is_private=True,
            created_by=user1
        )
        room.members.add(user1, user2)
        
        # إضافة إلى RecentContact
        RecentContact.objects.get_or_create(
            user=user1,
            contact_user=user2
        )
        RecentContact.objects.get_or_create(
            user=user2,
            contact_user=user1
        )
        
        return room
    
    def send_notification_to_other_users(self, room, message):
        """إرسال إشعار للمستخدمين الآخرين عند استقبال رسالة جديدة"""
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            # الحصول على جميع الأعضاء الآخرين في الغرفة
            other_members = room.members.exclude(id=message.sender.id)
            
            for member in other_members:
                # إرسال إشعار WebSocket لكل مستخدم
                user_group_name = f'user_{member.id}_notifications'
                async_to_sync(channel_layer.group_send)(
                    user_group_name,
                    {
                        'type': 'new_message_notification',
                        'room_id': room.id,
                        'message': message.content[:100],
                        'sender_id': message.sender.id,
                        'sender_username': message.sender.username,
                        'timestamp': message.created_at.isoformat(),
                        'message_id': message.id,
                    }
                )
                
                # إرسال تحديث قائمة الدردشات
                unread_count = Message.objects.filter(
                    room=room
                ).exclude(
                    read_by__user=member
                ).count()
                
                async_to_sync(channel_layer.group_send)(
                    user_group_name,
                    {
                        'type': 'chat_list_update',
                        'room_id': room.id,
                        'last_message': {
                            'id': message.id,
                            'content': message.content[:100],
                            'sender_id': message.sender.id,
                            'sender_username': message.sender.username,
                            'created_at': message.created_at.isoformat(),
                        },
                        'unread_count': unread_count,
                        'updated_at': room.updated_at.isoformat(),
                    }
                )
                
                # إرسال إشعار Push
                send_message_notification_task.delay(message.id, member.id)
        except Exception as e:
            # في حالة فشل إرسال الإشعار، لا نوقف العملية
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error sending notification: {e}')

    @action(detail=True, methods=['get'])
    def download_original(self, request, pk=None):
        """تحميل النسخة الأصلية للملف إن وجدت"""
        message = self.get_object()
        if not message.original_file:
            return Response({'error': 'لا توجد نسخة أصلية متاحة'}, status=status.HTTP_404_NOT_FOUND)

        filename = Path(message.original_file.name).name
        return FileResponse(message.original_file.open('rb'), as_attachment=True, filename=filename)
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request, pk=None):
        """تحديد الرسالة كمقروءة"""
        message = self.get_object()
        MessageRead.objects.get_or_create(message=message, user=request.user)
        message.is_read = True
        message.save()
        return Response({'status': 'marked as read'})
    
class MessageReadViewSet(viewsets.ModelViewSet):
    """ViewSet لتتبع قراءة الرسائل"""
    queryset = MessageRead.objects.all()
    serializer_class = MessageReadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على الرسائل المقروءة للمستخدم الحالي"""
        return MessageRead.objects.filter(user=self.request.user)


class CallSessionViewSet(viewsets.ModelViewSet):
    """إدارة جلسات المكالمات (صوت/فيديو)"""

    serializer_class = CallSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CallSession.objects.filter(
            Q(initiator=user) | Q(participants__user=user)
        ).select_related('room', 'initiator').prefetch_related('participants__user').distinct()

    def perform_create(self, serializer):
        room = serializer.validated_data.get('room')
        request_user = self.request.user

        if room is None or not room.members.filter(id=request_user.id).exists():
            raise serializers.ValidationError({
                'room': 'لا يمكنك بدء مكالمة في غرفة لست عضواً فيها.'
            })

        participant_ids = self._normalize_participant_ids(self.request.data.get('participants', []))
        allowed_participants = self._validate_participants(room, request_user, participant_ids)

        call_session = serializer.save()

        for participant_user in allowed_participants:
            participant, _ = CallParticipant.objects.get_or_create(
                session=call_session,
                user=participant_user,
                defaults={
                    'role': CallParticipant.Role.RECEIVER,
                    'is_connected': False,
                }
            )
            if participant_user.id != request_user.id:
                send_call_invite_task.delay(call_session.id, participant_user.id)

        call_session.activate()

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        call_session = self.get_object()
        if call_session.status not in (CallSession.Status.ACTIVE, CallSession.Status.PENDING):
            return Response({'error': 'لا يمكن دعوة مستخدمين بعد انتهاء المكالمة.'}, status=status.HTTP_400_BAD_REQUEST)

        participant_ids = self._normalize_participant_ids(request.data.get('participants', []))
        if not participant_ids:
            return Response({'error': 'لا يوجد مشاركون صالحون'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_participants = self._validate_participants(call_session.room, request.user, participant_ids)

        invited = []
        for participant_user in allowed_participants:
            participant, created = CallParticipant.objects.get_or_create(
                session=call_session,
                user=participant_user,
                defaults={'role': CallParticipant.Role.RECEIVER}
            )
            if created or not participant.is_connected:
                send_call_invite_task.delay(call_session.id, participant_user.id)
            invited.append(participant_user.id)

        serializer = self.get_serializer(call_session)
        return Response({'invited': invited, 'call': serializer.data})

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        call_session = self.get_object()
        if call_session.status not in (CallSession.Status.ACTIVE, CallSession.Status.PENDING):
            return Response({'error': 'لا يمكن الانضمام بسبب انتهاء المكالمة.'}, status=status.HTTP_400_BAD_REQUEST)

        call_session.activate()

        participant, _ = CallParticipant.objects.get_or_create(
            session=call_session,
            user=request.user,
            defaults={'role': CallParticipant.Role.RECEIVER}
        )
        peer_id = request.data.get('peer_id')
        participant.mark_connected(peer_id=peer_id)

        serializer = self.get_serializer(call_session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        call_session = self.get_object()
        try:
            participant = call_session.participants.get(user=request.user)
        except CallParticipant.DoesNotExist:
            return Response({'error': 'أنت لست مشاركاً في هذه المكالمة.'}, status=status.HTTP_404_NOT_FOUND)

        participant.mark_disconnected()

        if not call_session.participants.filter(is_connected=True).exists():
            call_session.end(reason=CallSession.EndReason.NO_PARTICIPANTS)

        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        call_session = self.get_object()
        if call_session.status in (CallSession.Status.ENDED, CallSession.Status.CANCELLED):
            return Response({'success': True})

        reason = request.data.get('reason') or CallSession.EndReason.NORMAL
        if reason not in CallSession.EndReason.values:
            reason = CallSession.EndReason.NORMAL

        call_session.end(reason=reason)
        return Response({'success': True})

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        call_session = self.get_object()
        serializer = self.get_serializer(call_session)
        return Response(serializer.data)

    @staticmethod
    def _normalize_participant_ids(raw_participants):
        if raw_participants is None:
            return set()
        if isinstance(raw_participants, (str, int)):
            raw_list = [raw_participants]
        else:
            raw_list = raw_participants

        normalized = set()
        for value in raw_list:
            if isinstance(value, int):
                normalized.add(value)
            else:
                str_value = str(value).strip()
                if str_value.isdigit():
                    normalized.add(int(str_value))
        return normalized

    def _validate_participants(self, room, request_user, participant_ids):
        participant_ids = set(participant_ids or set())
        participant_ids.discard(request_user.id)

        if not participant_ids:
            return []

        room_member_ids = set(
            room.members.filter(id__in=participant_ids).values_list('id', flat=True)
        )
        missing_ids = participant_ids - room_member_ids
        if missing_ids:
            raise serializers.ValidationError({
                'participants': 'يمكن دعوة أعضاء الغرفة فقط.'
            })

        blocked_q = BlockedUser.objects.filter(
            Q(user_id=request_user.id, blocked_user_id__in=participant_ids) |
            Q(user_id__in=participant_ids, blocked_user_id=request_user.id)
        )
        if blocked_q.exists():
            raise serializers.ValidationError({
                'participants': 'لا يمكن دعوة مستخدمين يوجد بينهم حظر.'
            })

        return list(User.objects.filter(id__in=room_member_ids, is_active=True))


def index_view(request):
    """الصفحة الرئيسية"""
    # إذا كان المستخدم مسجل دخول، توجيهه للـ dashboard
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard')
    
    # إذا لم يكن مسجل دخول، توجيهه لصفحة الشروط
    from django.shortcuts import redirect
    return redirect('terms')
