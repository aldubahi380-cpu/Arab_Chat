from __future__ import annotations

from django.conf import settings


def app_config(request):
    """
    إرجاع إعدادات الواجهة الأمامية حتى تكون متاحة في جميع القوالب.
    """
    return {
        'APP_CONFIG': {
            'baseUrl': getattr(settings, 'BASE_URL', ''),
            'frontendBaseUrl': getattr(settings, 'FRONTEND_BASE_URL', ''),
            'apiBaseUrl': getattr(settings, 'API_BASE_URL', ''),
            'wsBaseUrl': getattr(settings, 'WS_BASE_URL', ''),
            'mediaUrl': settings.MEDIA_URL,
            'staticUrl': settings.STATIC_URL,
            'fcmWebPushPublicKey': getattr(settings, 'FCM_WEB_PUSH_PUBLIC_KEY', ''),
            'fcmWebPushSenderId': getattr(settings, 'FCM_WEB_PUSH_SENDER_ID', ''),
            'firebaseConfig': getattr(settings, 'FIREBASE_CONFIG', {}),
            'callSessionMaxMinutes': getattr(settings, 'CALL_SESSION_MAX_MINUTES', 120),
            'userId': request.user.id if request.user.is_authenticated else None,
        }
    }

