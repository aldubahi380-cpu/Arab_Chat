# 🚀 بناء APK بسرعة - خطوات سريعة

## المشكلة
الصفحة تظهر لكن التحميل لا يعمل لأن **APK غير موجود في مجلد `/apk`**.

## الحل السريع (5 خطوات)

### 1️⃣ افتح المشروع في Android Studio
- File > Open > اختر مجلد المشروع

### 2️⃣ حدث API URL
افتح `app/build.gradle` وحدث السطر 22:
```gradle
buildConfigField "String", "API_BASE_URL", '"https://YOUR-ACTUAL-APP.onrender.com/api"'
```
(استبدل `YOUR-ACTUAL-APP` بـ URL السيرفر الفعلي)

### 3️⃣ بناء APK
- من القائمة: **Build > Build Bundle(s) / APK(s) > Build APK(s)**
- انتظر حتى يكتمل (1-2 دقيقة)

### 4️⃣ نسخ APK
```bash
# Windows PowerShell
copy app\build\outputs\apk\release\*.apk apk\
```

### 5️⃣ رفع إلى Git
```bash
git add apk/*.apk
git commit -m "Add APK file"
git push origin main
```

## ✅ بعد 1-2 دقيقة
افتح: `https://your-app.onrender.com` واضغط "تحميل التطبيق" ✅

---

**ملاحظة**: إذا لم يكن لديك Android Studio، ثبتّه من: https://developer.android.com/studio

