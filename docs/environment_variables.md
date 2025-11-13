# Environment Variables Documentation

هذا الملف يوثق جميع Environment Variables المطلوبة للمشروع.

## ملاحظة مهمة

- في **Production (Render)**: يتم تعيين هذه القيم في لوحة Render Dashboard
- في **Development**: يتم استخدام ملف `.env` (يجب عدم رفعه إلى Git)

---

## Django Backend Variables

### Required Variables (مطلوبة)

```env
# Secret Key - مفتاح أمان Django
DJANGO_SECRET_KEY=your-secret-key-here-min-50-chars

# Debug Mode
DJANGO_DEBUG=False  # يجب أن يكون False في Production

# Allowed Hosts
DJANGO_ALLOWED_HOSTS=your-app.onrender.com,www.your-app.onrender.com
```

### Base URLs

```env
# Base URL للمشروع
BASE_URL=https://your-app.onrender.com

# Frontend Base URL (للـ Web App)
FRONTEND_BASE_URL=https://your-app.onrender.com

# API Base URL
API_BASE_URL=https://your-app.onrender.com/api

# WebSocket Base URL
WS_BASE_URL=wss://your-app.onrender.com
```

### Database

```env
# PostgreSQL Database URL (في Render)
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Redis (للـ Channels و Celery)

```env
# Redis URL
REDIS_URL=rediss://:password@host:6379/0

# Celery Broker (عادة نفس Redis URL)
CELERY_BROKER_URL=${REDIS_URL}

# Celery Result Backend (عادة نفس Redis URL)
CELERY_RESULT_BACKEND=${REDIS_URL}
```

### Firebase Cloud Messaging (FCM)

```env
# FCM Server Key
FCM_SERVER_KEY=your-fcm-server-key-here

# FCM Web Push Public Key (للـ Web App)
FCM_WEB_PUSH_PUBLIC_KEY=your-fcm-public-key

# FCM Web Push Sender ID
FCM_WEB_PUSH_SENDER_ID=your-sender-id
```

### Session Settings

```env
# Session Cookie Age (بالثواني) - 90 يوم
SESSION_COOKIE_AGE=7776000
```

---

## Flutter App Variables

الـ Flutter App سيستخدم نفس URLs من Backend:

```env
# API Base URL للـ Flutter
FLUTTER_API_BASE_URL=${API_BASE_URL}
# أو مباشرة:
FLUTTER_API_BASE_URL=https://your-app.onrender.com/api

# WebSocket Base URL للـ Flutter
FLUTTER_WS_BASE_URL=${WS_BASE_URL}
# أو مباشرة:
FLUTTER_WS_BASE_URL=wss://your-app.onrender.com
```

**ملاحظة:** في Flutter، عادةً تُحفظ هذه القيم في ملف `config.dart` أو `constants.dart`

---

## Optional Variables (اختيارية)

### CORS Settings

```env
# CORS Allowed Origins (للتطبيقات الأخرى التي تستخدم API)
CORS_ALLOWED_ORIGINS=https://other-app.com,https://another-app.com
```

### Cloud Storage (AWS S3)

```env
# تفعيل Cloud Storage
USE_CLOUD_STORAGE=True

# AWS S3 Settings
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=eu-west-1
AWS_S3_CUSTOM_DOMAIN=cdn.your-domain.com

# Storage Backends
DEFAULT_FILE_STORAGE_BACKEND=storages.backends.s3boto3.S3Boto3Storage
STATICFILES_STORAGE_BACKEND=storages.backends.s3boto3.S3StaticStorage
```

### Email Settings (اختياري)

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

---

## Environment Variables في Render

### خطوات إضافة Environment Variables في Render:

1. اذهب إلى Render Dashboard
2. اختر المشروع (Service)
3. اضغط على "Environment" من القائمة الجانبية
4. أضف كل متغير على حدة
5. احفظ التغييرات
6. Render سيعيد تشغيل الخدمة تلقائياً

### مثال على القيم في Render:

```
DJANGO_SECRET_KEY = abc123...xyz789
DJANGO_DEBUG = False
DJANGO_ALLOWED_HOSTS = your-app.onrender.com
BASE_URL = https://your-app.onrender.com
API_BASE_URL = https://your-app.onrender.com/api
WS_BASE_URL = wss://your-app.onrender.com
DATABASE_URL = postgresql://user:pass@host:5432/db
REDIS_URL = rediss://:pass@host:6379/0
...
```

---

## Development (.env file)

للعمل محلياً، أنشئ ملف `.env` في جذر المشروع:

```env
# .env (يجب عدم رفعه إلى Git)
DJANGO_SECRET_KEY=dev-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

BASE_URL=http://127.0.0.1:8000
FRONTEND_BASE_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000/api
WS_BASE_URL=ws://127.0.0.1:8000

DATABASE_URL=sqlite:///db.sqlite3
# أو PostgreSQL محلي:
# DATABASE_URL=postgresql://user:password@localhost:5432/arab_chat

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

FCM_SERVER_KEY=your-dev-fcm-key
SESSION_COOKIE_AGE=7776000
```

**ملاحظة:** ملف `.env` موجود في `.gitignore` ولن يُرفع إلى Git

---

## Security Notes

⚠️ **مهم جداً:**

1. **لا ترفع ملف `.env` إلى Git أبداً**
2. **لا تشارك `DJANGO_SECRET_KEY` أو أي معلومات حساسة**
3. **استخدم قيم مختلفة للـ Development و Production**
4. **في Production، استخدم HTTPS/WSS دائماً**
5. **احفظ `FCM_SERVER_KEY` بشكل آمن**

---

## Checklist للتطبيق على Render

- [ ] `DJANGO_SECRET_KEY` مُعيّن
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_ALLOWED_HOSTS` يحتوي على نطاق Render
- [ ] `BASE_URL` و `API_BASE_URL` و `WS_BASE_URL` صحيحة
- [ ] `DATABASE_URL` من Render Database
- [ ] `REDIS_URL` من Render Redis
- [ ] `FCM_SERVER_KEY` مُعيّن (للإشعارات)
- [ ] جميع المتغيرات مكتوبة بشكل صحيح (بدون أخطاء إملائية)

---

**Last Updated:** 2025-01-13

