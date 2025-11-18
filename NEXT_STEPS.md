# الخطوة التالية - حل مشكلة Gradle Wrapper

## 🔍 المشكلة الحالية

الخطأ: `Could not find or load main class org.gradle.wrapper.GradleWrapperMain`

**السبب**: ملف `gradle-wrapper.jar` غير موجود في `gradle/wrapper/`

## ✅ الحل: استخدام Android Studio (الأسهل والأضمن)

### الطريقة الموصى بها:

1. **في Android Studio**:
   - من القائمة: **File**
   - اختر: **Sync Project with Gradle Files**
   - Android Studio سينشئ `gradle-wrapper.jar` تلقائياً ✅

2. **انتظر** حتى يكتمل Sync (2-3 دقائق)

3. **بعد اكتمال Sync**:
   - `gradle-wrapper.jar` سيكون موجوداً تلقائياً
   - يمكنك بناء APK مباشرة

## 🚀 بعد حل المشكلة - الخطوات التالية:

### 1️⃣ تحديث API URL
افتح `app/build.gradle` وحدث السطر 22:
```gradle
buildConfigField "String", "API_BASE_URL", '"https://YOUR-ACTUAL-APP.onrender.com/api"'
```

### 2️⃣ بناء APK
- من القائمة: **Build > Build Bundle(s) / APK(s) > Build APK(s)**

### 3️⃣ نسخ APK
```bash
copy app\build\outputs\apk\release\*.apk apk\
```

### 4️⃣ رفع إلى Git
```bash
git add apk/*.apk
git commit -m "Add APK file"
git push origin main
```

---

## ⚡ الحل السريع الآن:

**في Android Studio**: **File > Sync Project with Gradle Files** وانتظر! 🚀

