import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Sparkles, Plus, MessageSquare, ChevronLeft, ChevronRight,
  LogOut, User, Clock
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useChatStore } from '../../store/chatStore'
import { formatDistanceToNow } from 'date-fns'
import toast from 'react-hot-toast'

export default function Sidebar({ isOpen, onToggle }) {
  const { user, logout } = useAuthStore()
  const { sessions, currentSessionId, createSession, loadMessages } = useChatStore()

  const handleNewChat = async () => {
    await createSession()
    toast.success('New conversation started')
  }

  const handleSelectSession = (sessionId) => {
    if (sessionId !== currentSessionId) {
      loadMessages(sessionId)
    }
  }

  return (
    <>
      {}
      <button
        onClick={onToggle}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-ink-800 border border-ink-700/50 
                   rounded-r-lg p-1.5 text-ink-400 hover:text-ink-200 transition-all"
        style={{ left: isOpen ? '256px' : '0px', transition: 'left 0.3s ease' }}
      >
        {isOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 256, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="h-full flex flex-col bg-ink-900/80 border-r border-ink-800/50 overflow-hidden"
          >
            {}
            <div className="p-4 border-b border-ink-800/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-sage-500/20 border border-sage-500/30 
                               flex items-center justify-center flex-shrink-0">
                  <Sparkles size={14} className="text-sage-400" />
                </div>
                <div>
                  <p className="font-display text-ink-100 text-sm font-semibold">MindfulAI</p>
                  <p className="text-ink-500 text-xs">Emotional Support</p>
                </div>
              </div>
            </div>

            {}
            <div className="p-3">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 bg-sage-500/15 hover:bg-sage-500/25 
                           border border-sage-500/30 text-sage-300 hover:text-sage-200
                           rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200"
              >
                <Plus size={15} />
                New conversation
              </button>
            </div>

            {}
            <div className="flex-1 overflow-y-auto px-2 pb-2">
              {sessions.length === 0 ? (
                <p className="text-ink-600 text-xs text-center py-6 px-4">
                  No conversations yet. Start a new one above.
                </p>
              ) : (
                <div className="space-y-1">
                  <p className="text-ink-600 text-xs font-medium px-2 py-2 uppercase tracking-wider">
                    Recent
                  </p>
                  {sessions.map((session) => (
                    <button
                      key={session._id}
                      onClick={() => handleSelectSession(session._id)}
                      className={`w-full text-left rounded-xl px-3 py-2.5 transition-all duration-150 group
                        ${currentSessionId === session._id
                          ? 'bg-ink-700/70 border border-ink-600/40 text-ink-100'
                          : 'hover:bg-ink-800/50 text-ink-400 hover:text-ink-200'
                        }`}
                    >
                      <div className="flex items-start gap-2">
                        <MessageSquare size={13} className="mt-0.5 flex-shrink-0 opacity-60" />
                        <div className="min-w-0">
                          <p className="text-xs font-medium truncate">
                            {session.title || 'Conversation'}
                          </p>
                          <div className="flex items-center gap-1 mt-0.5">
                            <Clock size={10} className="opacity-40" />
                            <p className="text-ink-600 text-xs">
                              {formatDistanceToNow(new Date(session.updatedAt), { addSuffix: true })}
                            </p>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {}
            <div className="p-3 border-t border-ink-800/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sage-500/40 to-ink-600/40 
                               border border-ink-600/40 flex items-center justify-center flex-shrink-0">
                  <User size={14} className="text-sage-300" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-ink-200 text-xs font-medium truncate">{user?.name}</p>
                  <p className="text-ink-500 text-xs truncate">{user?.email}</p>
                </div>
                <button
                  onClick={logout}
                  title="Sign out"
                  className="text-ink-600 hover:text-blush-400 transition-colors flex-shrink-0"
                >
                  <LogOut size={14} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
