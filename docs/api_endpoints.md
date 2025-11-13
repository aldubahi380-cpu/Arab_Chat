# API Documentation - Arab Chat Backend

هذا الملف يوثق جميع API endpoints المتاحة للتطبيق.

**Base URL:** `https://your-app.onrender.com/api/`

## Authentication

جميع الـ endpoints تحتاج Authentication ما لم يُذكر خلاف ذلك.

### طريقة Authentication:
```
Authorization: Token <your-token>
```

### الحصول على Token:
```
POST /api/auth/login/
Body: {
    "username": "username",
    "password": "password"
}
Response: {
    "token": "xxxxxxxxxxxx"
}
```

---

## Users & Profiles

### Get Current User
```
GET /api/users/me/
Response: {
    "id": 1,
    "username": "username",
    "email": "email@example.com",
    ...
}
```

### Get Auth Token
```
GET /api/users/auth_token/
Response: {
    "token": "xxxxxxxxxxxx",
    "created": false
}
```

### Logout
```
POST /api/users/logout/
Body: {
    "session_token": "...",
    "device_id": "..."
}
Response: {
    "success": true
}
```

### Delete Account
```
DELETE /api/users/delete_account/
Response: {
    "message": "تم طلب حذف الحساب"
}
```

### User CRUD
```
GET    /api/users/          # List all users
POST   /api/users/          # Create user
GET    /api/users/{id}/     # Get user details
PUT    /api/users/{id}/     # Update user
DELETE /api/users/{id}/     # Delete user
```

### User Profile
```
GET    /api/profiles/       # List all profiles
POST   /api/profiles/       # Create profile
GET    /api/profiles/{id}/  # Get profile details
PUT    /api/profiles/{id}/  # Update profile
DELETE /api/profiles/{id}/  # Delete profile
```

---

## Chat Rooms

### List Rooms
```
GET /api/rooms/
Response: [
    {
        "id": 1,
        "name": "Room Name",
        "room_type": "private",
        "members": [...],
        ...
    }
]
```

### Create Room
```
POST /api/rooms/
Body: {
    "name": "Room Name",
    "room_type": "group",
    "description": "...",
    "members": [user_ids]
}
```

### Room Details
```
GET /api/rooms/{id}/
PUT /api/rooms/{id}/
DELETE /api/rooms/{id}/
```

### Join Room
```
POST /api/rooms/{id}/join/
```

### Leave Room
```
POST /api/rooms/{id}/leave/
```

### Invite to Room
```
POST /api/rooms/{id}/invite/
Body: {
    "user_ids": [1, 2, 3]
}
```

---

## Messages

### List Messages
```
GET /api/messages/?room={room_id}
Query Parameters:
    - room: Room ID
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50)
Response: {
    "count": 100,
    "next": "...",
    "previous": null,
    "results": [...]
}
```

### Send Message
```
POST /api/messages/
Body: {
    "room": room_id,
    "content": "Message text",
    "message_type": "text",  # text, image, video, audio, file
    "file": <file>  # للوسائط
}
Response: {
    "id": 123,
    "content": "Message text",
    "sender": {...},
    "created_at": "...",
    ...
}
```

### Message Details
```
GET /api/messages/{id}/
PUT /api/messages/{id}/     # Edit message
DELETE /api/messages/{id}/  # Delete message
```

### Mark as Read
```
POST /api/messages/{id}/mark_read/
```

### Pin Message
```
POST /api/messages/{id}/pin/
```

### Unpin Message
```
POST /api/messages/{id}/unpin/
```

### Reply to Message
```
POST /api/messages/{id}/reply/
Body: {
    "content": "Reply text"
}
```

### Forward Message
```
POST /api/messages/{id}/forward/
Body: {
    "room_ids": [1, 2, 3]
}
```

---

## Message Reads

### List Read Status
```
GET /api/message-reads/
GET /api/message-reads/?message={message_id}
```

### Mark as Read
```
POST /api/message-reads/
Body: {
    "message": message_id
}
```

---

## OTP Verification

### Request OTP
```
POST /api/otp/
Body: {
    "phone": "+1234567890"
}
Response: {
    "otp_code": "123456",
    "expires_at": "..."
}
```

### Verify OTP
```
POST /api/otp/{id}/verify/
Body: {
    "otp_code": "123456"
}
Response: {
    "is_verified": true,
    "user": {...}  # إذا تم إنشاء حساب جديد
}
```

---

## Friends

### List Friends
```
GET /api/friends/
Response: [
    {
        "id": 1,
        "friend": {
            "id": 2,
            "username": "friend_username",
            ...
        }
    }
]
```

### Add Friend
```
POST /api/friends/
Body: {
    "friend": user_id
}
```

### Remove Friend
```
DELETE /api/friends/{id}/
```

### Friend Requests

#### List Friend Requests
```
GET /api/friend-requests/
```

#### Send Friend Request
```
POST /api/friend-requests/
Body: {
    "to_user": user_id
}
```

#### Accept Friend Request
```
POST /api/friend-requests/{id}/accept/
```

#### Reject Friend Request
```
POST /api/friend-requests/{id}/reject/
```

#### Cancel Friend Request
```
DELETE /api/friend-requests/{id}/
```

---

## Blocked Users

### List Blocked Users
```
GET /api/blocked-users/
```

### Block User
```
POST /api/blocked-users/
Body: {
    "blocked_user": user_id
}
```

### Unblock User
```
DELETE /api/blocked-users/{id}/
```

---

## Stories

### List Stories
```
GET /api/stories/
Query Parameters:
    - feed: true  # للحصول على feed القصص
Response: [
    {
        "id": 1,
        "user": {...},
        "content_type": "image",
        "content": "url",
        "caption": "...",
        "created_at": "...",
        "expires_at": "...",
        ...
    }
]
```

### Create Story
```
POST /api/stories/
Body: {
    "content_type": "image",  # image, video, text
    "content": <file>,  # للصورة/الفيديو
    "text_content": "...",  # للنص
    "background_color": "#FFFFFF",
    "font_color": "#000000",
    "caption": "..."
}
```

### Story Details
```
GET /api/stories/{id}/
PUT /api/stories/{id}/
DELETE /api/stories/{id}/
```

### View Story
```
POST /api/story-views/
Body: {
    "story": story_id
}
```

### Story Views List
```
GET /api/story-views/?story={story_id}
```

### Story Feed (with badges)
```
GET /api/stories/feed/
Response: {
    "stories": [...],
    "badge_count": 5,
    "channel_badge_count": 2
}
```

---

## Contacts

### List Contacts
```
GET /api/contacts/
```

### Add Contact
```
POST /api/contacts/
Body: {
    "phone": "+1234567890",
    "name": "Contact Name"
}
```

### Update Contact
```
PUT /api/contacts/{id}/
```

### Delete Contact
```
DELETE /api/contacts/{id}/
```

### Delete All Contacts
```
DELETE /api/contacts/delete_all/
```

---

## Recent Contacts

### List Recent Contacts
```
GET /api/recent-contacts/
Response: [
    {
        "id": 1,
        "contact_user": {...},
        "last_message_time": "...",
        "message_count": 10,
        "is_pinned": false,
        ...
    }
]
```

### Pin/Unpin Contact
```
POST /api/recent-contacts/{id}/pin/
POST /api/recent-contacts/{id}/unpin/
```

---

## Calls

### List Calls
```
GET /api/calls/
```

### Create Call Session
```
POST /api/calls/
Body: {
    "room": room_id,
    "call_type": "audio",  # audio or video
    "participants": [user_ids]
}
```

### Call Details
```
GET /api/calls/{id}/
```

### Join Call
```
POST /api/calls/{id}/join/
```

### Leave Call
```
POST /api/calls/{id}/leave/
```

### End Call
```
POST /api/calls/{id}/end/
```

---

## Device Tokens (Push Notifications)

### List Device Tokens
```
GET /api/device-tokens/
```

### Register Device Token
```
POST /api/device-tokens/
Body: {
    "token": "fcm_token_here",
    "device_type": "android",  # android, ios, web
    "device_name": "Device Name"
}
```

### Update Device Token
```
PUT /api/device-tokens/{id}/
```

### Delete Device Token
```
DELETE /api/device-tokens/{id}/
```

---

## Session Devices

### List Session Devices
```
GET /api/session-devices/
```

### Validate Token
```
POST /api/session-devices/validate_token/
Body: {
    "session_token": "...",
    "device_id": "..."
}
Response: {
    "valid": true,
    "user": {...},
    "session": {...}
}
```

### Session Device Details
```
GET /api/session-devices/{id}/
DELETE /api/session-devices/{id}/  # Logout device
```

---

## WebSocket Endpoints

### Notifications WebSocket
```
URL: wss://your-app.onrender.com/ws/notifications/?token=<token>
Protocol: WebSocket
Events:
    - connect: الاتصال
    - message: استقبال إشعارات
    - disconnect: قطع الاتصال
```

### Chat WebSocket
```
URL: wss://your-app.onrender.com/ws/chat/{room_id}/
Protocol: WebSocket
Events:
    - connect: الاتصال
    - chat_message: استقبال/إرسال رسالة
    - typing: مؤشر الكتابة
    - disconnect: قطع الاتصال
```

### Call WebSocket (Signaling)
```
URL: wss://your-app.onrender.com/ws/call/{call_type}/{room_id}/
Protocol: WebSocket
Call Types: audio, video
Events:
    - offer: WebRTC offer
    - answer: WebRTC answer
    - ice_candidate: ICE candidate
    - disconnect: قطع الاتصال
```

---

## Error Responses

جميع الأخطاء تعيد JSON في هذا التنسيق:

```json
{
    "error": "Error message",
    "detail": "Detailed error information"
}
```

### Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

---

## Pagination

جميع الـ endpoints التي تعيد قوائم تدعم Pagination:

```
GET /api/endpoint/?page=1&page_size=50
Response: {
    "count": 100,
    "next": "http://...?page=2",
    "previous": null,
    "results": [...]
}
```

---

## Notes for Flutter Development

1. **Authentication**: استخدم `Authorization: Token <token>` في جميع الطلبات
2. **Base URL**: استخدم `API_BASE_URL` من environment variables
3. **WebSocket**: استخدم `web_socket_channel` package في Flutter
4. **File Upload**: استخدم `multipart/form-data` للصور/الفيديو
5. **Pagination**: جميع القوائم تدعم pagination - استخدم page و page_size
6. **Error Handling**: تحقق دائماً من status code قبل معالجة Response

---

## Testing

يمكنك استخدام هذه الأدوات لاختبار API:
- Postman
- Insomnia
- curl
- Flutter `http` package

---

**Last Updated:** $(date)
**API Version:** 1.0

