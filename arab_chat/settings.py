"""الضبط الأساسي لمشروع arab_chat مع تهيئة جاهزة للإنتاج."""

from pathlib import Path
import os
import json
from celery.schedules import crontab

import dj_database_url
import environ


BASE_DIR = Path(__file__).resolve().parent.parent

# تحميل متغيرات البيئة من ملف .env (اختياري)
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, ''),
    DJANGO_ALLOWED_HOSTS=(list, ['.onrender.com']),
    FRONTEND_BASE_URL=(str, 'https://your-app.onrender.com'),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    REDIS_URL=(str, ''),
    SESSION_COOKIE_AGE=(int, 90 * 24 * 60 * 60),
    USE_CLOUD_STORAGE=(bool, False),
    AWS_STORAGE_BUCKET_NAME=(str, ''),
    AWS_S3_REGION_NAME=(str, ''),
    AWS_S3_CUSTOM_DOMAIN=(str, ''),
    DEFAULT_FILE_STORAGE_BACKEND=(str, ''),
    STATICFILES_STORAGE_BACKEND=(str, ''),
    SECURE_SSL_REDIRECT=(bool, True),
    FCM_SERVER_KEY=(str, ''),
    OTP_DEV_MODE=(bool, False),
    CELERY_BROKER_URL=(str, ''),
    CELERY_RESULT_BACKEND=(str, ''),
    FCM_WEB_PUSH_PUBLIC_KEY=(str, ''),
    FCM_WEB_PUSH_SENDER_ID=(str, ''),
    CALL_SESSION_MAX_MINUTES=(int, 120),
)
environ.Env.read_env(str(BASE_DIR / '.env'))

# الأمان الأساسي
SECRET_KEY = env('DJANGO_SECRET_KEY') or os.environ.get(
    'SECRET_KEY',
    'django-insecure-change-me'
)
DEBUG = env.bool('DJANGO_DEBUG')

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')
if DEBUG:
    ALLOWED_HOSTS = list(set(ALLOWED_HOSTS + ['localhost', '127.0.0.1']))

# ضبط التطبيقات
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'channels',
    # Local apps
    'chat',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'chat.middleware.TokenAutoLoginMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'arab_chat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'chat.context_processors.app_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'arab_chat.wsgi.application'

# قاعدة البيانات
DATABASES = {
    'default': dj_database_url.parse(
        env('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# التحقق من كلمات المرور
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# الترجمة
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# الملفات الثابتة والوسائط
STATIC_URL = env('DJANGO_STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
static_path = BASE_DIR / 'static'
if static_path.exists():
    STATICFILES_DIRS.append(static_path)

MEDIA_URL = env('DJANGO_MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'staticfiles': {
        'BACKEND': env('STATICFILES_STORAGE_BACKEND', default='whitenoise.storage.CompressedManifestStaticFilesStorage'),
    },
    'default': {
        'BACKEND': env('DEFAULT_FILE_STORAGE_BACKEND', default='django.core.files.storage.FileSystemStorage'),
    },
}

WHITENOISE_MANIFEST_STRICT = False

if env.bool('USE_CLOUD_STORAGE'):
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME')
    AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com')
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_EXPIRE = 3600

    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': AWS_S3_REGION_NAME or None,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN or None,
        }
    }
    STORAGES['staticfiles'] = {
        'BACKEND': 'storages.backends.s3boto3.S3StaticStorage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': AWS_S3_REGION_NAME or None,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN or None,
            'default_acl': 'public-read',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# مصادقة المستخدم
LOGIN_URL = '/dashboard/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/dashboard/'

SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_SAVE_EVERY_REQUEST = False
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
else:
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# إعداد روابط القاعدة
BASE_URL = env('BASE_URL', default='')
FRONTEND_BASE_URL = env('FRONTEND_BASE_URL', default=BASE_URL or '')
API_BASE_URL = env('API_BASE_URL', default=f"{BASE_URL.rstrip('/')}/api" if BASE_URL else '/api')
WS_BASE_URL = env('WS_BASE_URL', default='')

# CORS و CSRF
DEFAULT_CORS_ORIGINS = []
for origin in (FRONTEND_BASE_URL, BASE_URL):
    if origin:
        DEFAULT_CORS_ORIGINS.append(origin)
DEFAULT_CORS_ORIGINS = list(dict.fromkeys(DEFAULT_CORS_ORIGINS))
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS') or DEFAULT_CORS_ORIGINS
CORS_ALLOW_CREDENTIALS = True

default_csrf_origins = []
for origin in DEFAULT_CORS_ORIGINS:
    if origin:
        if origin.startswith('http://') or origin.startswith('https://'):
            default_csrf_origins.append(origin)
        else:
            default_csrf_origins.append(f'https://{origin.lstrip(".")}')

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS') or default_csrf_origins

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-token',
    'x-device-id',
]

CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']

# القنوات
ASGI_APPLICATION = 'arab_chat.asgi.application'
redis_url = env('REDIS_URL')
if redis_url:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [redis_url],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

# Celery settings
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=redis_url or 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_TASK_DEFAULT_QUEUE = 'arab_chat'
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 10 * 60
CELERY_BEAT_SCHEDULE = {
    'cleanup-stale-call-sessions': {
        'task': 'chat.tasks.cleanup_stale_call_sessions',
        'schedule': crontab(minute='*/10'),
    },
    'cleanup-expired-session-devices': {
        'task': 'chat.tasks.cleanup_stale_session_devices',
        'schedule': crontab(hour='*/4'),
    },
    'cleanup-expired-otp-codes': {
        'task': 'chat.tasks.cleanup_expired_otps',
        'schedule': crontab(hour='*/1'),
    },
}

if DEBUG and not redis_url and not env('CELERY_BROKER_URL'):
    CELERY_TASK_ALWAYS_EAGER = True

# Firebase Cloud Messaging
FCM_SERVER_KEY = env('FCM_SERVER_KEY', default=os.environ.get('FCM_SERVER_KEY', ''))
OTP_DEV_MODE = env.bool('OTP_DEV_MODE', default=DEBUG)

# ضغط الوسائط
MEDIA_IMAGE_COMPRESSION = {
    'max_edge': 1440,
    'quality': 88,
    'min_quality': 78,
    'target_max_kb': 650,
    'target_min_kb': 220,
    'allow_webp': True,
}

MEDIA_VIDEO_COMPRESSION = {
    'target_width': 720,
    'max_height': 1280,
    'max_bitrate': '1200k',
    'min_bitrate': '800k',
    'audio_bitrate': '96k',
    'frame_rate': 30,
    'max_duration': 120,
}

# رأس الثقة للأصول الآمنة
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# إعدادات إضافية لتشغيل الخدمة كـ PWA
PWA_APP_NAME = 'Arab Chat'
PWA_APP_DESCRIPTION = 'تجربة دردشة فورية آمنة شبيهة بتطبيق واتساب.'
PWA_APP_THEME_COLOR = '#075E54'
PWA_APP_BACKGROUND_COLOR = '#F0F2F5'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'portrait'
PWA_APP_START_URL = '/'
PWA_DIR = 'ltr'
PWA_LANG = 'ar'

# مسارات ffmpeg/ffprobe للإنتاج
FFMPEG_BIN = env('FFMPEG_BIN', default=os.environ.get('FFMPEG_BINARY', 'ffmpeg'))
FFPROBE_BIN = env('FFPROBE_BIN', default=os.environ.get('FFPROBE_BINARY', 'ffprobe'))

CALL_SESSION_MAX_MINUTES = env.int('CALL_SESSION_MAX_MINUTES')
FCM_WEB_PUSH_PUBLIC_KEY = env('FCM_WEB_PUSH_PUBLIC_KEY')
FCM_WEB_PUSH_SENDER_ID = env('FCM_WEB_PUSH_SENDER_ID')
firebase_config_raw = env('FIREBASE_CONFIG', default='{}')
if isinstance(firebase_config_raw, dict):
    FIREBASE_CONFIG = firebase_config_raw
else:
    try:
        FIREBASE_CONFIG = json.loads(firebase_config_raw or '{}')
    except json.JSONDecodeError:
        FIREBASE_CONFIG = {}