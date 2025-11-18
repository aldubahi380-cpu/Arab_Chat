# ✅ Gradle يعمل الآن - الخطوات التالية

## 🎉 ممتاز! Gradle 8.2 يعمل بنجاح

الآن اتبع هذه الخطوات بالترتيب:

## 1️⃣ تحديث API URL (مهم جداً!)

### في Android Studio:

1. **افتح ملف `app/build.gradle`**
2. **ابحث عن السطر 22**:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
   ```
3. **استبدل `your-app.onrender.com`** بـ URL السيرفر الفعلي من Render
   
   **مثال**: إذا كان URL هو `https://arab-chat-abc123.onrender.com`
   
   **استبدله بـ**:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://arab-chat-abc123.onrender.com/api"'
   ```

4. **حدث أيضاً السطر 23**:
   ```gradle
   buildConfigField "String", "WS_BASE_URL", '"wss://arab-chat-abc123.onrender.com/ws"'
   ```

5. **احفظ الملف**: `Ctrl + S`

## 2️⃣ بناء APK

### في Terminal في Android Studio:

```bash
.\gradlew.bat assembleRelease
```

**انتظر** حتى يكتمل البناء (2-5 دقائق)

## 3️⃣ التحقق من APK

بعد اكتمال البناء، APK سيكون في:
```
app\build\outputs\apk\release\ArabChat-release-v1.0.0-1.apk
```

## 4️⃣ نسخ APK إلى مجلد /apk

```bash
copy app\build\outputs\apk\release\*.apk apk\
```

## 5️⃣ رفع APK إلى Git

```bash
git add apk/*.apk
git commit -m "Add APK file for download"
git push origin main
```

## 6️⃣ انتظر نشر Render

بعد `git push`، Render سينشر APK تلقائياً (1-2 دقيقة)

## 7️⃣ اختبار التحميل

افتح: `https://your-app.onrender.com` واضغط "تحميل التطبيق" ✅

---

## 🚀 ابدأ الآن:

**الخطوة 1**: حدث API URL في `app/build.gradle` ثم احفظ

**الخطوة 2**: شغّل `.\gradlew.bat assembleRelease` في Terminal

---

**ما هو URL السيرفر الفعلي على Render؟** (مثل: `https://arab-chat-xxxxx.onrender.com`)

