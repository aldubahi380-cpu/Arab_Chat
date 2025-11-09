"""
Views لإدارة إشعارات Push (FCM Tokens)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import DeviceToken
from .serializers import DeviceTokenSerializer


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة رموز الأجهزة (FCM Tokens)"""
    queryset = DeviceToken.objects.all()
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على رموز الأجهزة للمستخدم الحالي فقط"""
        return DeviceToken.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        """إنشاء أو تحديث رمز الجهاز"""
        token = serializer.validated_data.get('token')
        device_type = serializer.validated_data.get('device_type', 'android')
        device_id = serializer.validated_data.get('device_id')
        device_name = serializer.validated_data.get('device_name')
        
        # البحث عن token موجود
        existing_token = DeviceToken.objects.filter(
            token=token,
            user=self.request.user
        ).first()
        
        if existing_token:
            # تحديث token موجود
            existing_token.device_type = device_type
            existing_token.device_id = device_id
            existing_token.device_name = device_name
            existing_token.is_active = True
            existing_token.last_used = timezone.now()
            existing_token.save()
            return existing_token
        else:
            # إنشاء token جديد
            return serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """تسجيل رمز جهاز جديد"""
        token = request.data.get('token')
        device_type = request.data.get('device_type', 'android')
        device_id = request.data.get('device_id')
        device_name = request.data.get('device_name')
        
        if not token:
            return Response(
                {'error': 'يجب إرسال رمز الجهاز (token)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # البحث عن token موجود
        existing_token = DeviceToken.objects.filter(
            token=token,
            user=request.user
        ).first()
        
        if existing_token:
            # تحديث token موجود
            existing_token.device_type = device_type
            existing_token.device_id = device_id
            existing_token.device_name = device_name
            existing_token.is_active = True
            existing_token.last_used = timezone.now()
            existing_token.save()
            serializer = self.get_serializer(existing_token)
            return Response({
                'message': 'تم تحديث رمز الجهاز',
                'device_token': serializer.data
            })
        else:
            # إنشاء token جديد
            device_token = DeviceToken.objects.create(
                user=request.user,
                token=token,
                device_type=device_type,
                device_id=device_id,
                device_name=device_name,
                is_active=True
            )
            serializer = self.get_serializer(device_token)
            return Response({
                'message': 'تم تسجيل رمز الجهاز بنجاح',
                'device_token': serializer.data
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def unregister(self, request):
        """إلغاء تسجيل رمز جهاز"""
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'يجب إرسال رمز الجهاز (token)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            device_token = DeviceToken.objects.get(
                token=token,
                user=request.user
            )
            device_token.is_active = False
            device_token.save()
            return Response({'message': 'تم إلغاء تسجيل رمز الجهاز'})
        except DeviceToken.DoesNotExist:
            return Response(
                {'error': 'رمز الجهاز غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_tokens(self, request):
        """الحصول على جميع رموز الأجهزة للمستخدم"""
        tokens = DeviceToken.objects.filter(user=request.user, is_active=True)
        serializer = self.get_serializer(tokens, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """تعطيل رمز جهاز"""
        device_token = self.get_object()
        
        if device_token.user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لتعطيل هذا الرمز'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        device_token.is_active = False
        device_token.save()
        return Response({'message': 'تم تعطيل رمز الجهاز'})

