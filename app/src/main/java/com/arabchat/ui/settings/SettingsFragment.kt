package com.arabchat.ui.settings

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import com.arabchat.R
import com.arabchat.databinding.FragmentSettingsBinding
import com.arabchat.ui.auth.PhoneVerificationActivity
import com.arabchat.util.TokenManager

class SettingsFragment : Fragment() {
    
    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!
    private val tokenManager by lazy { TokenManager(requireContext()) }
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        binding.btnLogout.setOnClickListener {
            tokenManager.clearAll()
            startActivity(Intent(requireContext(), PhoneVerificationActivity::class.java))
            requireActivity().finishAffinity()
        }
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

