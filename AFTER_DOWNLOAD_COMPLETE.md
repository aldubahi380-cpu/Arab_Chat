# ماذا تفعل بعد اكتمال تحميل Gradle؟

## ✅ لا حاجة لفك الضغط يدوياً!

**Gradle Wrapper سيفك الضغط تلقائياً** ويضع الملفات في المكان الصحيح.

## 📋 الخطوات بعد اكتمال التحميل:

### 1️⃣ التحقق من أن Gradle يعمل

**في Terminal في Android Studio** (أو PowerShell):
```bash
.\gradlew.bat --version
```

إذا ظهر رقم الإصدار (مثل `Gradle 8.2`)، يعني أن كل شيء يعمل ✅

### 2️⃣ تحديث API URL (مهم جداً!)

**في Android Studio**:
1. افتح ملف `app/build.gradle`
2. ابحث عن السطر 22:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
   ```
3. **استبدل `your-app.onrender.com`** بـ URL السيرفر الفعلي من Render
   - مثال: إذا كان URL هو `https://arab-chat-abc123.onrender.com`
   - استبدله بـ:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://arab-chat-abc123.onrender.com/api"'
   ```
4. حدث أيضاً السطر 23:
   ```gradle
   buildConfigField "String", "WS_BASE_URL", '"wss://arab-chat-abc123.onrender.com/ws"'
   ```
5. **احفظ الملف**: `Ctrl + S`

### 3️⃣ بناء APK

**الطريقة 1: من Terminal**
```bash
.\gradlew.bat assembleRelease
```

**الطريقة 2: من Android Studio**
- من القائمة: **Build > Build Bundle(s) / APK(s) > Build APK(s)**

### 4️⃣ نسخ APK إلى مجلد /apk

بعد اكتمال البناء:
```bash
copy app\build\outputs\apk\release\*.apk apk\
```

### 5️⃣ رفع APK إلى Git

```bash
git add apk/*.apk
git commit -m "Add APK file"
git push origin main
```

---

## 🎯 الخطوة التالية الآن:

**بعد اكتمال تحميل `gradle-8.2-bin.zip`**:

1. **في Terminal**: شغّل `.\gradlew.bat --version` للتحقق
2. **حدث API URL** في `app/build.gradle`
3. **ابني APK**: `.\gradlew.bat assembleRelease`

---

**ملاحظة**: Gradle سيضع الملفات في: `C:\Users\YourName\.gradle\wrapper\dists\gradle-8.2-bin\...`

**لا تحتاج لفعل شيء - كل شيء تلقائي!** ✅

