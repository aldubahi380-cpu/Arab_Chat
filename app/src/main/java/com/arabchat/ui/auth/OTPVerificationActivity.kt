package com.arabchat.ui.auth

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import com.arabchat.R
import com.arabchat.databinding.ActivityOtpVerificationBinding
import com.arabchat.ui.auth.viewmodel.AuthViewModel
import com.arabchat.ui.auth.viewmodel.AuthViewModelFactory
import com.arabchat.ui.main.MainActivity

class OTPVerificationActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityOtpVerificationBinding
    private lateinit var viewModel: AuthViewModel
    private var phone: String = ""
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityOtpVerificationBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        phone = intent.getStringExtra("phone") ?: ""
        
        val factory = AuthViewModelFactory(this)
        viewModel = ViewModelProvider(this, factory)[AuthViewModel::class.java]
        
        setupObservers()
        
        binding.btnVerify.setOnClickListener {
            val otp = binding.etOtp.text.toString().trim()
            val username = intent.getStringExtra("username") ?: ""
            if (otp.length == 6 && username.isNotEmpty()) {
                // Get device info
                val deviceId = android.provider.Settings.Secure.getString(
                    contentResolver,
                    android.provider.Settings.Secure.ANDROID_ID
                )
                val deviceName = android.os.Build.MODEL
                viewModel.verifyOTP(phone, otp, username, deviceId, deviceName)
            } else {
                Toast.makeText(this, R.string.invalid_otp, Toast.LENGTH_SHORT).show()
            }
        }
        
        binding.btnResend.setOnClickListener {
            val username = intent.getStringExtra("username") ?: ""
            if (username.isNotEmpty()) {
                viewModel.requestOTP(phone, username)
            }
        }
    }
    
    private fun setupObservers() {
        viewModel.authSuccess.observe(this) { success ->
            if (success) {
                startActivity(Intent(this, MainActivity::class.java))
                finishAffinity()
            }
        }
        
        viewModel.error.observe(this) { error ->
            error?.let {
                Toast.makeText(this, it, Toast.LENGTH_SHORT).show()
            }
        }
        
        viewModel.loading.observe(this) { isLoading ->
            binding.btnVerify.isEnabled = !isLoading
            binding.progressBar.visibility = if (isLoading) android.view.View.VISIBLE else android.view.View.GONE
        }
    }
}

