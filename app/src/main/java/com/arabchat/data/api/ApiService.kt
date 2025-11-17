package com.arabchat.data.api

import com.arabchat.BuildConfig
import com.arabchat.data.model.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*
import java.io.File

/**
 * API Service Interface - جميع الـ endpoints المتاحة على السيرفر
 * متوافق مع Django REST Framework على Render
 */
interface ApiService {
    
    // ==================== Authentication ====================
    
    /**
     * POST /api/otp/request/
     * إرسال رمز OTP
     * Body: { "phone": "...", "username": "..." }
     */
    @POST("otp/request/")
    suspend fun requestOTP(@Body request: Map<String, String>): Response<Map<String, Any>>
    
    /**
     * POST /api/otp/verify/
     * التحقق من رمز OTP وإنشاء حساب/تسجيل دخول
     * Body: { "phone": "...", "otp_code": "...", "username": "...", "device_id": "...", "device_name": "...", "platform": "android" }
     */
    @POST("otp/verify/")
    suspend fun verifyOTP(@Body request: Map<String, Any>): Response<Map<String, Any>>
    
    /**
     * POST /api/auth/login/
     * تسجيل الدخول بالاسم وكلمة المرور (Token Authentication)
     */
    @POST("auth/login/")
    suspend fun login(@Body request: Map<String, String>): Response<Map<String, String>>
    
    // ==================== Users ====================
    
    /**
     * GET /api/users/me/
     * الحصول على معلومات المستخدم الحالي
     */
    @GET("users/me/")
    suspend fun getCurrentUser(): Response<User>
    
    /**
     * GET /api/users/{id}/
     * الحصول على معلومات مستخدم معين
     */
    @GET("users/{id}/")
    suspend fun getUser(@Path("id") id: Int): Response<User>
    
    /**
     * GET /api/users/?search=query
     * البحث عن المستخدمين
     */
    @GET("users/")
    suspend fun searchUsers(@Query("search") query: String): Response<List<User>>
    
    /**
     * POST /api/users/logout/
     * تسجيل الخروج
     */
    @POST("users/logout/")
    suspend fun logout(@Body request: Map<String, String>? = null): Response<Map<String, Any>>
    
    /**
     * DELETE /api/users/delete_account/
     * حذف الحساب
     */
    @HTTP(method = "DELETE", path = "users/delete_account/", hasBody = false)
    suspend fun deleteAccount(): Response<Map<String, Any>>
    
    // ==================== Profiles ====================
    
    /**
     * GET /api/profiles/{id}/
     * الحصول على ملف مستخدم
     */
    @GET("profiles/{id}/")
    suspend fun getProfile(@Path("id") id: Int): Response<UserProfile>
    
    /**
     * PUT /api/profiles/{id}/
     * تحديث الملف الشخصي (نص فقط)
     */
    @PUT("profiles/{id}/")
    suspend fun updateProfile(
        @Path("id") id: Int,
        @Body profile: Map<String, Any>
    ): Response<UserProfile>
    
    /**
     * PUT /api/profiles/{id}/
     * تحديث الملف الشخصي مع صورة
     */
    @Multipart
    @PUT("profiles/{id}/")
    suspend fun updateProfileWithImage(
        @Path("id") id: Int,
        @Part avatar: MultipartBody.Part?,
        @Part("bio") bio: RequestBody?,
        @Part("first_name") firstName: RequestBody?,
        @Part("last_name") lastName: RequestBody?
    ): Response<UserProfile>
    
    // ==================== Chat Rooms ====================
    
    /**
     * GET /api/rooms/
     * الحصول على جميع غرف الدردشة للمستخدم
     */
    @GET("rooms/")
    suspend fun getChatRooms(): Response<List<ChatRoom>>
    
    /**
     * GET /api/rooms/my_rooms/
     * الحصول على غرف المستخدم
     */
    @GET("rooms/my_rooms/")
    suspend fun getMyRooms(): Response<List<ChatRoom>>
    
    /**
     * GET /api/rooms/{id}/
     * الحصول على غرفة دردشة معينة
     */
    @GET("rooms/{id}/")
    suspend fun getChatRoom(@Path("id") id: Int): Response<ChatRoom>
    
    /**
     * POST /api/rooms/
     * إنشاء غرفة دردشة جديدة
     */
    @POST("rooms/")
    suspend fun createChatRoom(@Body room: Map<String, Any>): Response<ChatRoom>
    
    /**
     * GET /api/rooms/chat_list_updates/
     * الحصول على تحديثات قائمة الدردشات
     */
    @GET("rooms/chat_list_updates/")
    suspend fun getChatListUpdates(): Response<Map<String, Any>>
    
    // ==================== Messages ====================
    
    /**
     * GET /api/messages/?room={roomId}&page={page}
     * الحصول على الرسائل في غرفة معينة
     */
    @GET("messages/")
    suspend fun getMessages(
        @Query("room") roomId: Int,
        @Query("page") page: Int = 1
    ): Response<Map<String, Any>>
    
    /**
     * POST /api/messages/
     * إرسال رسالة نصية
     * Body: { "room": roomId, "content": "...", "message_type": "text" }
     */
    @POST("messages/")
    suspend fun sendMessage(@Body message: Map<String, Any>): Response<Message>
    
    /**
     * POST /api/messages/
     * إرسال رسالة مع ملف (صورة/فيديو/صوت/ملف)
     * Multipart: room, message_type, file, content (optional)
     */
    @Multipart
    @POST("messages/")
    suspend fun sendMediaMessage(
        @Part("room") roomId: RequestBody,
        @Part("message_type") messageType: RequestBody,
        @Part file: MultipartBody.Part,
        @Part("content") content: RequestBody?
    ): Response<Message>
    
    /**
     * PUT /api/messages/{id}/
     * تعديل رسالة نصية
     */
    @PUT("messages/{id}/")
    suspend fun updateMessage(
        @Path("id") id: Int,
        @Body message: Map<String, Any>
    ): Response<Message>
    
    /**
     * DELETE /api/messages/{id}/
     * حذف رسالة
     */
    @DELETE("messages/{id}/")
    suspend fun deleteMessage(@Path("id") id: Int): Response<Map<String, Any>>
    
    /**
     * GET /api/messages/poll_new/?room_id={roomId}&last_message_id={id}
     * Polling للحصول على الرسائل الجديدة
     */
    @GET("messages/poll_new/")
    suspend fun pollNewMessages(
        @Query("room_id") roomId: Int,
        @Query("last_message_id") lastMessageId: Int = 0
    ): Response<Map<String, Any>>
    
    /**
     * GET /api/messages/unread_count/?room={roomId}
     * الحصول على عدد الرسائل غير المقروءة
     */
    @GET("messages/unread_count/")
    suspend fun getUnreadCount(@Query("room") roomId: Int): Response<Map<String, Any>>
    
    /**
     * POST /api/messages/{id}/mark_read/
     * تحديد رسالة كمقروءة
     */
    @POST("messages/{id}/mark_read/")
    suspend fun markMessageAsRead(@Path("id") id: Int): Response<Map<String, Any>>
    
    // ==================== Message Reads ====================
    
    /**
     * POST /api/message-reads/
     * تحديد رسالة كمقروءة
     * Body: { "message": messageId, "room": roomId }
     */
    @POST("message-reads/")
    suspend fun markAsRead(@Body read: Map<String, Int>): Response<Map<String, Any>>
    
    // ==================== Friends ====================
    
    /**
     * GET /api/friends/
     * الحصول على قائمة الأصدقاء
     */
    @GET("friends/")
    suspend fun getFriends(): Response<List<User>>
    
    /**
     * POST /api/friend-requests/
     * إرسال طلب صداقة
     */
    @POST("friend-requests/")
    suspend fun sendFriendRequest(@Body request: Map<String, Int>): Response<Map<String, Any>>
    
    /**
     * PUT /api/friend-requests/{id}/accept/
     * قبول طلب صداقة
     */
    @PUT("friend-requests/{id}/accept/")
    suspend fun acceptFriendRequest(@Path("id") id: Int): Response<Map<String, Any>>
    
    /**
     * DELETE /api/friend-requests/{id}/
     * رفض طلب صداقة
     */
    @DELETE("friend-requests/{id}/")
    suspend fun rejectFriendRequest(@Path("id") id: Int): Response<Map<String, Any>>
    
    // ==================== Contacts ====================
    
    /**
     * GET /api/contacts/
     * الحصول على قائمة جهات الاتصال
     */
    @GET("contacts/")
    suspend fun getContacts(): Response<List<User>>
    
    // ==================== Recent Contacts ====================
    
    /**
     * GET /api/recent-contacts/
     * الحصول على جهات الاتصال الأخيرة
     */
    @GET("recent-contacts/")
    suspend fun getRecentContacts(): Response<List<User>>
    
    // ==================== Stories ====================
    
    /**
     * GET /api/stories/
     * الحصول على الاستوريات
     */
    @GET("stories/")
    suspend fun getStories(): Response<List<Story>>
    
    /**
     * POST /api/stories/
     * إنشاء استوري نصي
     */
    @POST("stories/")
    suspend fun createStory(@Body story: Map<String, Any>): Response<Story>
    
    /**
     * POST /api/stories/
     * إنشاء استوري مع ملف (صورة/فيديو)
     */
    @Multipart
    @POST("stories/")
    suspend fun createStoryWithMedia(
        @Part("content") content: RequestBody?,
        @Part file: MultipartBody.Part
    ): Response<Story>
    
    // ==================== Device Tokens (Push Notifications) ====================
    
    /**
     * POST /api/device-tokens/
     * تسجيل رمز الجهاز للإشعارات
     * Body: { "token": "...", "device_type": "android", "device_id": "...", "device_name": "..." }
     */
    @POST("device-tokens/")
    suspend fun registerDeviceToken(@Body token: Map<String, String>): Response<Map<String, Any>>
    
    /**
     * POST /api/device-tokens/register/
     * تسجيل رمز الجهاز (endpoint بديل)
     */
    @POST("device-tokens/register/")
    suspend fun registerDeviceTokenAlt(@Body token: Map<String, String>): Response<Map<String, Any>>
    
    /**
     * POST /api/device-tokens/unregister/
     * إلغاء تسجيل رمز الجهاز
     */
    @POST("device-tokens/unregister/")
    suspend fun unregisterDeviceToken(@Body token: Map<String, String>): Response<Map<String, Any>>
    
    /**
     * GET /api/device-tokens/my_tokens/
     * الحصول على جميع رموز الأجهزة للمستخدم
     */
    @GET("device-tokens/my_tokens/")
    suspend fun getMyDeviceTokens(): Response<List<Map<String, Any>>>
}
