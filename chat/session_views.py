from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from rest_framework.authtoken.models import Token

from .models import SessionDevice
from .serializers import SessionDeviceSerializer, UserSerializer


class SessionDeviceViewSet(viewsets.ModelViewSet):
    """إدارة جلسات الأجهزة الموثوقة"""

    serializer_class = SessionDeviceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        return SessionDevice.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_device = serializer.save()
        output_serializer = self.get_serializer(session_device)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def validate_token(self, request):
        """التحقق من صلاحية session token القادم من الجهاز"""
        session_token = request.data.get('session_token') or request.data.get('token')
        device_id = request.data.get('device_id')

        if not session_token or not device_id:
            return Response(
                {'success': False, 'valid': False, 'error': 'session_token و device_id مطلوبان'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = SessionDevice.objects.select_related('user').filter(
            session_token=session_token,
            device_id=device_id,
            is_active=True
        ).first()

        if not session or session.expires_at < timezone.now():
            if session:
                session.mark_inactive()
            return Response(
                {'success': False, 'valid': False, 'error': 'رمز الجلسة غير صالح أو منتهي'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        session.touch()
        auth_token, _ = Token.objects.get_or_create(user=session.user)

        user_data = UserSerializer(session.user).data

        return Response({
            'success': True,
            'valid': True,
            'user': user_data,
            'auth_token': auth_token.key,
            'session': {
                'session_token': session.session_token,
                'device_id': session.device_id,
                'device_name': session.device_name,
                'platform': session.platform,
                'expires_at': session.expires_at,
            }
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def revoke(self, request):
        """إلغاء جلسة جهاز محدد للمستخدم الحالي"""
        session_token = request.data.get('session_token') or request.COOKIES.get('session_token')
        device_id = request.data.get('device_id') or request.COOKIES.get('session_device_id')

        if not session_token or not device_id:
            return Response(
                {'success': False, 'error': 'session_token و device_id مطلوبان لإلغاء الجلسة'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = SessionDevice.objects.get(
                user=request.user,
                session_token=session_token,
                device_id=device_id
            )
        except SessionDevice.DoesNotExist:
            return Response({
                'success': False,
                'error': 'الجلسة غير موجودة أو تم إلغاؤها مسبقاً'
            }, status=status.HTTP_404_NOT_FOUND)

        session.mark_inactive()

        return Response({'success': True})


