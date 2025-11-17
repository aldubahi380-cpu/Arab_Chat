package com.arabchat.data.repository

import com.arabchat.data.api.ApiService
import com.arabchat.data.model.ChatRoom
import com.arabchat.data.model.Message

class ChatRepository(private val apiService: ApiService) {
    
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
    
    suspend fun getMessages(roomId: Int, page: Int = 1): Result<List<Message>> {
        return try {
            val response = apiService.getMessages(roomId, page)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val messages = body["results"] as? List<Map<String, Any>>?
                if (messages != null) {
                    // Parse messages from JSON
                    Result.success(emptyList()) // TODO: Parse properly
                } else {
                    Result.success(emptyList())
                }
            } else {
                Result.failure(Exception("فشل تحميل الرسائل"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
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
                Result.failure(Exception("فشل إرسال الرسالة"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
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
}

