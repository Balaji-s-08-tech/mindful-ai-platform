import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import { useChatStore } from '../store/chatStore'
import { initSocket, disconnectSocket } from '../services/socketService'
import Sidebar from '../components/Dashboard/Sidebar'
import ChatInterface from '../components/Chat/ChatInterface'
import CameraPanel from '../components/Camera/CameraPanel'
import EmotionPanel from '../components/Dashboard/EmotionPanel'
import VoiceButton from '../components/Voice/VoiceButton'
import DisclaimerBanner from '../components/UI/DisclaimerBanner'

export default function DashboardPage() {
  const { user, token } = useAuthStore()
  const { loadSessions, createSession, currentSessionId } = useChatStore()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showDisclaimer, setShowDisclaimer] = useState(() => 
    !localStorage.getItem('disclaimer_seen')
  )

  useEffect(() => {
    
    const socket = initSocket(token)

    loadSessions().then(async () => {
      const { sessions, createSession: cs } = useChatStore.getState()
      if (sessions.length === 0) {
        await cs()
      } else {
        const { loadMessages } = useChatStore.getState()
        await loadMessages(sessions[0]._id)
      }
    })

    return () => disconnectSocket()
  }, [token])

  const handleDisclaimerClose = () => {
    localStorage.setItem('disclaimer_seen', 'true')
    setShowDisclaimer(false)
  }

  return (
    <div className="h-screen flex overflow-hidden bg-ink-950">
      {}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {showDisclaimer && (
          <DisclaimerBanner onClose={handleDisclaimerClose} />
        )}

        <div className="flex-1 flex min-h-0">
          {}
          <div className="flex-1 flex flex-col min-w-0">
            <ChatInterface />
          </div>

          {}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="w-72 xl:w-80 flex flex-col gap-3 p-3 border-l border-ink-800/50 overflow-y-auto"
          >
            <CameraPanel />
            <EmotionPanel />
          </motion.div>
        </div>

        {}
        <VoiceButton />
      </div>
    </div>
  )
}
