package com.arabchat.data.repository

import com.arabchat.data.api.ApiService
import com.arabchat.data.model.ChatRoom
import com.arabchat.data.model.Message
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class ChatRepository(private val apiService: ApiService) {
    
    /**
     * الحصول على جميع غرف الدردشة
     * GET /api/rooms/
     */
    suspend fun getChatRooms(): Result<List<ChatRoom>> {
        return try {
            val response = apiService.getChatRooms()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("فشل تحميل الدردشات"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * الحصول على تحديثات قائمة الدردشات
     * GET /api/rooms/chat_list_updates/
     */
    suspend fun getChatListUpdates(): Result<Map<String, Any>> {
        return try {
            val response = apiService.getChatListUpdates()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("فشل تحميل تحديثات الدردشات"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * الحصول على غرفة دردشة معينة
     * GET /api/rooms/{id}/
     */
    suspend fun getChatRoom(roomId: Int): Result<ChatRoom> {
        return try {
            val response = apiService.getChatRoom(roomId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("فشل تحميل الدردشة"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * الحصول على الرسائل في غرفة
     * GET /api/messages/?room={roomId}&page={page}
     */
    suspend fun getMessages(roomId: Int, page: Int = 1): Result<List<Message>> {
        return try {
            val response = apiService.getMessages(roomId, page)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                // Django REST Framework returns paginated results
                val results = body["results"] as? List<Map<String, Any>>?
                if (results != null) {
                    // Parse messages - TODO: Use Gson to parse properly
                    Result.success(emptyList()) // Placeholder
                } else {
                    // If not paginated, try direct list
                    val messages = body as? List<Map<String, Any>>?
                    Result.success(emptyList()) // Placeholder
                }
            } else {
                Result.failure(Exception("فشل تحميل الرسائل"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * إرسال رسالة نصية
     * POST /api/messages/
     */
    suspend fun sendMessage(roomId: Int, content: String): Result<Message> {
        return try {
            val response = apiService.sendMessage(mapOf(
                "room" to roomId,
                "content" to content,
                "message_type" to "text"
            ))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                val errorBody = response.errorBody()?.string() ?: "فشل إرسال الرسالة"
                Result.failure(Exception(errorBody))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * إرسال رسالة مع ملف (صورة/فيديو/صوت)
     * POST /api/messages/ (Multipart)
     */
    suspend fun sendMediaMessage(
        roomId: Int,
        file: File,
        messageType: String,
        content: String? = null
    ): Result<Message> {
        return try {
            val roomIdBody = roomId.toString().toRequestBody("text/plain".toMediaTypeOrNull())
            val messageTypeBody = messageType.toRequestBody("text/plain".toMediaTypeOrNull())
            val contentBody = content?.toRequestBody("text/plain".toMediaTypeOrNull())
            
            val filePart = MultipartBody.Part.createFormData(
                "file",
                file.name,
                file.asRequestBody(getMediaType(messageType).toMediaTypeOrNull())
            )
            
            val response = apiService.sendMediaMessage(
                roomIdBody,
                messageTypeBody,
                filePart,
                contentBody
            )
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                val errorBody = response.errorBody()?.string() ?: "فشل إرسال الملف"
                Result.failure(Exception(errorBody))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * تحديد رسالة كمقروءة
     * POST /api/message-reads/
     */
    suspend fun markAsRead(roomId: Int, messageId: Int): Result<Unit> {
        return try {
            val response = apiService.markAsRead(mapOf(
                "room" to roomId,
                "message" to messageId
            ))
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("فشل تحديث حالة القراءة"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * Polling للحصول على الرسائل الجديدة
     * GET /api/messages/poll_new/
     */
    suspend fun pollNewMessages(roomId: Int, lastMessageId: Int = 0): Result<List<Message>> {
        return try {
            val response = apiService.pollNewMessages(roomId, lastMessageId)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val messages = body["messages"] as? List<Map<String, Any>>?
                Result.success(emptyList()) // TODO: Parse messages
            } else {
                Result.failure(Exception("فشل تحميل الرسائل الجديدة"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * الحصول على عدد الرسائل غير المقروءة
     * GET /api/messages/unread_count/
     */
    suspend fun getUnreadCount(roomId: Int): Result<Int> {
        return try {
            val response = apiService.getUnreadCount(roomId)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val count = (body["unread_count"] as? Number)?.toInt() ?: 0
                Result.success(count)
            } else {
                Result.failure(Exception("فشل تحميل عدد الرسائل غير المقروءة"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    private fun getMediaType(messageType: String): String {
        return when (messageType) {
            "image" -> "image/*"
            "video" -> "video/*"
            "audio" -> "audio/*"
            "file" -> "application/octet-stream"
            else -> "application/octet-stream"
        }
    }
}

