# API Testing Guide

دليل لاختبار API باستخدام Postman و Insomnia

---

## 1. إعداد Postman

### أ) إنشاء Collection جديد

1. افتح Postman
2. اضغط على "New" → "Collection"
3. اسم Collection: "Arab Chat API"
4. احفظ Collection

### ب) إضافة Environment

1. اضغط على "Environments" من القائمة
2. اضغط على "+" لإنشاء Environment جديد
3. اسم Environment: "Arab Chat - Production"

**أضف Variables:**

| Variable | Initial Value | Current Value |
|----------|--------------|---------------|
| `base_url` | `https://your-app.onrender.com` | `https://your-app.onrender.com` |
| `api_url` | `{{base_url}}/api` | `{{base_url}}/api` |
| `ws_url` | `wss://your-app.onrender.com` | `wss://your-app.onrender.com` |
| `token` | `` | `` |

4. احفظ Environment
5. اختر Environment من القائمة المنسدلة

---

## 2. اختبار Authentication

### أ) Get Auth Token

**Request:**
```
POST {{api_url}}/auth/login/
Headers:
    Content-Type: application/json
Body (JSON):
{
    "username": "testuser",
    "password": "password123"
}
```

**Expected Response:**
```json
{
    "token": "abc123def456..."
}
```

**Action:**
1. بعد الحصول على Token، احفظه في Environment Variable `token`
2. في Postman: Tests tab
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.token);
}
```

### ب) Get Current User

**Request:**
```
GET {{api_url}}/users/me/
Headers:
    Authorization: Token {{token}}
```

**Expected Response:**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    ...
}
```

---

## 3. اختبار Chat Rooms

### أ) List Rooms

**Request:**
```
GET {{api_url}}/rooms/
Headers:
    Authorization: Token {{token}}
```

### ب) Create Room

**Request:**
```
POST {{api_url}}/rooms/
Headers:
    Authorization: Token {{token}}
    Content-Type: application/json
Body (JSON):
{
    "name": "Test Room",
    "room_type": "group",
    "description": "Test description",
    "members": [1, 2, 3]
}
```

### ج) Room Details

**Request:**
```
GET {{api_url}}/rooms/1/
Headers:
    Authorization: Token {{token}}
```

---

## 4. اختبار Messages

### أ) List Messages

**Request:**
```
GET {{api_url}}/messages/?room=1
Headers:
    Authorization: Token {{token}}
Query Parameters:
    room: 1
    page: 1
    page_size: 50
```

### ب) Send Message

**Request:**
```
POST {{api_url}}/messages/
Headers:
    Authorization: Token {{token}}
    Content-Type: application/json
Body (JSON):
{
    "room": 1,
    "content": "Hello, this is a test message!",
    "message_type": "text"
}
```

### ج) Send Image Message

**Request:**
```
POST {{api_url}}/messages/
Headers:
    Authorization: Token {{token}}
Body (form-data):
    room: 1
    content: "Check this image!"
    message_type: image
    file: [Select File] (image.jpg)
```

### د) Mark as Read

**Request:**
```
POST {{api_url}}/messages/1/mark_read/
Headers:
    Authorization: Token {{token}}
```

---

## 5. اختبار Stories

### أ) List Stories Feed

**Request:**
```
GET {{api_url}}/stories/feed/
Headers:
    Authorization: Token {{token}}
```

### ب) Create Story

**Request:**
```
POST {{api_url}}/stories/
Headers:
    Authorization: Token {{token}}
Body (form-data):
    content_type: image
    content: [Select File] (image.jpg)
    caption: "My story"
```

### ج) View Story

**Request:**
```
POST {{api_url}}/story-views/
Headers:
    Authorization: Token {{token}}
Body (JSON):
{
    "story": 1
}
```

---

## 6. اختبار Friends

### أ) Send Friend Request

**Request:**
```
POST {{api_url}}/friend-requests/
Headers:
    Authorization: Token {{token}}
Body (JSON):
{
    "to_user": 2
}
```

### ب) Accept Friend Request

**Request:**
```
POST {{api_url}}/friend-requests/1/accept/
Headers:
    Authorization: Token {{token}}
```

### ج) List Friends

**Request:**
```
GET {{api_url}}/friends/
Headers:
    Authorization: Token {{token}}
```

---

## 7. اختبار Recent Contacts

### أ) List Recent Contacts

**Request:**
```
GET {{api_url}}/recent-contacts/
Headers:
    Authorization: Token {{token}}
```

### ب) Pin Contact

**Request:**
```
POST {{api_url}}/recent-contacts/1/pin/
Headers:
    Authorization: Token {{token}}
```

---

## 8. اختبار WebSocket

### أ) Notifications WebSocket

**استخدام أداة WebSocket مثل WebSocketKing أو wscat:**

```
URL: wss://your-app.onrender.com/ws/notifications/?token={{token}}
```

**Message Format:**
```json
{
    "type": "ping"
}
```

**Expected Response:**
```json
{
    "type": "notification",
    "payload": {
        "type": "new_message",
        "data": {...}
    }
}
```

### ب) Chat WebSocket

```
URL: wss://your-app.onrender.com/ws/chat/1/
```

**Send Message:**
```json
{
    "type": "chat_message",
    "message": "Hello!",
    "room_id": 1
}
```

**Receive Message:**
```json
{
    "type": "chat_message",
    "message": {
        "id": 123,
        "content": "Hello!",
        "sender": {...},
        "created_at": "..."
    }
}
```

---

## 9. Postman Collection Template

يمكنك حفظ هذا كـ Collection JSON:

```json
{
    "info": {
        "name": "Arab Chat API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Authentication",
            "item": [
                {
                    "name": "Login",
                    "request": {
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "url": {
                            "raw": "{{api_url}}/auth/login/",
                            "host": ["{{api_url}}"],
                            "path": ["auth", "login", ""]
                        },
                        "body": {
                            "mode": "raw",
                            "raw": "{\n    \"username\": \"testuser\",\n    \"password\": \"password123\"\n}"
                        }
                    }
                }
            ]
        }
    ]
}
```

---

## 10. اختبار في Insomnia

### أ) إعدادات مشابهة لـ Postman

1. إنشاء Request Group: "Arab Chat API"
2. إضافة Environment Variables
3. إضافة Requests لكل endpoint

### ب) استخدام Cookie Authentication

في Insomnia، يمكنك استخدام Cookie Authentication بدلاً من Token:

1. بعد Login، Insomnia سيحفظ Cookies تلقائياً
2. يمكنك استخدام Cookie Authentication للطلبات التالية

---

## 11. اختبار باستخدام curl

### Get Token
```bash
curl -X POST https://your-app.onrender.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

### Get Current User
```bash
curl -X GET https://your-app.onrender.com/api/users/me/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

### Send Message
```bash
curl -X POST https://your-app.onrender.com/api/messages/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "room": 1,
    "content": "Test message",
    "message_type": "text"
  }'
```

---

## 12. Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution:** تحقق من Token في Authorization header

### Issue: 403 Forbidden
**Solution:** تحقق من permissions - قد تحتاج authentication أو permissions خاصة

### Issue: 404 Not Found
**Solution:** تحقق من URL و API endpoint path

### Issue: 500 Server Error
**Solution:** تحقق من Server logs في Render Dashboard

### Issue: CORS Error (في Browser)
**Solution:** هذا طبيعي - Mobile Apps لا تواجه CORS issues

---

## 13. Testing Checklist

- [ ] Authentication (Login/Token) يعمل
- [ ] Get Current User يعمل
- [ ] List Rooms يعمل
- [ ] Create Room يعمل
- [ ] List Messages يعمل
- [ ] Send Message (text) يعمل
- [ ] Send Message (image) يعمل
- [ ] Mark as Read يعمل
- [ ] List Stories يعمل
- [ ] Create Story يعمل
- [ ] WebSocket Notifications يعمل
- [ ] WebSocket Chat يعمل

---

**ملاحظة:** استبدل `your-app.onrender.com` بـ النطاق الفعلي في Render

**Last Updated:** 2025-01-13

