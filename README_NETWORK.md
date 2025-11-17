# Network Layer - طبقة الشبكة

## نظرة عامة

تم إعادة كتابة طبقة الشبكة بالكامل في Kotlin لتتوافق مع Django REST Framework API على Render.

## API Endpoints

### Authentication (المصادقة)

#### 1. إرسال رمز OTP
- **Endpoint**: `POST /api/otp/request/`
- **Body**: 
  ```json
  {
    "phone": "+966501234567",
    "username": "username"
  }
  ```
- **Response**: 
  ```json
  {
    "message": "✅ تم إرسال رمز التحقق بنجاح",
    "success": true,
    "phone": "+966501234567"
  }
  ```

#### 2. التحقق من OTP
- **Endpoint**: `POST /api/otp/verify/`
- **Body**:
  ```json
  {
    "phone": "+966501234567",
    "otp_code": "123456",
    "username": "username",
    "device_id": "device_id",
    "device_name": "Samsung Galaxy",
    "platform": "android"
  }
  ```
- **Response**:
  ```json
  {
    "token": "auth_token_here",
    "user": { ... },
    "session": { ... },
    "success": true
  }
  ```

### Messages (الرسائل)

#### 1. إرسال رسالة نصية
- **Endpoint**: `POST /api/messages/`
- **Body**:
  ```json
  {
    "room": 1,
    "content": "مرحبا",
    "message_type": "text"
  }
  ```

#### 2. إرسال رسالة مع ملف
- **Endpoint**: `POST /api/messages/` (Multipart)
- **Form Data**:
  - `room`: roomId (Int)
  - `message_type`: "image" | "video" | "audio" | "file"
  - `file`: File
  - `content`: String (optional)

#### 3. الحصول على الرسائل
- **Endpoint**: `GET /api/messages/?room={roomId}&page={page}`
- **Response**: Paginated results

### Chat Rooms (غرف الدردشة)

#### 1. الحصول على جميع الغرف
- **Endpoint**: `GET /api/rooms/`

#### 2. تحديثات قائمة الدردشات
- **Endpoint**: `GET /api/rooms/chat_list_updates/`

### Push Notifications (الإشعارات)

#### 1. تسجيل Device Token
- **Endpoint**: `POST /api/device-tokens/`
- **Body**:
  ```json
  {
    "token": "fcm_token_here",
    "device_type": "android",
    "device_id": "device_id",
    "device_name": "Samsung Galaxy"
  }
  ```

## الاستخدام في الكود

### AuthRepository
```kotlin
val authRepository = AuthRepository(apiService)

// إرسال OTP
authRepository.requestOTP(phone, username)

// التحقق من OTP
authRepository.verifyOTP(phone, otpCode, username, deviceId, deviceName)
```

### ChatRepository
```kotlin
val chatRepository = ChatRepository(apiService)

// إرسال رسالة نصية
chatRepository.sendMessage(roomId, "مرحبا")

// إرسال صورة
chatRepository.sendMediaMessage(roomId, imageFile, "image", "وصف الصورة")
```

## ملاحظات

- جميع الطلبات تتطلب Token Authentication في Header: `Authorization: Token <token>`
- يتم إضافة Token تلقائياً عبر `AuthInterceptor`
- API Base URL يتم ضبطه في `build.gradle` حسب build type (debug/release)

