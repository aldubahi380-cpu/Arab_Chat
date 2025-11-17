package com.arabchat.ui.splash

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.appcompat.app.AppCompatActivity
import com.arabchat.R
import com.arabchat.ui.auth.PhoneVerificationActivity
import com.arabchat.ui.main.MainActivity
import com.arabchat.util.TokenManager

class SplashActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_splash)
        
        val tokenManager = TokenManager(this)
        
        Handler(Looper.getMainLooper()).postDelayed({
            if (tokenManager.isLoggedIn()) {
                startActivity(Intent(this, MainActivity::class.java))
            } else {
                startActivity(Intent(this, PhoneVerificationActivity::class.java))
            }
            finish()
        }, 2000)
    }
}

