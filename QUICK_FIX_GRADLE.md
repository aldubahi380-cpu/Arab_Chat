# حل سريع: Gradle Wrapper غير موجود

## ✅ الحل الأسرع

**Android Studio سينشئ Gradle Wrapper تلقائياً!**

### خطوات بسيطة:

1. **من القائمة العلوية**: **File**
2. اختر: **Sync Project with Gradle Files**
3. **انتظر** حتى يكتمل (2-3 دقائق)
4. Android Studio سينشئ `gradlew.bat` تلقائياً ✅

## أو من Terminal:

إذا كان Gradle مثبتاً على النظام:
```bash
gradle wrapper --gradle-version 8.2
```

## بعد ذلك:

بعد Sync، جرب:
```bash
.\gradlew.bat --version
```

---

**الآن**: جرب **File > Sync Project with Gradle Files** وانتظر! 🚀

