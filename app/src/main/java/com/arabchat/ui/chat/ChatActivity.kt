package com.arabchat.ui.chat

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.arabchat.R
import com.arabchat.databinding.ActivityChatBinding
import com.arabchat.ui.chat.viewmodel.ChatViewModel
import com.arabchat.ui.chat.viewmodel.ChatViewModelFactory

class ChatActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityChatBinding
    private lateinit var viewModel: ChatViewModel
    private lateinit var adapter: MessagesAdapter
    private var roomId: Int = -1
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChatBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        roomId = intent.getIntExtra("room_id", -1)
        if (roomId == -1) {
            finish()
            return
        }
        
        val factory = ChatViewModelFactory(requireContext(), roomId)
        viewModel = ViewModelProvider(this, factory)[ChatViewModel::class.java]
        
        setupRecyclerView()
        setupObservers()
        
        binding.btnSend.setOnClickListener {
            val message = binding.etMessage.text.toString().trim()
            if (message.isNotEmpty()) {
                viewModel.sendMessage(message)
                binding.etMessage.text?.clear()
            }
        }
        
        viewModel.loadMessages()
    }
    
    private fun setupRecyclerView() {
        val tokenManager = com.arabchat.util.TokenManager(this)
        adapter = MessagesAdapter(tokenManager.getUserId())
        binding.recyclerView.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        binding.recyclerView.adapter = adapter
    }
    
    private fun setupObservers() {
        viewModel.messages.observe(this) { messages ->
            adapter.submitList(messages)
            binding.recyclerView.scrollToPosition(messages.size - 1)
        }
        
        viewModel.error.observe(this) { error ->
            error?.let {
                Toast.makeText(this, it, Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun requireContext() = this
}

