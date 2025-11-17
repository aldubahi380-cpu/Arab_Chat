package com.arabchat.util

import android.content.Context
import android.content.SharedPreferences

class TokenManager(context: Context) {
    
    private val prefs: SharedPreferences = context.getSharedPreferences(
        "arab_chat_prefs",
        Context.MODE_PRIVATE
    )
    
    fun saveToken(token: String) {
        prefs.edit().putString("auth_token", token).apply()
    }
    
    fun getToken(): String? {
        return prefs.getString("auth_token", null)
    }
    
    fun clearToken() {
        prefs.edit().remove("auth_token").apply()
    }
    
    fun isLoggedIn(): Boolean {
        return getToken() != null
    }
    
    fun saveUserId(userId: Int) {
        prefs.edit().putInt("user_id", userId).apply()
    }
    
    fun getUserId(): Int? {
        return if (prefs.contains("user_id")) prefs.getInt("user_id", -1) else null
    }
    
    fun clearAll() {
        prefs.edit().clear().apply()
    }
}

