package com.arabchat.data.model

import com.google.gson.annotations.SerializedName

data class AuthResponse(
    @SerializedName("token")
    val token: String,
    @SerializedName("user")
    val user: User
)

data class OTPRequest(
    @SerializedName("phone")
    val phone: String
)

data class OTPVerifyRequest(
    @SerializedName("phone")
    val phone: String,
    @SerializedName("otp_code")
    val otpCode: String
)

data class LoginRequest(
    @SerializedName("username")
    val username: String,
    @SerializedName("password")
    val password: String
)

