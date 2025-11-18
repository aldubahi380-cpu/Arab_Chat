# خطوات بناء APK في Android Studio - خطوة بخطوة

## ✅ أنت الآن في Android Studio - اتبع هذه الخطوات:

### 1️⃣ انتظر حتى يكتمل Gradle Sync
- في أسفل Android Studio، ستجد شريط تقدم "Gradle Sync"
- انتظر حتى يظهر "Gradle sync completed" أو "Gradle build finished"
- إذا ظهرت أخطاء، أخبرني

### 2️⃣ حدث API URL (مهم جداً!)

1. **افتح ملف `app/build.gradle`** (يبدو أنه مفتوح بالفعل)
2. **ابحث عن السطر 22** الذي يحتوي على:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
   ```
3. **استبدل `your-app.onrender.com`** بـ URL السيرفر الفعلي من Render
   - مثال: إذا كان URL هو `https://arab-chat-abc123.onrender.com`
   - استبدله بـ:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://arab-chat-abc123.onrender.com/api"'
   ```
4. **حدث أيضاً السطر 23** (WS_BASE_URL):
   ```gradle
   buildConfigField "String", "WS_BASE_URL", '"wss://arab-chat-abc123.onrender.com/ws"'
   ```
5. **احفظ الملف**: `Ctrl + S`

### 3️⃣ بناء APK

**الطريقة 1: من القائمة**
1. من القائمة العلوية: **Build**
2. اختر: **Build Bundle(s) / APK(s)**
3. اختر: **Build APK(s)**
4. انتظر حتى يكتمل البناء (1-2 دقيقة)

**الطريقة 2: من Terminal في Android Studio**
1. افتح Terminal في أسفل Android Studio
2. اكتب:
   ```bash
   .\gradlew.bat assembleRelease
   ```
   (أو `./gradlew assembleRelease` على Linux/Mac)

### 4️⃣ التحقق من نجاح البناء

بعد اكتمال البناء:
1. في أسفل Android Studio، ستجد إشعار: **"APK(s) generated successfully"**
2. اضغط على **"locate"** في الإشعار
3. أو افتح: `app/build/outputs/apk/release/`
4. يجب أن تجد ملف: `ArabChat-release-v1.0.0-1.apk`

### 5️⃣ نسخ APK إلى مجلد /apk

**من Terminal في Android Studio:**
```bash
copy app\build\outputs\apk\release\*.apk apk\
```

**أو يدوياً:**
1. افتح `app/build/outputs/apk/release/` في File Explorer
2. انسخ ملف `.apk`
3. الصقه في مجلد `apk/` في جذر المشروع

### 6️⃣ رفع APK إلى Git

**من Terminal في Android Studio:**
```bash
git add apk/*.apk
git commit -m "Add APK file for download"
git push origin main
```

### 7️⃣ انتظر نشر Render

- بعد `git push`، Render سينشر التحديثات تلقائياً
- انتظر 1-2 دقيقة

### 8️⃣ اختبار التحميل

افتح: `https://your-app.onrender.com` واضغط "تحميل التطبيق" ✅

---

## ⚠️ إذا واجهت مشاكل:

### مشكلة: "Gradle sync failed"
- انتظر قليلاً ثم حاول: **File > Sync Project with Gradle Files**

### مشكلة: "Build failed"
- تحقق من الأخطاء في تبويب **Build** في أسفل Android Studio
- تأكد من تحديث API URL بشكل صحيح

### مشكلة: "No APK found"
- تأكد من بناء **Release** وليس Debug
- تحقق من: `app/build/outputs/apk/release/`

---

**ابدأ بالخطوة 1️⃣ الآن!** 🚀

