# بناء APK للتطبيق

## الخطوات

### 1. تحديث API URL

قبل البناء، قم بتحديث URL السيرفر في `app/build.gradle`:

```gradle
buildConfigField "String", "API_BASE_URL", '"https://your-actual-app.onrender.com/api"'
```

### 2. بناء APK Release

#### باستخدام Android Studio:
1. افتح المشروع في Android Studio
2. Build > Generate Signed Bundle / APK
3. اختر APK
4. اختر Release
5. استخدم debug keystore (للتطوير) أو أنشئ keystore جديد (للإنتاج)
6. Build

#### باستخدام Gradle Command Line:
```bash
# Windows
.\gradlew assembleRelease

# Linux/Mac
./gradlew assembleRelease
```

### 3. موقع APK

بعد البناء، سيكون APK في:
```
app/build/outputs/apk/release/ArabChat-release-v1.0.0-1.apk
```

### 4. نسخ APK إلى مجلد /apk

```bash
# Windows PowerShell
Copy-Item "app\build\outputs\apk\release\*.apk" -Destination "apk\" -Force

# Linux/Mac
cp app/build/outputs/apk/release/*.apk apk/
```

## ملاحظات

- للتطوير: استخدم debug keystore
- للإنتاج: أنشئ keystore خاص وضعه في `keystore/` مع تحديث `signingConfigs` في `build.gradle`
- حجم APK المتوقع: ~15-25 MB
- التطبيق يعمل بدون Google Play (Standalone APK)

