# تحديث API URL في build.gradle

## الطريقة 1: تعديل يدوي في Android Studio

الملف `app/build.gradle` مفتوح بالفعل. اتبع هذه الخطوات:

### 1. ابحث عن السطر 22 و 23:
```gradle
buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
buildConfigField "String", "WS_BASE_URL", '"wss://your-app.onrender.com/ws"'
```

### 2. استبدل `your-app.onrender.com` بـ URL السيرفر الفعلي

**مثال**: إذا كان URL هو `https://arab-chat-abc123.onrender.com`

**استبدله بـ**:
```gradle
buildConfigField "String", "API_BASE_URL", '"https://arab-chat-abc123.onrender.com/api"'
buildConfigField "String", "WS_BASE_URL", '"wss://arab-chat-abc123.onrender.com/ws"'
```

### 3. حدث أيضاً السطر 56 و 57 (في buildTypes > release):
```gradle
buildConfigField "String", "API_BASE_URL", '"https://arab-chat-abc123.onrender.com/api"'
buildConfigField "String", "WS_BASE_URL", '"wss://arab-chat-abc123.onrender.com/ws"'
```

### 4. احفظ الملف: `Ctrl + S`

---

## الطريقة 2: من Terminal (إذا أعطيتني URL)

أخبرني بـ URL السيرفر وسأعدل الملف تلقائياً!

---

**ما هو URL السيرفر الفعلي على Render؟**

