"""
Views للتحقق والتسجيل
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from datetime import timedelta
from .models import OTPVerification, UserProfile, SessionDevice
from .serializers import OTPVerificationSerializer
import secrets
import threading
from collections import defaultdict


class OTPVerificationViewSet(viewsets.ModelViewSet):
    """ViewSet للتحقق برمز OTP"""
    queryset = OTPVerification.objects.all()
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # لا حاجة للمصادقة للـ OTP
    
    # Locks لمنع race conditions في الطلبات المتزامنة
    _send_otp_locks = {}  # Dictionary لتخزين locks لكل phone
    _verify_otp_locks = {}  # Dictionary لتخزين locks لكل phone
    _locks_lock = threading.Lock()  # Lock لحماية الـ dictionaries نفسها
    
    # Rate limiting - تتبع الطلبات لكل رقم هاتف
    _rate_limit_data = defaultdict(list)  # {phone: [timestamps]}
    _rate_limit_lock = threading.Lock()
    
    # إعدادات Rate Limiting
    MAX_REQUESTS_PER_HOUR = 5  # الحد الأقصى للطلبات في الساعة
    MAX_REQUESTS_PER_MINUTE = 2  # الحد الأقصى للطلبات في الدقيقة
    
    def _get_lock(self, phone, lock_type='send'):
        """الحصول على lock لمستخدم معين"""
        with self._locks_lock:
            locks_dict = self._send_otp_locks if lock_type == 'send' else self._verify_otp_locks
            if phone not in locks_dict:
                locks_dict[phone] = threading.Lock()
            return locks_dict[phone]
    
    def _check_rate_limit(self, phone):
        """التحقق من Rate Limiting"""
        now = timezone.now()
        with self._rate_limit_lock:
            # تنظيف الطلبات القديمة (أكثر من ساعة)
            if phone in self._rate_limit_data:
                self._rate_limit_data[phone] = [
                    ts for ts in self._rate_limit_data[phone]
                    if (now - ts).total_seconds() < 3600
                ]
            
            # التحقق من الحد الأقصى في الساعة
            if len(self._rate_limit_data[phone]) >= self.MAX_REQUESTS_PER_HOUR:
                return False, 'لقد تجاوزت الحد الأقصى من الطلبات. يرجى المحاولة بعد ساعة.'
            
            # التحقق من الحد الأقصى في الدقيقة
            recent_requests = [
                ts for ts in self._rate_limit_data[phone]
                if (now - ts).total_seconds() < 60
            ]
            if len(recent_requests) >= self.MAX_REQUESTS_PER_MINUTE:
                return False, 'يرجى الانتظار دقيقة واحدة قبل إرسال طلب جديد.'
            
            # إضافة الطلب الحالي
            self._rate_limit_data[phone].append(now)
            return True, None
    
    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        """إرسال رمز OTP مع حماية من الطلبات المتزامنة"""
        phone = request.data.get('phone', '').strip()
        username = request.data.get('username', '').strip()
        
        # استخدام lock لمنع الطلبات المتزامنة لنفس الرقم
        lock = self._get_lock(phone, 'send')
        with lock:
            # التحقق من وجود البيانات المطلوبة
            if not phone:
                return Response(
                    {'error': '❌ خطأ: يجب إدخال رقم الهاتف', 'field': 'phone'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not username:
                return Response(
                    {'error': '❌ خطأ: يجب إدخال اسم المستخدم', 'field': 'username'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # التحقق من صحة تنسيق رقم الهاتف
            import re
            phone_pattern = re.compile(r'^\+?[1-9]\d{9,14}$')
            if not phone_pattern.match(phone):
                return Response(
                    {'error': '❌ رقم الهاتف غير صحيح. يجب أن يكون من 10 إلى 15 رقماً. مثال: +966501234567 أو 966501234567', 'field': 'phone'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # التحقق من طول اسم المستخدم
            if len(username) < 3:
                return Response(
                    {'error': '❌ اسم المستخدم قصير جداً. يجب أن يكون 3 أحرف على الأقل', 'field': 'username'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(username) > 150:
                return Response(
                    {'error': '❌ اسم المستخدم طويل جداً. الحد الأقصى 150 حرف', 'field': 'username'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # التحقق من أن اسم المستخدم يحتوي على أحرف صالحة فقط (أحرف، أرقام، _)
            username_pattern = re.compile(r'^[a-zA-Z0-9_\u0600-\u06FF]+$')
            if not username_pattern.match(username):
                return Response(
                    {'error': '❌ اسم المستخدم يحتوي على أحرف غير مسموحة. يمكن استخدام الأحرف العربية والإنجليزية والأرقام وعلامة _ فقط', 'field': 'username'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # التحقق من وجود المستخدم بنفس اسم المستخدم
            if User.objects.filter(username=username).exists():
                existing_user = User.objects.get(username=username)
                existing_profile = UserProfile.objects.filter(user=existing_user).first()
                if existing_profile and existing_profile.phone != phone:
                    return Response(
                        {'error': f'❌ اسم المستخدم "{username}" مستخدم بالفعل من قبل مستخدم آخر. يرجى اختيار اسم مستخدم مختلف', 'field': 'username'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # التحقق من وجود رقم الهاتف مستخدم من قبل مستخدم آخر
            existing_profile_with_phone = UserProfile.objects.filter(phone=phone).first()
            if existing_profile_with_phone:
                if existing_profile_with_phone.user.username != username:
                    return Response(
                        {
                            'error': f'❌ رقم الهاتف {phone} مستخدم بالفعل من قبل مستخدم آخر. إذا كان هذا رقمك، يرجى استخدام اسم المستخدم "{existing_profile_with_phone.user.username}"',
                            'field': 'phone',
                            'success': False
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Rate Limiting - التحقق من عدد الطلبات
            rate_ok, rate_error = self._check_rate_limit(phone)
            if not rate_ok:
                return Response(
                    {
                        'error': f'⚠️ {rate_error}',
                        'field': 'rate_limit',
                        'success': False
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            try:
                dev_mode_enabled = getattr(settings, 'OTP_DEV_MODE', False)
                otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
                expires_delta = timedelta(minutes=5)
                if dev_mode_enabled:
                    expires_delta = timedelta(hours=12)

                expires_at = timezone.now() + expires_delta

                OTPVerification.objects.update_or_create(
                    phone=phone,
                    defaults={
                        'otp_code': otp_code,
                        'expires_at': expires_at,
                        'is_verified': False
                    }
                )

                # TODO: دمج خدمة إرسال OTP (رسائل نصية أو واتساب) في الإنتاج

                dev_mode_request = request.data.get('dev_mode', False)
                if isinstance(dev_mode_request, str):
                    dev_mode_request = dev_mode_request.lower() in ('true', '1', 'yes')

                should_expose_code = dev_mode_enabled and dev_mode_request

                return Response({
                    'message': '✅ تم إرسال رمز التحقق بنجاح',
                    'phone': phone,
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'otp_code': otp_code if should_expose_code else None,
                    'success': True,
                    'dev_mode': dev_mode_enabled
                })
            except Exception as e:
                import traceback
                error_message = str(e)
                print(f"Error in send_otp: {error_message}")
                print(traceback.format_exc())
                
                # رسائل خطأ واضحة حسب نوع الخطأ
                if 'phone' in error_message.lower() or 'unique' in error_message.lower():
                    return Response(
                        {
                            'error': '❌ رقم الهاتف مستخدم بالفعل. إذا كان هذا رقمك، يرجى استخدام اسم المستخدم المرتبط به',
                            'field': 'phone',
                            'success': False
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif 'username' in error_message.lower():
                    return Response(
                        {
                            'error': '❌ اسم المستخدم غير متاح. يرجى اختيار اسم مستخدم آخر',
                            'field': 'username',
                            'success': False
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {
                            'error': f'❌ حدث خطأ غير متوقع: {error_message}. يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني',
                            'field': 'general',
                            'success': False
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
    
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """التحقق من رمز OTP مع حماية من الطلبات المتزامنة"""
        phone = request.data.get('phone', '').strip()
        otp_code = request.data.get('otp_code', '').strip()
        username = request.data.get('username', '').strip()

        lock = self._get_lock(phone, 'verify')
        with lock:
            if not phone:
                return Response(
                    {
                        'error': '❌ خطأ: يجب إدخال رقم الهاتف',
                        'field': 'phone',
                        'success': False
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not otp_code:
                return Response(
                    {
                        'error': '❌ خطأ: يجب إدخال رمز التحقق',
                        'field': 'otp_code',
                        'success': False
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not username:
                return Response(
                    {
                        'error': '❌ خطأ: يجب إدخال اسم المستخدم',
                        'field': 'username',
                        'success': False
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                with transaction.atomic():
                    otp_record = (
                        OTPVerification.objects.select_for_update()
                        .filter(phone=phone, otp_code=otp_code, is_verified=False)
                        .order_by('-created_at')
                        .first()
                    )

                    if not otp_record or (otp_record.expires_at and otp_record.expires_at < timezone.now()):
                        return Response(
                            {
                                'error': '❌ رمز التحقق غير صحيح أو منتهي الصلاحية',
                                'field': 'otp_code',
                                'success': False
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={'email': f'{phone}@arabchat.com'}
                    )
                    if not created and user.email != f'{phone}@arabchat.com':
                        user.email = f'{phone}@arabchat.com'
                        user.save(update_fields=['email'])

                    profile, profile_created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={'phone': phone, 'is_verified': True}
                    )
                    if not profile_created:
                        update_fields = []
                        if profile.phone != phone:
                            profile.phone = phone
                            update_fields.append('phone')
                        if not profile.is_verified:
                            profile.is_verified = True
                            update_fields.append('is_verified')
                        if update_fields:
                            profile.save(update_fields=update_fields)

                    otp_record.is_verified = True
                    otp_record.expires_at = timezone.now()
                    otp_record.save(update_fields=['is_verified', 'expires_at'])

                    device_id = request.data.get('device_id') or request.data.get('deviceId')
                    device_name = request.data.get('device_name') or request.data.get('deviceName')
                    platform = request.data.get('platform') or request.data.get('device_platform')
                    session_device = SessionDevice.issue_for_request(
                        user=user,
                        request=request,
                        device_id=device_id,
                        device_name=device_name,
                        platform=platform,
                    )

                    token, _ = Token.objects.get_or_create(user=user)

                    response_data = {
                        'message': '✅ تم التحقق بنجاح! مرحباً بك في واتساب الدوبحي',
                        'token': token.key,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'phone': profile.phone if profile else None,
                            'is_verified': profile.is_verified if profile else False,
                        },
                        'created': created,
                        'session': {
                            'session_token': session_device.session_token,
                            'device_id': session_device.device_id,
                            'device_name': session_device.device_name,
                            'platform': session_device.platform,
                            'expires_at': session_device.expires_at.isoformat(),
                        },
                        'success': True
                    }

                    response = Response(response_data)
                    login(request, user)

                    secure_cookie = not settings.DEBUG
                    cookie_max_age = SessionDevice.DEFAULT_TTL_DAYS * 24 * 60 * 60
                    response.set_cookie(
                        'session_token',
                        session_device.session_token,
                        httponly=True,
                        secure=secure_cookie,
                        samesite='None' if secure_cookie else 'Lax',
                        max_age=cookie_max_age,
                    )
                    response.set_cookie(
                        'session_device_id',
                        session_device.device_id,
                        httponly=False,
                        secure=secure_cookie,
                        samesite='None' if secure_cookie else 'Lax',
                        max_age=cookie_max_age,
                    )
                    response.set_cookie(
                        'auth_token',
                        token.key,
                        httponly=True,
                        secure=secure_cookie,
                        samesite='None' if secure_cookie else 'Lax',
                        max_age=cookie_max_age,
                    )

                    return response
            except Exception as exc:
                import logging
                logger = logging.getLogger(__name__)
                logger.error('Error verifying OTP: %s', exc, exc_info=True)
                return Response(
                    {
                        'error': f'❌ حدث خطأ أثناء التحقق: {exc}',
                        'success': False
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    @action(detail=False, methods=['get'])
    def otp_logs(self, request):
        """عرض سجل رموز OTP (للتطوير فقط)"""
        # التحقق من أننا في وضع التطوير
        if not getattr(settings, 'DEBUG', False):
            return Response(
                {
                    'error': '❌ هذه الميزة متاحة فقط في وضع التطوير',
                    'success': False
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # الحصول على آخر 50 رمز OTP
        otps = OTPVerification.objects.all().order_by('-created_at')[:50]
        
        from .serializers import OTPVerificationSerializer
        serializer = OTPVerificationSerializer(otps, many=True)
        
        return Response({
            'otps': serializer.data,
            'count': len(otps),
            'success': True
        })

