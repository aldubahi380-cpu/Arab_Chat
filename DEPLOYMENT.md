# نشر Arab Chat على Render / بيئات الإنتاج

يوضح هذا المستند كيفية تهيئة متغيّرات البيئة والاعتماد على HTTPS/WSS عند تشغيل المشروع في بيئة سحابية مثل Render، بالإضافة إلى الخطوات الأساسية للتشغيل المحلي مع نفس الإعدادات.

## متغيّرات البيئة الأساسية

ضع القيم التالية في ملف `.env` (أو في لوحة متغيّرات البيئة لدى مزوّد الخدمة):

```
DJANGO_SECRET_KEY=سلسلة_سرية_قوية
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-app.onrender.com

# روابط الشبكات
BASE_URL=https://your-app.onrender.com
API_BASE_URL=https://your-app.onrender.com/api
WS_BASE_URL=wss://your-app.onrender.com

# قاعدة البيانات (Render يوفّر PostgreSQL افتراضياً)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis للـ Channels و Celery
REDIS_URL=rediss://:password@host:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Firebase Cloud Messaging
FCM_SERVER_KEY=ضع_مفتاح_FCM_من_Firebase

# إعدادات الجلسات
SESSION_COOKIE_AGE=7776000  # 90 يوماً (بالثواني)

# ضغط الوسائط / ffmpeg (إن تم تثبيته في الحاوية)
FFMPEG_BIN=/opt/render/project/src/bin/ffmpeg
FFPROBE_BIN=/opt/render/project/src/bin/ffprobe

# التخزين السحابي (اختياري)
USE_CLOUD_STORAGE=True
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=eu-west-1
AWS_S3_CUSTOM_DOMAIN=cdn.your-domain.com
DEFAULT_FILE_STORAGE_BACKEND=storages.backends.s3boto3.S3Boto3Storage
```

> **ملاحظة:** عند العمل محلياً مع نفس الملف، عيّن `BASE_URL=http://127.0.0.1:8000` و `WS_BASE_URL=ws://127.0.0.1:8000` وسيقوم الكود بضبط المسارات تلقائياً.

## الخدمات على Render

استخدم ملف `render.yaml` المضمّن لتهيئة:

- خدمة Web (تشغّل `daphne arab_chat.asgi:application`)
- خدمة Worker لتشغيل Celery (`celery -A arab_chat worker --loglevel=info --pool=solo`)
- خدمة Redis مجانية (للوسيط والنتائج/Channels)
- قاعدة بيانات PostgreSQL مجانية

بعد الربط بـ GitHub وتشغيل النشر التلقائي:

1. تأكد من تشغيل migrations أثناء البناء (موجود في `render.yaml`).
2. عيّن جميع متغيّرات البيئة المذكورة أعلاه عبر لوحة Render.
3. فعّل HTTPS على النطاق (Render يوفّر شهادة TLS تلقائياً).

## تشغيل محلي بنفس الإعدادات

1. أنشئ ملف `.env` في الجذر واستخدم القيم المناسبة.
2. ثبّت الاعتمادات:
   ```
   python -m pip install -r requirements.txt
   ```
3. شغّل Redis محلياً (مثلاً عبر Docker أو `redis-server`).
4. شغّل خدمات التطوير:
   ```
   celery -A arab_chat worker --loglevel=info --pool=solo
   celery -A arab_chat beat --loglevel=info
   python manage.py runserver
   ```
5. استخدم `BASE_URL=http://127.0.0.1:8000` و `WS_BASE_URL=ws://127.0.0.1:8000` لاختبار API.

## ملاحظات إضافية

- **HTTPS/WSS:** جميع الروابط للتطبيق الأصلي فقط. تأكد من ضبط BASE_URL و API_BASE_URL بشكل صحيح.
- **التوثيق:** الكود يستخدم ملفات تعريف أجهزة (`SessionDevice`) للحفاظ على تسجيل الدخول الآلي شبيهاً بتطبيقات المراسلة.
- **المكالمات/الإشعارات:** يتطلب تمكين FCM في التطبيق الأصلي.
- **تنظيف الجلسات:** استخدم Celery Beat لإضافة مهام مجدولة (مثل تنظيف الأجهزة منتهية الصلاحية أو تحديث مؤشرات الحالة).
- **حذف الحساب:**  
  - الوضع الاعتيادي يعتمد على Celery Worker نشط. بعد استقبال طلب الحذف (واجهة API)، تُرسل مهمة `delete_user_account_task`، ويكمل العامل حذف جميع البيانات. شغّل الأوامر:
    ```
    celery -A arab_chat worker --loglevel=info --pool=solo
    celery -A arab_chat beat --loglevel=info
    ```
  - في البيئات التي لا يتوفر فيها عامل خلفي، يمكنك تفعيل التنفيذ المتزامن لكل مهام Celery (بما فيها حذف الحساب) بضبط:
    ```
    CELERY_TASK_ALWAYS_EAGER=True
    ```
    أو اتركه كما هو في بيئة التطوير مع `DEBUG=True` وبدون Redis، حيث يُفعَّل ذلك تلقائياً. سيقوم التطبيق الآن بتشغيل الحذف داخل نفس الطلب إذا تعذّر إرسال المهمة للخلفية.

باتباع هذه الخطوات تكون جاهزاً لنشر Arab Chat على Render أو أي منصة تعيد توجيه جميع الطلبات عبر HTTPS بشكل آمن.

