# خطوات النشر والبناء

## 1. رفع التغييرات إلى Git

```bash
git add -A
git commit -m "feat: إضافة صفحة تحميل APK وضبط Responsive Design

- إضافة صفحة HTML لتحميل APK من Render
- إضافة route لتحميل APK من مجلد /apk
- ضبط جميع الواجهات لتكون Responsive باستخدام dp/sp
- إنشاء dimens.xml للوحدات القياسية
- إزالة جميع بقايا Web/Hybrid (whitenoise, staticfiles, FRONTEND_BASE_URL)
- حذف mysite/ وإزالة Activities غير موجودة
- تحديث DEPLOYMENT.md و settings_production.py
- إضافة REQUEST_INSTALL_PACKAGES permission"

git push origin main
```

## 2. نشر على Render

بعد رفع التغييرات إلى Git:
- Render سيقوم تلقائياً بنشر التحديثات
- الصفحة الرئيسية (`/`) ستكون صفحة تحميل APK
- رابط التحميل: `https://your-app.onrender.com/download/apk/`

## 3. بناء APK

### الطريقة 1: استخدام Android Studio
1. افتح المشروع في Android Studio
2. انتقل إلى `Build > Build Bundle(s) / APK(s) > Build APK(s)`
3. أو استخدم `Build > Generate Signed Bundle / APK` للـ Release

### الطريقة 2: استخدام Gradle Command Line
```bash
# تأكد من وجود Gradle wrapper
# إذا لم يكن موجوداً، أنشئه من Android Studio:
# File > Settings > Build, Execution, Deployment > Build Tools > Gradle
# أو استخدم: gradle wrapper

# بناء APK
./gradlew assembleRelease

# أو على Windows
gradlew.bat assembleRelease
```

### الطريقة 3: استخدام build_apk.bat (Windows)
```bash
.\build_apk.bat
```

## 4. نسخ APK إلى مجلد /apk

بعد بناء APK، سيتم نسخه تلقائياً إذا استخدمت `build_apk.bat`.

أو يدوياً:
```bash
# Windows
copy app\build\outputs\apk\release\*.apk apk\

# Linux/Mac
cp app/build/outputs/apk/release/*.apk apk/
```

## 5. اختبار التحميل

1. بعد نشر التغييرات على Render
2. افتح الرابط: `https://your-app.onrender.com`
3. اضغط على زر "تحميل التطبيق (APK)"
4. يجب أن يبدأ التحميل مباشرة

## ملاحظات مهمة

- تأكد من وجود APK في مجلد `/apk` قبل النشر
- إذا لم يكن Gradle wrapper موجوداً، استخدم Android Studio لبناء APK
- تأكد من تحديث `API_BASE_URL` في `app/build.gradle` قبل البناء
- APK يجب أن يكون signed للـ Release (استخدم debug keystore للاختبار)

