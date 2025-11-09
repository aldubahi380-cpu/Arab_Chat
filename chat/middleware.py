"""
Middleware للسماح بالوصول من الشبكة المحلية في وضع التطوير
"""
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import login
from rest_framework.authtoken.models import Token

from .models import SessionDevice


class AllowLocalNetworkMiddleware:
    """
    Middleware للسماح بالوصول من أي IP محلي في وضع DEBUG
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        # في وضع DEBUG، السماح بالوصول من أي IP محلي
        if settings.DEBUG:
            host = request.get_host().split(':')[0]
            
            # التحقق من أن العنوان هو IP محلي
            if self._is_local_ip(host):
                # إضافة العنوان إلى ALLOWED_HOSTS مؤقتاً
                if host not in settings.ALLOWED_HOSTS:
                    settings.ALLOWED_HOSTS.append(host)
        
        response = self.get_response(request)
        return response
    
    def _is_local_ip(self, ip: str) -> bool:
        """
        التحقق من أن IP هو عنوان محلي
        """
        if ip in ['localhost', '127.0.0.1']:
            return True
        
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            # 192.168.x.x
            if parts[0] == '192' and parts[1] == '168':
                return True
            
            # 10.x.x.x
            if parts[0] == '10':
                return True
            
            # 172.16.x.x - 172.31.x.x
            if parts[0] == '172' and 16 <= int(parts[1]) <= 31:
                return True
            
            # 169.254.x.x (Auto-IP)
            if parts[0] == '169' and parts[1] == '254':
                return True
                
        except (ValueError, IndexError):
            return False
        
        return False


class TokenAutoLoginMiddleware:
    """تسجيل الدخول تلقائياً باستخدام auth_token المخزن في الكوكيز"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if not request.user.is_authenticated:
            token_key = self._extract_token(request)
            if token_key:
                try:
                    token = Token.objects.select_related('user').get(key=token_key)
                    user = token.user
                    if user.is_active:
                        login(request, user)
                        request.authenticated_via_token = True
                except Token.DoesNotExist:
                    request.invalid_auth_token = True
            else:
                session_token, device_id = self._extract_session_tokens(request)
                if session_token and device_id:
                    session = SessionDevice.objects.select_related('user').filter(
                        session_token=session_token,
                        device_id=device_id,
                        is_active=True
                    ).first()
                    if session and session.is_valid():
                        user = session.user
                        if user.is_active:
                            login(request, user)
                            request.session_device = session
                            session.touch()
                    else:
                        request.invalid_session_token = True

        response = self.get_response(request)

        # إذا كان هناك token غير صالح، إزالة الكوكيز من الاستجابة
        if getattr(request, 'invalid_auth_token', False):
            try:
                response.delete_cookie('auth_token')
            except Exception:
                pass

        if getattr(request, 'invalid_session_token', False):
            try:
                response.delete_cookie('session_token')
                response.delete_cookie('session_device_id')
            except Exception:
                pass

        return response

    def _extract_token(self, request: HttpRequest):
        token_key = request.COOKIES.get('auth_token')
        if token_key:
            return token_key

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            return auth_header.split(' ', 1)[1].strip()

        return None

    def _extract_session_tokens(self, request: HttpRequest):
        session_token = request.COOKIES.get('session_token')
        device_id = request.COOKIES.get('session_device_id')

        if not session_token:
            session_token = request.META.get('HTTP_X_SESSION_TOKEN')
        if not device_id:
            device_id = request.META.get('HTTP_X_DEVICE_ID')

        return session_token, device_id

