# أين Gradle في Android Studio؟

## 🔍 كيفية التحقق من Gradle Sync

### 1️⃣ شريط الحالة في أسفل Android Studio

انظر إلى **الأسفل** في Android Studio:
- ستجد شريط في أسفل النافذة
- إذا كان Gradle Sync يعمل، ستجد: **"Gradle sync in progress..."** أو **"Indexing..."**
- إذا اكتمل، ستجد: **"Gradle sync completed"** أو **"Gradle build finished"**

### 2️⃣ من القائمة

1. **File** (في القائمة العلوية)
2. اختر: **Sync Project with Gradle Files**
   - إذا كان Gradle Sync يعمل، ستجد: "Syncing..."
   - إذا اكتمل، لن يحدث شيء (يعني أنه مكتمل)

### 3️⃣ من Event Log

1. في **أسفل يمين** Android Studio، ابحث عن أيقونة **Event Log** (مربع صغير)
2. اضغط عليها لرؤية أحداث Gradle

### 4️⃣ من Terminal

1. افتح **Terminal** في أسفل Android Studio
2. اكتب:
   ```bash
   .\gradlew.bat --version
   ```
   - إذا ظهر رقم الإصدار، Gradle يعمل ✅
   - إذا ظهر خطأ، Gradle غير مثبت ❌

## ⚠️ إذا كان Gradle Sync لا يزال يعمل

- **انتظر** حتى يكتمل (قد يستغرق 2-5 دقائق في المرة الأولى)
- **لا تغلق** Android Studio أثناء Sync
- إذا استغرق وقتاً طويلاً، جرب: **File > Invalidate Caches / Restart**

## ✅ علامات اكتمال Gradle Sync

- اختفاء "loading..." من Project Explorer
- ظهور هيكل المشروع كاملاً في الجانب الأيسر
- عدم وجود أخطاء حمراء في تبويب **Build** في الأسفل

---

**الآن**: انظر إلى **أسفل Android Studio** وأخبرني ماذا ترى؟ هل يوجد "Gradle sync..." أم "completed"؟

