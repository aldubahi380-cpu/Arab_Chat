# Arab Chat - Android Native App

تطبيق دردشة أندرويد أصلي مبني بـ Kotlin يتصل مع سيرفر Django على Render.

## البنية

```
app/
├── src/main/
│   ├── java/com/arabchat/
│   │   ├── data/
│   │   │   ├── api/          # API Service و Retrofit
│   │   │   ├── model/        # Data Models
│   │   │   └── repository/   # Repository Pattern
│   │   ├── ui/
│   │   │   ├── auth/         # شاشات المصادقة
│   │   │   ├── main/         # MainActivity
│   │   │   ├── chat/         # شاشات الدردشة
│   │   │   ├── contacts/     # جهات الاتصال
│   │   │   ├── stories/      # الاستوريات
│   │   │   └── settings/     # الإعدادات
│   │   └── util/             # Utilities
│   └── res/                  # Resources
└── build.gradle
```

## الإعداد

1. افتح المشروع في Android Studio
2. قم بتحديث `API_BASE_URL` في `app/build.gradle`:
   ```gradle
   buildConfigField "String", "API_BASE_URL", '"https://your-app.onrender.com/api"'
   ```
3. قم ببناء المشروع (Build > Make Project)

## الميزات

- ✅ مصادقة عبر OTP
- ✅ قائمة الدردشات
- ✅ إرسال واستقبال الرسائل
- ✅ واجهة مستخدم شبيهة بـ WhatsApp
- ✅ دعم RTL للغة العربية

## API Endpoints المستخدمة

- `POST /api/otp/request/` - طلب رمز OTP
- `POST /api/otp/verify/` - التحقق من OTP
- `GET /api/rooms/` - الحصول على الدردشات
- `GET /api/messages/` - الحصول على الرسائل
- `POST /api/messages/` - إرسال رسالة

## ملاحظات

- التطبيق يستخدم Token Authentication
- جميع الطلبات تتضمن Header: `Authorization: Token <token>`
- للتطوير المحلي، استخدم `10.0.2.2` بدلاً من `localhost`

