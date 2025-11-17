package com.arabchat.ui.auth

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import com.arabchat.R
import com.arabchat.databinding.ActivityPhoneVerificationBinding
import com.arabchat.ui.auth.viewmodel.AuthViewModel
import com.arabchat.ui.auth.viewmodel.AuthViewModelFactory

class PhoneVerificationActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityPhoneVerificationBinding
    private lateinit var viewModel: AuthViewModel
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPhoneVerificationBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        val factory = AuthViewModelFactory(this)
        viewModel = ViewModelProvider(this, factory)[AuthViewModel::class.java]
        
        setupObservers()
        
        binding.btnSendOtp.setOnClickListener {
            val phone = binding.etPhone.text.toString().trim()
            val username = binding.etUsername.text.toString().trim()
            if (phone.isNotEmpty() && username.isNotEmpty()) {
                viewModel.requestOTP(phone, username)
            } else {
                Toast.makeText(this, "يرجى إدخال رقم الهاتف واسم المستخدم", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun setupObservers() {
        viewModel.otpSent.observe(this) { success ->
            if (success) {
                val phone = binding.etPhone.text.toString().trim()
                val username = binding.etUsername.text.toString().trim()
                val intent = Intent(this, OTPVerificationActivity::class.java)
                intent.putExtra("phone", phone)
                intent.putExtra("username", username)
                startActivity(intent)
            }
        }
        
        viewModel.error.observe(this) { error ->
            error?.let {
                Toast.makeText(this, it, Toast.LENGTH_SHORT).show()
            }
        }
        
        viewModel.loading.observe(this) { isLoading ->
            binding.btnSendOtp.isEnabled = !isLoading
            binding.progressBar.visibility = if (isLoading) android.view.View.VISIBLE else android.view.View.GONE
        }
    }
}

