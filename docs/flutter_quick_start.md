# Flutter App - Quick Start Guide

دليل سريع لبدء تطوير Flutter App

---

## ⚠️ **معلومة مهمة: Environment Variables في Render**

### ✅ **لا تحتاج إضافة Environment Variables جديدة في Render!**

**السبب:**
- ✅ Flutter App يستخدم **نفس URLs** الموجودة بالفعل
- ✅ Mobile Apps **لا تحتاج CORS** (لأنها ليست browsers)
- ✅ Backend **جاهز تماماً** لاستقبال طلبات من Flutter

**ما تحتاج فعله فقط:**
1. انسخ URL الخاص بك من Render
2. ضعه في `lib/config/app_config.dart` في Flutter Project
3. انتهى! ✅

---

## الخطوات السريعة

### 1. إنشاء Flutter Project

```bash
flutter create arab_chat_app
cd arab_chat_app
```

### 2. تحديث pubspec.yaml

انسخ محتوى `pubspec.yaml` من `docs/flutter_setup_guide.md`

```bash
# في ملف pubspec.yaml، ضع Dependencies المطلوبة
# ثم قم بتثبيت:
flutter pub get
```

### 3. إنشاء Structure

```bash
# إنشاء المجلدات
mkdir -p lib/config
mkdir -p lib/services
mkdir -p lib/models
mkdir -p lib/screens/auth
mkdir -p lib/screens/chats
mkdir -p lib/screens/stories
mkdir -p lib/screens/groups
mkdir -p lib/screens/calls
mkdir -p lib/screens/settings
mkdir -p lib/widgets
mkdir -p lib/utils
```

### 4. إنشاء الملفات الأساسية

انسخ الملفات من `docs/flutter_setup_guide.md`:

- ✅ `lib/config/app_config.dart` - **⚠️ غيّر URL هنا**
- ✅ `lib/config/theme_config.dart`
- ✅ `lib/services/storage_service.dart`
- ✅ `lib/services/api_service.dart`
- ✅ `lib/services/auth_service.dart`
- ✅ `lib/main.dart`

### 5. ⚠️ **مهم: تحديث App Config**

افتح `lib/config/app_config.dart` وغيّر:

```dart
class AppConfig {
  // ⚠️ غيّر هذا إلى URL الخاص بك
  static const String baseUrl = 'https://YOUR-APP.onrender.com';
  // استبدل YOUR-APP بـ اسم تطبيقك في Render
  
  static const String apiBaseUrl = '$baseUrl/api';
  static const String wsBaseUrl = 'wss://YOUR-APP.onrender.com';
  // ...
}
```

### 6. تشغيل التطبيق

```bash
# على جهاز Android متصل
flutter run

# أو على Emulator
flutter emulators
flutter emulators --launch <emulator_id>
flutter run
```

---

## 📁 Structure الكامل

```
arab_chat_app/
├── lib/
│   ├── main.dart                    ✅ موجود
│   ├── config/
│   │   ├── app_config.dart          ✅ إنشاؤه
│   │   └── theme_config.dart        ✅ إنشاؤه
│   ├── services/
│   │   ├── api_service.dart         ✅ إنشاؤه
│   │   ├── auth_service.dart        ✅ إنشاؤه
│   │   ├── storage_service.dart     ✅ إنشاؤه
│   │   └── websocket_service.dart   ⏳ المرحلة التالية
│   ├── models/                      ⏳ المرحلة التالية
│   ├── screens/                     ⏳ المرحلة التالية
│   ├── widgets/                     ⏳ المرحلة التالية
│   └── utils/                       ⏳ المرحلة التالية
├── pubspec.yaml                     ✅ محدث
└── android/                         ✅ موجود
```

---

## ✅ Checklist

- [ ] تثبيت Flutter SDK
- [ ] إنشاء Flutter Project
- [ ] تحديث pubspec.yaml
- [ ] تثبيت Dependencies (`flutter pub get`)
- [ ] إنشاء Structure (المجلدات)
- [ ] إنشاء ملفات Config
- [ ] إنشاء ملفات Services
- [ ] **تحديث App Config بـ URL الخاص بك**
- [ ] تحديث main.dart
- [ ] تشغيل التطبيق (`flutter run`)
- [ ] اختبار التطبيق

---

## 🔗 روابط مهمة

- [Flutter Setup Guide](./flutter_setup_guide.md) - الدليل التفصيلي الكامل
- [API Documentation](./api_endpoints.md) - توثيق API
- [API Testing Guide](./api_testing_guide.md) - دليل اختبار API
- [Render Environment Checklist](./render_environment_checklist.md) - ✅ لا تحتاج إضافة شيء

---

## ❓ أسئلة شائعة

### Q: هل أحتاج إضافة Environment Variables في Render؟
**A:** ❌ **لا!** كل شيء موجود. فقط ضع URL في Flutter Config.

### Q: كيف أحصل على URL الخاص بي في Render?
**A:** اذهب إلى Render Dashboard → اختر Service → URL موجود في الأعلى

### Q: هل أحتاج تغيير شيء في Backend؟
**A:** ❌ **لا!** Backend جاهز تماماً. Flutter سيستخدم نفس API.

### Q: متى أبدأ بتطوير الشاشات؟
**A:** بعد إكمال Setup الأساسي (هذه الخطوة) → المرحلة التالية.

---

**Last Updated:** 2025-01-13

