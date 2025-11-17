package com.arabchat.data.api

import com.arabchat.BuildConfig
import com.arabchat.data.model.*
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface ApiService {
    
    // Authentication
    @POST("otp/request/")
    suspend fun requestOTP(@Body request: OTPRequest): Response<Map<String, String>>
    
    @POST("otp/verify/")
    suspend fun verifyOTP(@Body request: OTPVerifyRequest): Response<AuthResponse>
    
    @POST("auth/login/")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>
    
    // Users
    @GET("users/me/")
    suspend fun getCurrentUser(): Response<User>
    
    @GET("users/{id}/")
    suspend fun getUser(@Path("id") id: Int): Response<User>
    
    @GET("users/")
    suspend fun searchUsers(@Query("search") query: String): Response<List<User>>
    
    // Profiles
    @GET("profiles/{id}/")
    suspend fun getProfile(@Path("id") id: Int): Response<UserProfile>
    
    @PUT("profiles/{id}/")
    suspend fun updateProfile(
        @Path("id") id: Int,
        @Body profile: Map<String, Any>
    ): Response<UserProfile>
    
    @Multipart
    @PUT("profiles/{id}/")
    suspend fun updateProfileWithImage(
        @Path("id") id: Int,
        @Part avatar: MultipartBody.Part?,
        @Part("bio") bio: String?,
        @Part("first_name") firstName: String?,
        @Part("last_name") lastName: String?
    ): Response<UserProfile>
    
    // Chat Rooms
    @GET("rooms/")
    suspend fun getChatRooms(): Response<List<ChatRoom>>
    
    @GET("rooms/{id}/")
    suspend fun getChatRoom(@Path("id") id: Int): Response<ChatRoom>
    
    @POST("rooms/")
    suspend fun createChatRoom(@Body room: Map<String, Any>): Response<ChatRoom>
    
    // Messages
    @GET("messages/")
    suspend fun getMessages(
        @Query("room") roomId: Int,
        @Query("page") page: Int = 1
    ): Response<Map<String, Any>>
    
    @POST("messages/")
    suspend fun sendMessage(@Body message: Map<String, Any>): Response<Message>
    
    @Multipart
    @POST("messages/")
    suspend fun sendMediaMessage(
        @Part("room") roomId: Int,
        @Part("message_type") messageType: String,
        @Part file: MultipartBody.Part,
        @Part("content") content: String?
    ): Response<Message>
    
    @PUT("messages/{id}/")
    suspend fun updateMessage(
        @Path("id") id: Int,
        @Body message: Map<String, Any>
    ): Response<Message>
    
    @DELETE("messages/{id}/")
    suspend fun deleteMessage(@Path("id") id: Int): Response<Unit>
    
    // Message Reads
    @POST("message-reads/")
    suspend fun markAsRead(@Body read: Map<String, Any>): Response<Unit>
    
    // Friends
    @GET("friends/")
    suspend fun getFriends(): Response<List<User>>
    
    @POST("friend-requests/")
    suspend fun sendFriendRequest(@Body request: Map<String, Any>): Response<Unit>
    
    @PUT("friend-requests/{id}/accept/")
    suspend fun acceptFriendRequest(@Path("id") id: Int): Response<Unit>
    
    @DELETE("friend-requests/{id}/")
    suspend fun rejectFriendRequest(@Path("id") id: Int): Response<Unit>
    
    // Contacts
    @GET("contacts/")
    suspend fun getContacts(): Response<List<User>>
    
    // Stories
    @GET("stories/")
    suspend fun getStories(): Response<List<Story>>
    
    @POST("stories/")
    suspend fun createStory(@Body story: Map<String, Any>): Response<Story>
    
    @Multipart
    @POST("stories/")
    suspend fun createStoryWithMedia(
        @Part("content") content: String?,
        @Part file: MultipartBody.Part
    ): Response<Story>
    
    // Device Token (for push notifications)
    @POST("device-tokens/")
    suspend fun registerDeviceToken(@Body token: Map<String, String>): Response<Unit>
    
    companion object {
        fun create(baseUrl: String = BuildConfig.API_BASE_URL): ApiService {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BODY
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            }
            
            val client = OkHttpClient.Builder()
                .addInterceptor(loggingInterceptor)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build()
            
            val retrofit = Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
            
            return retrofit.create(ApiService::class.java)
        }
    }
}


