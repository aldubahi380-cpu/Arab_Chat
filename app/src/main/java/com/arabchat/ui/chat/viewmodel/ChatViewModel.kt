package com.arabchat.ui.chat.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arabchat.data.api.ApiClient
import com.arabchat.data.model.Message
import com.arabchat.data.repository.ChatRepository
import kotlinx.coroutines.launch

class ChatViewModel(private val context: android.content.Context, private val roomId: Int) : ViewModel() {
    
    private val chatRepository = ChatRepository(ApiClient.getApiService())
    
    private val _messages = MutableLiveData<List<Message>>()
    val messages: LiveData<List<Message>> = _messages
    
    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading
    
    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error
    
    fun loadMessages() {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            
            chatRepository.getMessages(roomId).fold(
                onSuccess = { messages ->
                    _messages.value = messages
                    _loading.value = false
                },
                onFailure = { exception ->
                    _error.value = exception.message
                    _loading.value = false
                }
            )
        }
    }
    
    fun sendMessage(content: String) {
        viewModelScope.launch {
            chatRepository.sendMessage(roomId, content).fold(
                onSuccess = { message ->
                    val currentMessages = _messages.value?.toMutableList() ?: mutableListOf()
                    currentMessages.add(message)
                    _messages.value = currentMessages
                },
                onFailure = { exception ->
                    _error.value = exception.message
                }
            )
        }
    }
}

