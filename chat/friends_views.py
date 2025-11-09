"""
Views لنظام الصداقات
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q
from .models import FriendRequest, Friend, BlockedUser
from .serializers import (
    FriendRequestSerializer, FriendSerializer, BlockedUserSerializer
)


class FriendRequestViewSet(viewsets.ModelViewSet):
    """ViewSet لطلبات الصداقة"""
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على طلبات الصداقة للمستخدم الحالي"""
        user = self.request.user
        return FriendRequest.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        )
    
    def perform_create(self, serializer):
        """إنشاء طلب صداقة"""
        to_user_id = self.request.data.get('to_user')
        from_user = self.request.user
        
        if not to_user_id:
            return Response(
                {'error': 'يجب تحديد المستخدم المرسل إليه'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'المستخدم غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # التحقق من أن المستخدم لا يرسل طلب لنفسه
        if from_user == to_user:
            return Response(
                {'error': 'لا يمكنك إرسال طلب صداقة لنفسك'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التحقق من وجود طلب مسبق
        existing_request = FriendRequest.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).first()
        
        if existing_request:
            return Response(
                {'error': 'يوجد طلب صداقة مسبق'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التحقق من أنهم أصدقاء بالفعل
        if Friend.objects.filter(
            Q(user=from_user, friend=to_user) |
            Q(user=to_user, friend=from_user)
        ).exists():
            return Response(
                {'error': 'أنتم أصدقاء بالفعل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friend_request = serializer.save(from_user=from_user, to_user=to_user)
        
        # إرسال إشعار Push للمستقبل
        try:
            from .push_notifications_service import push_notification_service
            push_notification_service.send_friend_request_notification(friend_request)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error sending push notification: {e}')
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """قبول طلب الصداقة"""
        friend_request = self.get_object()
        
        if friend_request.to_user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لقبول هذا الطلب'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if friend_request.status != 'pending':
            return Response(
                {'error': 'تم الرد على هذا الطلب مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحديث حالة الطلب
        friend_request.status = 'accepted'
        friend_request.save()
        
        # إنشاء علاقة صداقة (متبادلة)
        Friend.objects.get_or_create(user=friend_request.from_user, friend=friend_request.to_user)
        Friend.objects.get_or_create(user=friend_request.to_user, friend=friend_request.from_user)
        
        # ملاحظة: لا حاجة لإرسال إشعار هنا لأن الطلب تم قبوله بالفعل
        # الإشعار يُرسل عند إنشاء الطلب فقط
        
        return Response({'message': 'تم قبول طلب الصداقة'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """رفض طلب الصداقة"""
        friend_request = self.get_object()
        
        if friend_request.to_user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لرفض هذا الطلب'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if friend_request.status != 'pending':
            return Response(
                {'error': 'تم الرد على هذا الطلب مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friend_request.status = 'rejected'
        friend_request.save()
        
        return Response({'message': 'تم رفض طلب الصداقة'})
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """الطلبات المرسلة"""
        requests = FriendRequest.objects.filter(from_user=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received(self, request):
        """الطلبات المستلمة"""
        requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)


class FriendViewSet(viewsets.ModelViewSet):
    """ViewSet للصداقات"""
    queryset = Friend.objects.all()
    serializer_class = FriendSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على أصدقاء المستخدم الحالي"""
        return Friend.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_friends(self, request):
        """قائمة الأصدقاء"""
        friends = Friend.objects.filter(user=request.user)
        serializer = self.get_serializer(friends, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """إزالة صديق"""
        friendship = self.get_object()
        
        if friendship.user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لإزالة هذا الصديق'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # حذف العلاقة من كلا الجانبين
        Friend.objects.filter(
            Q(user=friendship.user, friend=friendship.friend) |
            Q(user=friendship.friend, friend=friendship.user)
        ).delete()
        
        return Response({'message': 'تم إزالة الصديق'})


class BlockedUserViewSet(viewsets.ModelViewSet):
    """ViewSet للمستخدمين المحظورين"""
    queryset = BlockedUser.objects.all()
    serializer_class = BlockedUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على المستخدمين المحظورين للمستخدم الحالي"""
        return BlockedUser.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """حظر مستخدم"""
        user_id = self.request.data.get('blocked_user')
        
        if not user_id:
            return Response(
                {'error': 'يجب تحديد المستخدم للحظر'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            blocked_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'المستخدم غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if blocked_user == self.request.user:
            return Response(
                {'error': 'لا يمكنك حظر نفسك'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(user=self.request.user, blocked_user=blocked_user)
    
    @action(detail=True, methods=['delete'])
    def unblock(self, request, pk=None):
        """إلغاء حظر مستخدم"""
        blocked = self.get_object()
        
        if blocked.user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لإلغاء هذا الحظر'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        blocked.delete()
        return Response({'message': 'تم إلغاء الحظر'})

