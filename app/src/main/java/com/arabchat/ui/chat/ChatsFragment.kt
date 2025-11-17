package com.arabchat.ui.chat

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.arabchat.databinding.FragmentChatsBinding
import com.arabchat.ui.chat.viewmodel.ChatsViewModel
import com.arabchat.ui.chat.viewmodel.ChatsViewModelFactory

class ChatsFragment : Fragment() {
    
    private var _binding: FragmentChatsBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: ChatsViewModel
    private lateinit var adapter: ChatRoomsAdapter
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentChatsBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        val factory = ChatsViewModelFactory(requireContext())
        viewModel = ViewModelProvider(this, factory)[ChatsViewModel::class.java]
        
        adapter = ChatRoomsAdapter { chatRoom ->
            val intent = Intent(requireContext(), ChatActivity::class.java)
            intent.putExtra("room_id", chatRoom.id)
            startActivity(intent)
        }
        
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter
        
        viewModel.chatRooms.observe(viewLifecycleOwner) { rooms ->
            adapter.submitList(rooms)
            binding.emptyView.visibility = if (rooms.isEmpty()) View.VISIBLE else View.GONE
        }
        
        viewModel.loading.observe(viewLifecycleOwner) { isLoading ->
            binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
        }
        
        viewModel.loadChatRooms()
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

