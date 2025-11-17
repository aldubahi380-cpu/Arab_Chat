package com.arabchat.ui.auth.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arabchat.data.api.ApiClient
import com.arabchat.data.repository.AuthRepository
import com.arabchat.util.TokenManager
import kotlinx.coroutines.launch

class AuthViewModel(private val context: android.content.Context) : ViewModel() {
    
    private val tokenManager = TokenManager(context)
    private val authRepository = AuthRepository(ApiClient.getApiService())
    
    private val _otpSent = MutableLiveData<Boolean>()
    val otpSent: LiveData<Boolean> = _otpSent
    
    private val _authSuccess = MutableLiveData<Boolean>()
    val authSuccess: LiveData<Boolean> = _authSuccess
    
    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading
    
    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error
    
    fun requestOTP(phone: String, username: String) {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            
            authRepository.requestOTP(phone, username).fold(
                onSuccess = { response ->
                    _otpSent.value = true
                    _loading.value = false
                },
                onFailure = { exception ->
                    _error.value = exception.message ?: "حدث خطأ"
                    _loading.value = false
                }
            )
        }
    }
    
    fun verifyOTP(
        phone: String,
        otpCode: String,
        username: String,
        deviceId: String? = null,
        deviceName: String? = null
    ) {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            
            authRepository.verifyOTP(phone, otpCode, username, deviceId, deviceName).fold(
                onSuccess = { authResponse ->
                    tokenManager.saveToken(authResponse.token)
                    authResponse.user?.let { user ->
                        tokenManager.saveUserId(user.id)
                    }
                    _authSuccess.value = true
                    _loading.value = false
                },
                onFailure = { exception ->
                    _error.value = exception.message ?: "رمز التحقق غير صحيح"
                    _loading.value = false
                }
            )
        }
    }
}

