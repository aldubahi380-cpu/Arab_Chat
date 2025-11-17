# تعليمات بناء APK

## المتطلبات

1. **Android Studio** - للتطوير والبناء
2. **JDK 17+** - Java Development Kit
3. **Android SDK** - من خلال Android Studio

## خطوات البناء

### 1. فتح المشروع في Android Studio

1. افتح Android Studio
2. اختر `Open` واختر مجلد المشروع
3. انتظر حتى يكتمل Gradle Sync

### 2. تحديث API URL (مهم!)

افتح `app/build.gradle` وتأكد من أن `API_BASE_URL` يشير إلى سيرفر Render:

```gradle
buildTypes {
    release {
        buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
        buildConfigField "String", "WS_BASE_URL", '"wss://your-app.onrender.com"'
    }
    debug {
        buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
        buildConfigField "String", "WS_BASE_URL", '"wss://your-app.onrender.com"'
    }
}
```

### 3. بناء APK Release

#### الطريقة 1: من Android Studio

1. من القائمة: `Build > Build Bundle(s) / APK(s) > Build APK(s)`
2. انتظر حتى يكتمل البناء
3. APK سيكون في: `app/build/outputs/apk/release/`

#### الطريقة 2: من Terminal

```bash
# Windows
gradlew.bat assembleRelease

# Linux/Mac
./gradlew assembleRelease
```

### 4. نسخ APK إلى مجلد /apk

بعد بناء APK:

```bash
# Windows
copy app\build\outputs\apk\release\*.apk apk\

# Linux/Mac
cp app/build/outputs/apk/release/*.apk apk/
```

### 5. تسمية APK

APK سيتم تسميته تلقائياً: `ArabChat-release-v1.0.0-1.apk`

يمكنك تغيير الاسم في `app/build.gradle`:

```gradle
android.applicationVariants.all { variant ->
    variant.outputs.all {
        outputFileName = "ArabChat-${variant.name}-v${variant.versionName}-${variant.versionCode}.apk"
    }
}
```

## Signing APK (للإنتاج)

للإنتاج، يجب توقيع APK:

1. أنشئ keystore:
```bash
keytool -genkey -v -keystore keystore/release.keystore -alias arabchat -keyalg RSA -keysize 2048 -validity 10000
```

2. أضف متغيرات البيئة:
```bash
KEYSTORE_PASSWORD=your_password
KEY_ALIAS=arabchat
KEY_PASSWORD=your_password
```

3. `app/build.gradle` يحتوي على signing config جاهز

## اختبار APK

1. انقل APK إلى هاتف Android
2. فعّل "التثبيت من مصادر غير معروفة"
3. افتح APK واتبع التعليمات
4. اختبر التطبيق

## حجم APK المتوقع

- بدون ProGuard: ~20-25 MB
- مع ProGuard: ~10-15 MB

## ملاحظات

- تأكد من تحديث `API_BASE_URL` قبل البناء
- APK يعمل بدون Google Play Services
- للتثبيت، يجب تفعيل "التثبيت من مصادر غير معروفة"

