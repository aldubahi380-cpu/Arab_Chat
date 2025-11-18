# كيفية تحديث API URL - شرح مختصر

## ✅ أنت في الملف الصحيح: `app/build.gradle`

## 📝 الأسطر التي تغيرها:

### 1️⃣ السطر 22:
```gradle
buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
```

**استبدل**: `your-app.onrender.com`  
**بـ**: URL السيرفر الفعلي من Render

**مثال**: إذا كان URL هو `https://arab-chat-abc123.onrender.com`
```gradle
buildConfigField "String", "API_BASE_URL", '"https://arab-chat-abc123.onrender.com/api"'
```

---

### 2️⃣ السطر 23:
```gradle
buildConfigField "String", "WS_BASE_URL", '"wss://your-app.onrender.com/ws"'
```

**استبدل**: `your-app.onrender.com`  
**بـ**: نفس URL السيرفر الفعلي

**مثال**:
```gradle
buildConfigField "String", "WS_BASE_URL", '"wss://arab-chat-abc123.onrender.com/ws"'
```

---

### 3️⃣ السطر 56 (في buildTypes > release):
```gradle
buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
```

**نفس التغيير**: استبدل `your-app.onrender.com` بـ URL السيرفر الفعلي

---

### 4️⃣ السطر 57 (في buildTypes > release):
```gradle
buildConfigField "String", "WS_BASE_URL", '"wss://your-app.onrender.com/ws"'
```

**نفس التغيير**: استبدل `your-app.onrender.com` بـ URL السيرفر الفعلي

---

## 🎯 ملخص:

1. **ابحث عن**: `your-app.onrender.com`
2. **استبدله بـ**: URL السيرفر الفعلي (مثل: `arab-chat-abc123.onrender.com`)
3. **في 4 أماكن**: السطر 22، 23، 56، 57
4. **احفظ**: `Ctrl + S`

---

## ❓ ما هو URL السيرفر الفعلي؟

افتح Render Dashboard وابحث عن:
- Service URL
- أو Application URL
- أو Production URL

مثال: `https://arab-chat-xxxxx.onrender.com`

---

**بعد التعديل، احفظ الملف ثم شغّل**: `.\gradlew.bat assembleRelease`

