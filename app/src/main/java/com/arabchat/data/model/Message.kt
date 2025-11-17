package com.arabchat.data.model

import com.google.gson.annotations.SerializedName

data class Message(
    @SerializedName("id")
    val id: Int,
    @SerializedName("room")
    val roomId: Int,
    @SerializedName("sender")
    val sender: User?,
    @SerializedName("sender_id")
    val senderId: Int,
    @SerializedName("content")
    val content: String?,
    @SerializedName("message_type")
    val messageType: String,
    @SerializedName("file")
    val file: String?,
    @SerializedName("original_file")
    val originalFile: String?,
    @SerializedName("thumbnail")
    val thumbnail: String?,
    @SerializedName("is_read")
    val isRead: Boolean,
    @SerializedName("is_deleted")
    val isDeleted: Boolean,
    @SerializedName("is_edited")
    val isEdited: Boolean,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("updated_at")
    val updatedAt: String
) {
    companion object {
        const val TYPE_TEXT = "text"
        const val TYPE_IMAGE = "image"
        const val TYPE_VIDEO = "video"
        const val TYPE_AUDIO = "audio"
        const val TYPE_FILE = "file"
    }
}

