# إنشاء Gradle Wrapper في Android Studio

## المشكلة
`gradlew.bat` غير موجود - يجب إنشاء Gradle Wrapper أولاً

## الحل: إنشاء Gradle Wrapper من Android Studio

### الطريقة 1: من القائمة (الأسهل)

1. **من القائمة العلوية**: **File**
2. اختر: **Settings** (أو **Preferences** على Mac)
3. في البحث، اكتب: **"Gradle"**
4. في قسم **Gradle**:
   - تأكد من أن **"Use Gradle from"** = **"Specified location"** أو **"gradle-wrapper.properties file"**
   - إذا لم يكن موجوداً، اختر **"Use default gradle wrapper"**
5. اضغط **OK**

### الطريقة 2: من Terminal في Android Studio

1. **افتح Terminal** في أسفل Android Studio
2. اكتب:
   ```bash
   gradle wrapper --gradle-version 8.2
   ```
   (إذا كان Gradle مثبتاً على النظام)

### الطريقة 3: استخدام Android Studio لإنشاء Wrapper تلقائياً

1. **File > Sync Project with Gradle Files**
2. Android Studio سينشئ Gradle wrapper تلقائياً إذا لم يكن موجوداً

## ✅ بعد إنشاء Wrapper

بعد إنشاء Gradle wrapper:
1. ستجد ملفات: `gradlew.bat` و `gradlew` في جذر المشروع
2. جرب مرة أخرى:
   ```bash
   .\gradlew.bat --version
   ```

---

**جرب الطريقة 1 أولاً** - Android Studio سينشئ Wrapper تلقائياً عند Sync!

