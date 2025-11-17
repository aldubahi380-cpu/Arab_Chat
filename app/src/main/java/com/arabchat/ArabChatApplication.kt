package com.arabchat

import android.app.Application
import com.arabchat.data.api.ApiClient
import com.arabchat.util.TokenManager

class ArabChatApplication : Application() {
    
    companion object {
        lateinit var instance: ArabChatApplication
            private set
    }
    
    override fun onCreate() {
        super.onCreate()
        instance = this
        
        // Initialize API Client
        val tokenManager = TokenManager(this)
        ApiClient.initialize(tokenManager)
    }
}

