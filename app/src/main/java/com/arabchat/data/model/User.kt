package com.arabchat.data.model

import com.google.gson.annotations.SerializedName

data class User(
    @SerializedName("id")
    val id: Int,
    @SerializedName("username")
    val username: String,
    @SerializedName("email")
    val email: String?,
    @SerializedName("first_name")
    val firstName: String?,
    @SerializedName("last_name")
    val lastName: String?,
    @SerializedName("profile")
    val profile: UserProfile?
)

data class UserProfile(
    @SerializedName("id")
    val id: Int,
    @SerializedName("phone")
    val phone: String,
    @SerializedName("avatar")
    val avatar: String?,
    @SerializedName("cover_image")
    val coverImage: String?,
    @SerializedName("bio")
    val bio: String?,
    @SerializedName("is_online")
    val isOnline: Boolean,
    @SerializedName("last_seen")
    val lastSeen: String?,
    @SerializedName("is_verified")
    val isVerified: Boolean
)

