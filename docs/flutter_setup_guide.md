# Flutter App Setup Guide - المرحلة الثانية

دليل شامل لإعداد Flutter App للـ Android

---

## المتطلبات الأساسية

### 1. تثبيت Flutter SDK

**للـ Windows:**
```bash
# تحميل Flutter SDK من:
# https://docs.flutter.dev/get-started/install/windows

# إضافة Flutter إلى PATH
# بعد التثبيت، تحقق من:
flutter doctor
```

**التحقق من التثبيت:**
```bash
flutter --version
# يجب أن يكون Flutter 3.x أو أحدث
```

### 2. تثبيت Android Studio

1. تحميل Android Studio من: https://developer.android.com/studio
2. تثبيت Android SDK
3. إعداد Android Emulator (اختياري - يمكن استخدام جهاز حقيقي)

### 3. إعداد Android Device (للاختبار)

1. تفعيل Developer Mode على الهاتف
2. تفعيل USB Debugging
3. توصيل الهاتف بالكمبيوتر

---

## الخطوة 1: إنشاء Flutter Project

### أ) إنشاء المشروع

```bash
# الانتقال لمجلد مناسب
cd /path/to/your/projects

# إنشاء Flutter Project
flutter create arab_chat_app

# الانتقال للمشروع
cd arab_chat_app
```

### ب) هيكل المشروع المطلوب

```
arab_chat_app/
├── lib/
│   ├── main.dart
│   ├── config/
│   │   ├── app_config.dart
│   │   └── theme_config.dart
│   ├── models/
│   │   ├── user.dart
│   │   ├── message.dart
│   │   ├── room.dart
│   │   └── story.dart
│   ├── services/
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   ├── storage_service.dart
│   │   └── websocket_service.dart
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── login_screen.dart
│   │   │   └── register_screen.dart
│   │   ├── chats/
│   │   │   ├── chats_list_screen.dart
│   │   │   └── chat_room_screen.dart
│   │   ├── stories/
│   │   │   └── stories_screen.dart
│   │   ├── groups/
│   │   │   └── groups_screen.dart
│   │   ├── calls/
│   │   │   └── calls_screen.dart
│   │   └── settings/
│   │       └── settings_screen.dart
│   ├── widgets/
│   │   ├── app_bar.dart
│   │   ├── bottom_nav_bar.dart
│   │   └── message_bubble.dart
│   └── utils/
│       ├── constants.dart
│       └── helpers.dart
├── android/
│   └── app/
│       └── build.gradle
├── pubspec.yaml
└── README.md
```

---

## الخطوة 2: إعداد pubspec.yaml

### أ) تحديث Dependencies

```yaml
name: arab_chat_app
description: Arab Chat - WhatsApp-like messaging app for Android
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & API
  http: ^1.1.0
  dio: ^5.4.0
  
  # WebSocket
  web_socket_channel: ^2.4.0
  
  # Storage
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  
  # State Management
  provider: ^6.1.1
  
  # UI Components
  cupertino_icons: ^1.0.6
  cached_network_image: ^3.3.1
  image_picker: ^1.0.5
  video_player: ^2.8.2
  
  # Utilities
  intl: ^0.18.1
  uuid: ^4.2.1
  path_provider: ^2.1.1
  
  # Permissions
  permission_handler: ^11.1.0
  
  # Notifications
  firebase_messaging: ^14.7.9
  firebase_core: ^2.24.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1

flutter:
  uses-material-design: true
  
  # Assets
  assets:
    - assets/images/
    - assets/icons/
  
  # Fonts (اختياري)
  # fonts:
  #   - family: Roboto
  #     fonts:
  #       - asset: fonts/Roboto-Regular.ttf
```

### ب) تثبيت Dependencies

```bash
flutter pub get
```

---

## الخطوة 3: إعداد App Configuration

### ملف: `lib/config/app_config.dart`

```dart
class AppConfig {
  // Base URLs - سيتم تعيينها من Environment Variables لاحقاً
  static const String baseUrl = 'https://your-app.onrender.com';
  static const String apiBaseUrl = '$baseUrl/api';
  static const String wsBaseUrl = 'wss://your-app.onrender.com';
  
  // API Endpoints
  static const String loginEndpoint = '/auth/login/';
  static const String usersEndpoint = '/users/';
  static const String roomsEndpoint = '/rooms/';
  static const String messagesEndpoint = '/messages/';
  static const String storiesEndpoint = '/stories/';
  
  // WebSocket Endpoints
  static const String notificationsWs = '/ws/notifications/';
  static const String chatWs = '/ws/chat/';
  
  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String sessionTokenKey = 'session_token';
  static const String deviceIdKey = 'device_id';
  static const String userIdKey = 'user_id';
  
  // App Info
  static const String appName = 'واتساب الدوبحي';
  static const String appVersion = '1.0.0';
  
  // Build API URL
  static String buildApiUrl(String endpoint) {
    return '$apiBaseUrl$endpoint';
  }
  
  // Build WebSocket URL
  static String buildWsUrl(String endpoint, {String? token}) {
    if (token != null) {
      return '$wsBaseUrl$endpoint?token=${Uri.encodeComponent(token)}';
    }
    return '$wsBaseUrl$endpoint';
  }
}
```

---

## الخطوة 4: إعداد Theme

### ملف: `lib/config/theme_config.dart`

```dart
import 'package:flutter/material.dart';

class AppTheme {
  // WhatsApp Colors
  static const Color primaryGreen = Color(0xFF075E54);
  static const Color primaryGreenDark = Color(0xFF06463F);
  static const Color accentGreen = Color(0xFF25D366);
  static const Color accentGreenDark = Color(0xFF128C7E);
  static const Color lightGreen = Color(0xFFDCF8C6);
  static const Color background = Color(0xFFECE5DD);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color divider = Color(0xFFE9EDEF);
  
  // Text Colors
  static const Color textPrimary = Color(0xFF111111);
  static const Color textSecondary = Color(0xFF54656F);
  
  // Message Bubble Colors
  static const Color bubbleSent = Color(0xFFDCF8C6);
  static const Color bubbleReceived = Color(0xFFFFFFFF);
  
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      primaryColor: primaryGreen,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.light(
        primary: primaryGreen,
        secondary: accentGreen,
        surface: surface,
        background: background,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryGreen,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: accentGreen,
        unselectedItemColor: textSecondary,
        type: BottomNavigationBarType.fixed,
      ),
      fontFamily: 'Roboto',
      textTheme: const TextTheme(
        displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: textPrimary),
        displayMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: textPrimary),
        displaySmall: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: textPrimary),
        headlineMedium: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: textPrimary),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: textPrimary),
        titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: textPrimary),
        bodyLarge: TextStyle(fontSize: 16, color: textPrimary),
        bodyMedium: TextStyle(fontSize: 14, color: textPrimary),
        bodySmall: TextStyle(fontSize: 12, color: textSecondary),
      ),
    );
  }
}
```

---

## الخطوة 5: إعداد Storage Service

### ملف: `lib/services/storage_service.dart`

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

class StorageService {
  static final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
  );
  static SharedPreferences? _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Token Storage (Secure)
  static Future<void> saveToken(String token) async {
    await _secureStorage.write(key: AppConfig.tokenKey, value: token);
  }

  static Future<String?> getToken() async {
    return await _secureStorage.read(key: AppConfig.tokenKey);
  }

  static Future<void> deleteToken() async {
    await _secureStorage.delete(key: AppConfig.tokenKey);
  }

  // Session Storage
  static Future<void> saveSessionToken(String token) async {
    await _secureStorage.write(key: AppConfig.sessionTokenKey, value: token);
  }

  static Future<String?> getSessionToken() async {
    return await _secureStorage.read(key: AppConfig.sessionTokenKey);
  }

  static Future<void> saveDeviceId(String deviceId) async {
    await _prefs?.setString(AppConfig.deviceIdKey, deviceId);
  }

  static Future<String?> getDeviceId() async {
    return _prefs?.getString(AppConfig.deviceIdKey);
  }

  // User ID Storage
  static Future<void> saveUserId(int userId) async {
    await _prefs?.setInt(AppConfig.userIdKey, userId);
  }

  static Future<int?> getUserId() async {
    return _prefs?.getInt(AppConfig.userIdKey);
  }

  // Clear All Data (Logout)
  static Future<void> clearAll() async {
    await _secureStorage.deleteAll();
    await _prefs?.clear();
  }
}
```

---

## الخطوة 6: إعداد API Service

### ملف: `lib/services/api_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import 'storage_service.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  // Get Headers with Token
  Future<Map<String, String>> _getHeaders({bool includeAuth = true}) async {
    Map<String, String> headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (includeAuth) {
      final token = await StorageService.getToken();
      if (token != null) {
        headers['Authorization'] = 'Token $token';
      }
    }

    return headers;
  }

  // GET Request
  Future<Map<String, dynamic>?> get(String endpoint, {bool requireAuth = true}) async {
    try {
      final url = Uri.parse(AppConfig.buildApiUrl(endpoint));
      final headers = await _getHeaders(includeAuth: requireAuth);
      
      final response = await http.get(url, headers: headers);
      
      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        print('GET Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('GET Exception: $e');
      return null;
    }
  }

  // POST Request
  Future<Map<String, dynamic>?> post(
    String endpoint,
    Map<String, dynamic>? data, {
    bool requireAuth = true,
  }) async {
    try {
      final url = Uri.parse(AppConfig.buildApiUrl(endpoint));
      final headers = await _getHeaders(includeAuth: requireAuth);
      
      final response = await http.post(
        url,
        headers: headers,
        body: data != null ? json.encode(data) : null,
      );
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        print('POST Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('POST Exception: $e');
      return null;
    }
  }

  // PUT Request
  Future<Map<String, dynamic>?> put(
    String endpoint,
    Map<String, dynamic>? data, {
    bool requireAuth = true,
  }) async {
    try {
      final url = Uri.parse(AppConfig.buildApiUrl(endpoint));
      final headers = await _getHeaders(includeAuth: requireAuth);
      
      final response = await http.put(
        url,
        headers: headers,
        body: data != null ? json.encode(data) : null,
      );
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        print('PUT Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('PUT Exception: $e');
      return null;
    }
  }

  // DELETE Request
  Future<bool> delete(String endpoint, {bool requireAuth = true}) async {
    try {
      final url = Uri.parse(AppConfig.buildApiUrl(endpoint));
      final headers = await _getHeaders(includeAuth: requireAuth);
      
      final response = await http.delete(url, headers: headers);
      
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (e) {
      print('DELETE Exception: $e');
      return false;
    }
  }

  // Upload File (Multipart)
  Future<Map<String, dynamic>?> uploadFile(
    String endpoint,
    String filePath,
    String fieldName,
    Map<String, dynamic>? additionalData, {
    bool requireAuth = true,
  }) async {
    try {
      final url = Uri.parse(AppConfig.buildApiUrl(endpoint));
      final token = await StorageService.getToken();
      
      var request = http.MultipartRequest('POST', url);
      
      if (token != null && requireAuth) {
        request.headers['Authorization'] = 'Token $token';
      }
      
      request.files.add(await http.MultipartFile.fromPath(fieldName, filePath));
      
      if (additionalData != null) {
        additionalData.forEach((key, value) {
          request.fields[key] = value.toString();
        });
      }
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        print('Upload Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('Upload Exception: $e');
      return null;
    }
  }
}
```

---

## الخطوة 7: إعداد Authentication Service

### ملف: `lib/services/auth_service.dart`

```dart
import '../config/app_config.dart';
import 'api_service.dart';
import 'storage_service.dart';
import '../models/user.dart';

class AuthService {
  static final ApiService _apiService = ApiService();

  // Login
  Future<Map<String, dynamic>?> login(String username, String password) async {
    final response = await _apiService.post(
      AppConfig.loginEndpoint,
      {
        'username': username,
        'password': password,
      },
      requireAuth: false,
    );

    if (response != null && response['token'] != null) {
      final token = response['token'] as String;
      await StorageService.saveToken(token);
      
      // Get user info
      final userInfo = await getCurrentUser();
      if (userInfo != null && userInfo['id'] != null) {
        await StorageService.saveUserId(userInfo['id'] as int);
      }
      
      return response;
    }

    return null;
  }

  // Get Current User
  Future<Map<String, dynamic>?> getCurrentUser() async {
    return await _apiService.get('${AppConfig.usersEndpoint}me/');
  }

  // Get Auth Token (if exists)
  Future<String?> getAuthToken() async {
    var token = await StorageService.getToken();
    
    if (token == null) {
      // Try to get token from API
      final response = await _apiService.get('${AppConfig.usersEndpoint}auth_token/');
      if (response != null && response['token'] != null) {
        token = response['token'] as String;
        await StorageService.saveToken(token);
      }
    }
    
    return token;
  }

  // Check if logged in
  Future<bool> isLoggedIn() async {
    final token = await StorageService.getToken();
    if (token == null) return false;
    
    // Verify token by getting user info
    final userInfo = await getCurrentUser();
    return userInfo != null;
  }

  // Logout
  Future<bool> logout() async {
    final sessionToken = await StorageService.getSessionToken();
    final deviceId = await StorageService.getDeviceId();
    
    if (sessionToken != null && deviceId != null) {
      await _apiService.post(
        '${AppConfig.usersEndpoint}logout/',
        {
          'session_token': sessionToken,
          'device_id': deviceId,
        },
      );
    }
    
    await StorageService.clearAll();
    return true;
  }
}
```

---

## الخطوة 8: تحديث main.dart

### ملف: `lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/theme_config.dart';
import 'services/storage_service.dart';
import 'screens/auth/login_screen.dart';
import 'screens/main/main_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Storage
  await StorageService.init();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'واتساب الدوبحي',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future.delayed(const Duration(seconds: 2));
    
    final authService = AuthService();
    final isLoggedIn = await authService.isLoggedIn();
    
    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => isLoggedIn 
            ? const MainScreen() 
            : const LoginScreen(),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primaryGreen,
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chat,
              size: 80,
              color: Colors.white,
            ),
            SizedBox(height: 20),
            CircularProgressIndicator(
              color: Colors.white,
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## الخطوة 9: Environment Variables في Render

### ⚠️ مهم: Environment Variables في Render

**لا تحتاج إضافة Environment Variables جديدة في Render لأن:**

1. ✅ Flutter App سيستخدم **نفس URLs** الموجودة بالفعل:
   - `BASE_URL` → موجود
   - `API_BASE_URL` → موجود  
   - `WS_BASE_URL` → موجود

2. ✅ Flutter App **لا يحتاج CORS** (لأنه ليس browser)

3. ✅ Backend **جاهز تماماً** لاستقبال طلبات من Mobile Apps

### ما تحتاج فعله:

**في Flutter App فقط:**
- تعديل `lib/config/app_config.dart` ووضع URL الخاص بك:
```dart
static const String baseUrl = 'https://YOUR-APP.onrender.com';
```

**في Render (لا حاجة لتغيير):**
- كل شيء موجود ويعمل ✅

---

## الخطوة 10: تشغيل التطبيق

```bash
# تشغيل على جهاز متصل
flutter run

# أو تشغيل على Emulator
flutter emulators --launch <emulator_id>
flutter run
```

---

## Checklist

- [ ] تثبيت Flutter SDK
- [ ] تثبيت Android Studio
- [ ] إنشاء Flutter Project
- [ ] تحديث pubspec.yaml
- [ ] تثبيت Dependencies
- [ ] إنشاء ملفات Configuration
- [ ] إنشاء ملفات Services
- [ ] تحديث main.dart
- [ ] تحديث App Config بـ URL الخاص بك
- [ ] تشغيل التطبيق واختباره

---

**ملاحظة:** هذا هو Setup الأساسي فقط. في المرحلة التالية سنبدأ ببناء الشاشات الفعلية.

**Last Updated:** 2025-01-13

