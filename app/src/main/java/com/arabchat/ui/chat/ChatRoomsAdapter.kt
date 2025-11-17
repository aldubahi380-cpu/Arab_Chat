package com.arabchat.ui.chat

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.arabchat.R
import com.arabchat.data.model.ChatRoom
import com.bumptech.glide.Glide
import android.widget.ImageView

class ChatRoomsAdapter(
    private val onItemClick: (ChatRoom) -> Unit
) : ListAdapter<ChatRoom, ChatRoomsAdapter.ViewHolder>(ChatRoomDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_chat_room, parent, false)
        return ViewHolder(view, onItemClick)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    class ViewHolder(
        itemView: View,
        private val onItemClick: (ChatRoom) -> Unit
    ) : RecyclerView.ViewHolder(itemView) {
        
        private val avatar: ImageView = itemView.findViewById(R.id.avatar)
        private val name: TextView = itemView.findViewById(R.id.name)
        private val lastMessage: TextView = itemView.findViewById(R.id.lastMessage)
        private val time: TextView = itemView.findViewById(R.id.time)
        private val unreadBadge: TextView = itemView.findViewById(R.id.unreadBadge)
        
        fun bind(chatRoom: ChatRoom) {
            name.text = chatRoom.name ?: "دردشة"
            lastMessage.text = chatRoom.lastMessage?.content ?: ""
            time.text = formatTime(chatRoom.updatedAt)
            
            if (chatRoom.unreadCount > 0) {
                unreadBadge.visibility = View.VISIBLE
                unreadBadge.text = chatRoom.unreadCount.toString()
            } else {
                unreadBadge.visibility = View.GONE
            }
            
            // Load avatar
            val avatarUrl = chatRoom.participants?.firstOrNull()?.profile?.avatar
            if (avatarUrl != null) {
                Glide.with(itemView.context)
                    .load(avatarUrl)
                    .placeholder(R.drawable.ic_avatar_placeholder)
                    .into(avatar)
            }
            
            itemView.setOnClickListener {
                onItemClick(chatRoom)
            }
        }
        
        private fun formatTime(timeString: String): String {
            // TODO: Format time properly
            return timeString.takeLast(5)
        }
    }
    
    class ChatRoomDiffCallback : DiffUtil.ItemCallback<ChatRoom>() {
        override fun areItemsTheSame(oldItem: ChatRoom, newItem: ChatRoom): Boolean {
            return oldItem.id == newItem.id
        }
        
        override fun areContentsTheSame(oldItem: ChatRoom, newItem: ChatRoom): Boolean {
            return oldItem == newItem
        }
    }
}

