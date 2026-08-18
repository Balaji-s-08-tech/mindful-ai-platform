import React, { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, AlertTriangle, Mic, MicOff, Keyboard } from 'lucide-react'
import toast from 'react-hot-toast'
import { useChatStore } from '../../store/chatStore'
import { useEmotionStore } from '../../store/emotionStore'
import { analyzeTextSentiment } from '../../services/emotionService'
import MessageBubble from './MessageBubble'
import ThinkingIndicator from './ThinkingIndicator'
import WelcomeScreen from './WelcomeScreen'
import VoiceInputModal from '../Voice/VoiceInputModal'

export default function ChatInterface() {
  const {
    messages,
    isThinking,
    streamingMessage,
    sendMessageStream,
    sendVoiceMessage,
    currentSessionId,
    inputMode,
    setInputMode,
    lastProvider,
  } = useChatStore()

  const { combinedEmotion, updateTextSentiment } = useEmotionStore()
  const [input, setInput]                   = useState('')
  const [isSending, setIsSending]           = useState(false)
  const [showVoiceModal, setShowVoiceModal] = useState(false)
  const bottomRef   = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking, streamingMessage?.content])

  const handleInputChange = useCallback((e) => {
    setInput(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
    if (e.target.value.length > 10) {
      const sentiment = analyzeTextSentiment(e.target.value)
      updateTextSentiment(sentiment)
    }
  }, [updateTextSentiment])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isSending || !currentSessionId) return

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setIsSending(true)

    try {
      await sendMessageStream(trimmed, {
        facial:   useEmotionStore.getState().facialEmotion,
        voice:    useEmotionStore.getState().voiceTone,
        text:     useEmotionStore.getState().textSentiment,
        combined: combinedEmotion,
      })
    } catch {
      toast.error('Failed to send message. Please try again.')
    } finally {
      setIsSending(false)
      textareaRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  useEffect(() => {
    const handler = (e) => {
      if (e.detail?.transcript) setInput(e.detail.transcript)
    }
    window.addEventListener('voice-transcript', handler)
    return () => window.removeEventListener('voice-transcript', handler)
  }, [])

  const handleVoiceComplete = async (audioBlob) => {
    setShowVoiceModal(false)
    if (!audioBlob) return

    setIsSending(true)
    try {
      const result = await sendVoiceMessage(audioBlob, {
        facial:   useEmotionStore.getState().facialEmotion,
        voice:    useEmotionStore.getState().voiceTone,
        combined: combinedEmotion,
      })

      if (result?.audioBase64) {
        playAudio(result.audioBase64)
      } else if (result?.aiText) {
        
        const utter = new SpeechSynthesisUtterance(result.aiText)
        utter.rate = 0.9
        utter.pitch = 1.0
        window.speechSynthesis.speak(utter)
      }
    } catch {
      toast.error('Voice processing failed. Please try again.')
    } finally {
      setIsSending(false)
    }
  }

  const playAudio = (base64) => {
    try {
      const audio = new Audio(`data:audio/mpeg;base64,${base64}`)
      audio.play().catch(console.error)
    } catch {  }
  }

  const isActive    = currentSessionId && !isSending
  const showCrisis  = combinedEmotion && ['fearful', 'sad', 'angry'].includes(combinedEmotion) && messages.length > 0

  return (
    <div className="flex flex-col h-full">

      {}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {messages.length === 0 && !isThinking && !streamingMessage ? (
          <WelcomeScreen />
        ) : (
          <>
            {messages.map((msg, i) => (
              <MessageBubble key={msg._id || i} message={msg} onPlayAudio={playAudio} />
            ))}

            {}
            <AnimatePresence>
              {streamingMessage && (
                <motion.div
                  key="streaming"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <MessageBubble
                    message={{
                      role:    'assistant',
                      content: streamingMessage.content,
                      _id:     'streaming',
                    }}
                    isStreaming
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {}
            <AnimatePresence>
              {isThinking && !streamingMessage && <ThinkingIndicator />}
            </AnimatePresence>
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {}
      <AnimatePresence>
        {lastProvider && lastProvider !== 'fallback' && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex justify-center pb-1"
          >
            <span className="text-ink-700 text-[10px] tracking-wide">
              {lastProvider === 'gemma' ? '🟢 Local Gemma' : '☁️ Claude'}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {}
      <AnimatePresence>
        {showCrisis && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="mx-4 mb-2 flex items-center gap-2 bg-amber-500/10 border border-amber-500/25 rounded-xl px-3 py-2"
          >
            <AlertTriangle size={13} className="text-amber-400 flex-shrink-0" />
            <p className="text-amber-300/80 text-xs">
              I'm here for you. If you're in crisis, call{' '}
              <span className="font-semibold">988</span> (Suicide &amp; Crisis Lifeline).
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {}
      <div className="p-4 border-t border-ink-800/50">
        <div
          className="flex items-end gap-3 bg-ink-800/60 border border-ink-700/50 rounded-2xl
                     px-4 py-3 focus-within:border-sage-500/50 focus-within:ring-1
                     focus-within:ring-sage-500/20 transition-all duration-200"
        >
          {}
          <button
            id="input-mode-toggle"
            onClick={() => {
              if (inputMode === 'voice') {
                setInputMode('text')
              } else {
                setInputMode('voice')
                setShowVoiceModal(true)
              }
            }}
            disabled={!isActive}
            title={inputMode === 'voice' ? 'Switch to text input' : 'Switch to voice input'}
            className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center
                       text-ink-500 hover:text-sage-400 hover:bg-ink-700/50
                       disabled:opacity-30 transition-all duration-150"
          >
            {inputMode === 'voice'
              ? <MicOff size={14} />
              : <Mic    size={14} />
            }
          </button>

          <textarea
            ref={textareaRef}
            id="chat-input"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={
              inputMode === 'voice'
                ? 'Voice mode — click mic to record…'
                : "Share what's on your mind…"
            }
            rows={1}
            disabled={!isActive || inputMode === 'voice'}
            className="flex-1 bg-transparent text-ink-100 placeholder-ink-600 text-sm font-sans
                       resize-none outline-none min-h-[24px] leading-relaxed
                       disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ maxHeight: '160px' }}
          />

          {}
          <motion.button
            id="chat-send-btn"
            onClick={inputMode === 'voice' ? () => setShowVoiceModal(true) : handleSend}
            disabled={!isActive || (inputMode === 'text' && !input.trim())}
            whileTap={{ scale: 0.9 }}
            className="flex-shrink-0 w-8 h-8 rounded-xl bg-sage-500 hover:bg-sage-400
                       disabled:opacity-30 disabled:cursor-not-allowed
                       flex items-center justify-center transition-all duration-150"
          >
            {inputMode === 'voice'
              ? <Mic  size={14} className="text-white" />
              : <Send size={14} className="text-white translate-x-px" />
            }
          </motion.button>
        </div>

        <p className="text-ink-700 text-xs text-center mt-2">
          MindfulAI is not a therapist ·{' '}
          {inputMode === 'text'
            ? <>Press <kbd className="bg-ink-800 px-1 rounded text-ink-500">⏎</kbd> to send</>
            : 'Click mic to record your voice'
          }
        </p>
      </div>

      {}
      <AnimatePresence>
        {showVoiceModal && (
          <VoiceInputModal
            onComplete={handleVoiceComplete}
            onClose={() => { setShowVoiceModal(false); setInputMode('text') }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
