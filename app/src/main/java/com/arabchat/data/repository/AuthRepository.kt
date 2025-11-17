package com.arabchat.data.repository

import com.arabchat.data.api.ApiService
import com.arabchat.data.model.AuthResponse
import com.arabchat.data.model.OTPRequest
import com.arabchat.data.model.OTPVerifyRequest
import com.arabchat.data.model.User

class AuthRepository(private val apiService: ApiService) {
    
    suspend fun requestOTP(phone: String): Result<String> {
        return try {
            val response = apiService.requestOTP(OTPRequest(phone))
            if (response.isSuccessful) {
                Result.success(response.body()?.get("message") ?: "تم إرسال الرمز")
            } else {
                Result.failure(Exception("فشل إرسال الرمز"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun verifyOTP(phone: String, otpCode: String): Result<AuthResponse> {
        return try {
            val response = apiService.verifyOTP(OTPVerifyRequest(phone, otpCode))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("رمز التحقق غير صحيح"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
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
}

