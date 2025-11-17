package com.arabchat.data.repository

import com.arabchat.data.api.ApiService
import com.arabchat.data.model.AuthResponse
import com.arabchat.data.model.User

class AuthRepository(private val apiService: ApiService) {
    
    /**
     * إرسال رمز OTP
     * POST /api/otp/request/
     */
    suspend fun requestOTP(phone: String, username: String): Result<Map<String, Any>> {
        return try {
            val request = mapOf(
                "phone" to phone,
                "username" to username
            )
            val response = apiService.requestOTP(request)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                if (body["success"] == true || body["message"] != null) {
                    Result.success(body)
                } else {
                    val error = body["error"] as? String ?: "فشل إرسال الرمز"
                    Result.failure(Exception(error))
                }
            } else {
                val errorBody = response.errorBody()?.string() ?: "فشل إرسال الرمز"
                Result.failure(Exception(errorBody))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * التحقق من رمز OTP وإنشاء حساب/تسجيل دخول
     * POST /api/otp/verify/
     */
    suspend fun verifyOTP(
        phone: String,
        otpCode: String,
        username: String,
        deviceId: String? = null,
        deviceName: String? = null,
        platform: String = "android"
    ): Result<AuthResponse> {
        return try {
            val request = mutableMapOf<String, Any>(
                "phone" to phone,
                "otp_code" to otpCode,
                "username" to username,
                "platform" to platform
            )
            deviceId?.let { request["device_id"] = it }
            deviceName?.let { request["device_name"] = it }
            
            val response = apiService.verifyOTP(request)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                if (body["success"] == true && body["token"] != null) {
                    // Parse response to AuthResponse
                    val token = body["token"] as String
                    val userMap = body["user"] as? Map<*, *>
                    val user = if (userMap != null) {
                        // Parse user from map
                        User(
                            id = (userMap["id"] as? Number)?.toInt() ?: 0,
                            username = userMap["username"] as? String ?: "",
                            email = userMap["email"] as? String,
                            firstName = userMap["first_name"] as? String,
                            lastName = userMap["last_name"] as? String,
                            profile = null // Will be loaded separately if needed
                        )
                    } else null
                    
                    val sessionMap = body["session"] as? Map<*, *>
                    val session = if (sessionMap != null) {
                        com.arabchat.data.model.SessionInfo(
                            sessionToken = sessionMap["session_token"] as? String ?: "",
                            deviceId = sessionMap["device_id"] as? String ?: "",
                            deviceName = sessionMap["device_name"] as? String,
                            platform = sessionMap["platform"] as? String,
                            expiresAt = sessionMap["expires_at"] as? String
                        )
                    } else null
                    
                    Result.success(
                        AuthResponse(
                            token = token,
                            user = user,
                            message = body["message"] as? String,
                            success = true,
                            created = body["created"] as? Boolean,
                            session = session
                        )
                    )
                } else {
                    val error = body["error"] as? String ?: "رمز التحقق غير صحيح"
                    Result.failure(Exception(error))
                }
            } else {
                val errorBody = response.errorBody()?.string() ?: "رمز التحقق غير صحيح"
                Result.failure(Exception(errorBody))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * الحصول على معلومات المستخدم الحالي
     * GET /api/users/me/
     */
    suspend fun getCurrentUser(): Result<User> {
        return try {
            val response = apiService.getCurrentUser()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("فشل تحميل بيانات المستخدم"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * تسجيل الخروج
     * POST /api/users/logout/
     */
    suspend fun logout(sessionToken: String?, deviceId: String?): Result<Boolean> {
        return try {
            val request = mutableMapOf<String, String>()
            sessionToken?.let { request["session_token"] = it }
            deviceId?.let { request["device_id"] = it }
            
            val response = apiService.logout(if (request.isNotEmpty()) request else null)
            if (response.isSuccessful) {
                Result.success(true)
            } else {
                Result.failure(Exception("فشل تسجيل الخروج"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

