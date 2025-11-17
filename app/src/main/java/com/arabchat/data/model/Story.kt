package com.arabchat.data.model

import com.google.gson.annotations.SerializedName

data class Story(
    @SerializedName("id")
    val id: Int,
    @SerializedName("user")
    val user: User,
    @SerializedName("content")
    val content: String?,
    @SerializedName("file")
    val file: String?,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("expires_at")
    val expiresAt: String
)

