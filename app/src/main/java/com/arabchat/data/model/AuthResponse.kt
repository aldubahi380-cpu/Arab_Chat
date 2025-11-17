package com.arabchat.data.model

import com.google.gson.annotations.SerializedName

/**
 * استجابة التحقق من OTP
 * Response من /api/otp/verify/
 */
data class AuthResponse(
    @SerializedName("token")
    val token: String,
    @SerializedName("user")
    val user: User?,
    @SerializedName("message")
    val message: String?,
    @SerializedName("success")
    val success: Boolean?,
    @SerializedName("created")
    val created: Boolean?,
    @SerializedName("session")
    val session: SessionInfo?
)

data class SessionInfo(
    @SerializedName("session_token")
    val sessionToken: String,
    @SerializedName("device_id")
    val deviceId: String,
    @SerializedName("device_name")
    val deviceName: String?,
    @SerializedName("platform")
    val platform: String?,
    @SerializedName("expires_at")
    val expiresAt: String?
)

