package com.arabchat.ui.chat.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arabchat.data.api.ApiClient
import com.arabchat.data.model.ChatRoom
import com.arabchat.data.repository.ChatRepository
import kotlinx.coroutines.launch

class ChatsViewModel(private val context: android.content.Context) : ViewModel() {
    
    private val chatRepository = ChatRepository(ApiClient.getApiService())
    
    private val _chatRooms = MutableLiveData<List<ChatRoom>>()
    val chatRooms: LiveData<List<ChatRoom>> = _chatRooms
    
    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading
    
    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error
    
    fun loadChatRooms() {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            
            chatRepository.getChatRooms().fold(
                onSuccess = { rooms ->
                    _chatRooms.value = rooms
                    _loading.value = false
                },
                onFailure = { exception ->
                    _error.value = exception.message
                    _loading.value = false
                }
            )
        }
    }
}

