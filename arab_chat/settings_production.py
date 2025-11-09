"""
Django settings for arab_chat project - Production Configuration

استخدم هذا الملف للإنتاج على السيرفر الحقيقي
"""
from .settings import *  # noqa: F401,F403
import os
import dj_database_url


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# الحصول على ALLOWED_HOSTS من متغير البيئة (متوافق مع المتغيرات المستخدمة في settings الأساسي)
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS') or os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS.split(',') if host.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# استخدام SECRET_KEY من نفس المتغير المعتمد في الإعدادات العامة
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("يجب تعيين SECRET_KEY في متغيرات البيئة للإنتاج!")

# تكوين قاعدة البيانات من DATABASE_URL (Postgres في Render)، مع دعم fallback اختياري
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
else:
    # Fallback لاستخدام MySQL في حال لم يتم توفير DATABASE_URL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'arab_chat_db'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }

# CORS settings للإنتاج - حدد النطاقات المسموحة فقط
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",  # غير هذا إلى نطاقك
    "https://www.yourdomain.com",
    # يمكن إضافة نطاقات تطبيق Android إذا لزم الأمر
]

# إعدادات الأمان
SECURE_SSL_REDIRECT = True  # إعادة توجيه HTTP إلى HTTPS
SESSION_COOKIE_SECURE = True  # إرسال cookies عبر HTTPS فقط
CSRF_COOKIE_SECURE = True  # CSRF cookies عبر HTTPS فقط
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# إعدادات Redis للإنتاج
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# إعدادات الملفات الثابتة
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# إعدادات البريد الإلكتروني (اختياري)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# إنشاء مجلد logs إذا لم يكن موجوداً
import os
logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

