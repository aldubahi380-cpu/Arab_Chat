# Arab Chat - تطبيق Android

## ✅ حالة المشروع

المشروع جاهز الآن كتطبيق **Android فقط** مع:
- ✅ صفحة تحميل APK على Render
- ✅ واجهات Responsive باستخدام dp/sp
- ✅ إزالة جميع بقايا Web/Hybrid
- ✅ Network Layer كامل في Kotlin
- ✅ ربط مع Render API

## 📱 خطوات النشر والبناء

### 1. رفع التغييرات إلى Git

```bash
git add -A
git commit -m "feat: إضافة صفحة تحميل APK وضبط Responsive Design"
git push origin main
```

### 2. نشر على Render

بعد رفع التغييرات:
- Render سينشر تلقائياً
- الصفحة الرئيسية: `https://your-app.onrender.com
- صفحة التحميل: `https://your-app.onrender.com/download/apk/`

### 3. بناء APK

#### باستخدام Android Studio:

1. افتح المشروع في Android Studio
2. **مهم**: حدث `API_BASE_URL` في `app/build.gradle`:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://your-actual-app.onrender.com/api"'
   ```
3. `Build > Build Bundle(s) / APK(s) > Build APK(s)`
4. APK في: `app/build/outputs/apk/release/`

#### باستخدام Gradle:

```bash
# Windows
gradlew.bat assembleRelease

# Linux/Mac
./gradlew assembleRelease
```

### 4. نسخ APK إلى مجلد /apk

```bash
# Windows
copy app\build\outputs\apk\release\*.apk apk\

# Linux/Mac
cp app/build/outputs/apk/release/*.apk apk/
```

### 5. اختبار التحميل

1. افتح: `https://your-app.onrender.com`
2. اضغط "تحميل التطبيق (APK)"
3. يجب أن يبدأ التحميل مباشرة

## 🔧 إعدادات مهمة

### تحديث API URL

في `app/build.gradle`:

```gradle
buildConfigField "String", "API_BASE_URL", '"https://your-actual-app.onrender.com/api"'
buildConfigField "String", "WS_BASE_URL", '"wss://your-actual-app.onrender.com/ws"'
```

### Signing APK (للإنتاج)

1. أنشئ keystore:
```bash
keytool -genkey -v -keystore keystore/release.keystore -alias arabchat -keyalg RSA -keysize 2048 -validity 10000
```

2. أضف متغيرات البيئة:
- `KEYSTORE_PASSWORD`
- `KEY_ALIAS`
- `KEY_PASSWORD`

## 📂 هيكل المشروع

```
.
├── app/                          # تطبيق Android
│   ├── src/main/
│   │   ├── java/com/arabchat/   # Kotlin code
│   │   ├── res/                  # Resources (layouts, drawables, etc.)
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── arab_chat/                    # Django Backend
│   ├── settings.py
│   └── urls.py
├── chat/                         # Django App
│   ├── download_views.py        # صفحة تحميل APK
│   ├── views.py
│   └── models.py
├── apk/                          # مجلد APK النهائي
├── keystore/                     # Keystore files
└── requirements.txt              # Python dependencies
```

## 🌐 API Endpoints

جميع الـ endpoints متصلة بـ Render:

- `POST /api/auth/request-otp/` - طلب OTP
- `POST /api/auth/verify-otp/` - التحقق من OTP
- `GET /api/chat/rooms/` - قائمة الدردشات
- `POST /api/chat/messages/` - إرسال رسالة
- `GET /download/apk/` - تحميل APK

## 📝 ملاحظات

- ✅ المشروع **Android-only** - لا توجد بقايا Web/Hybrid
- ✅ جميع الواجهات **Responsive** باستخدام dp/sp
- ✅ صفحة تحميل APK جاهزة على Render
- ✅ Network Layer كامل في Kotlin
- ✅ APK يعمل بدون Google Play Services

## 🚀 الخطوات التالية

1. ✅ رفع التغييرات إلى Git
2. ✅ نشر على Render
3. ⏳ بناء APK (استخدم Android Studio)
4. ⏳ نسخ APK إلى `/apk`
5. ⏳ اختبار التحميل من الرابط

---

**المشروع جاهز للنشر! 🎉**

