package com.arabchat.data.model

import com.google.gson.annotations.SerializedName

data class ChatRoom(
    @SerializedName("id")
    val id: Int,
    @SerializedName("name")
    val name: String?,
    @SerializedName("room_type")
    val roomType: String,
    @SerializedName("participants")
    val participants: List<User>?,
    @SerializedName("last_message")
    val lastMessage: Message?,
    @SerializedName("unread_count")
    val unreadCount: Int = 0,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("updated_at")
    val updatedAt: String
)

