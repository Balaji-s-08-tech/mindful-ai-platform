import React, { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { useChatStore } from '../../store/chatStore'
import { useEmotionStore } from '../../store/emotionStore'
import {
  startBrowserSTT,
  stopBrowserSTT,
  isSpeechRecognitionSupported,
  startWhisperRecording,
  stopWhisperRecording,
} from '../../services/voiceService'

export default function VoiceButton() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [mode, setMode] = useState('idle') 
  const { sendMessage, currentSessionId } = useChatStore()
  const { combinedEmotion, updateVoiceTone } = useEmotionStore()
  const useWhisper = !isSpeechRecognitionSupported()

  const startRecording = useCallback(async () => {
    if (!currentSessionId) {
      toast.error('Start a conversation first')
      return
    }
    setTranscript('')
    setMode('recording')
    setIsRecording(true)

    if (useWhisper) {
      try {
        await startWhisperRecording()
      } catch (err) {
        toast.error('Microphone access denied')
        setMode('idle')
        setIsRecording(false)
      }
    } else {
      startBrowserSTT(
        (text, isFinal) => {
          setTranscript(text)
          if (isFinal && text) {
            
          }
        },
        () => {
          
          setMode('idle')
          setIsRecording(false)
        },
        (err) => {
          if (err !== 'no-speech') toast.error(`Voice error: ${err}`)
          setMode('idle')
          setIsRecording(false)
        }
      )
    }
  }, [currentSessionId, useWhisper])

  const stopAndSend = useCallback(async () => {
    setMode('processing')
    setIsRecording(false)

    let finalText = transcript

    if (useWhisper) {
      try {
        finalText = await stopWhisperRecording()
      } catch (err) {
        toast.error('Transcription failed')
        setMode('idle')
        return
      }
    } else {
      stopBrowserSTT()
    }

    if (finalText?.trim()) {
      
      const lower = finalText.toLowerCase()
      const tone = lower.includes('stress') || lower.includes('anxious') ? 'fearful'
        : lower.includes('sad') || lower.includes('cry') ? 'sad'
        : lower.includes('happy') || lower.includes('great') ? 'happy'
        : 'neutral'
      updateVoiceTone(tone)

      window.dispatchEvent(new CustomEvent('voice-transcript', {
        detail: { transcript: finalText }
      }))

      try {
        await sendMessage(finalText, {
          combined: combinedEmotion,
          voice: tone,
        })
      } catch (err) {
        toast.error('Failed to send voice message')
      }
    } else {
      toast('No speech detected', { icon: '🎤' })
    }

    setTranscript('')
    setMode('idle')
  }, [transcript, useWhisper, updateVoiceTone, sendMessage, combinedEmotion])

  const cancel = () => {
    stopBrowserSTT()
    setTranscript('')
    setMode('idle')
    setIsRecording(false)
  }

  return (
    <div className="absolute bottom-20 right-6 flex flex-col items-end gap-2 z-10">
      {}
      <AnimatePresence>
        {transcript && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            className="glass rounded-2xl px-4 py-2.5 max-w-xs text-sm text-ink-200 italic"
          >
            "{transcript}"
          </motion.div>
        )}
      </AnimatePresence>

      {}
      <div className="flex items-center gap-2">
        {}
        <AnimatePresence>
          {isRecording && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={cancel}
              className="w-10 h-10 rounded-full bg-ink-800/90 border border-ink-700/50 
                         text-ink-400 hover:text-blush-400 flex items-center justify-center 
                         transition-colors"
            >
              <X size={16} />
            </motion.button>
          )}
        </AnimatePresence>

        {}
        <motion.button
          onClick={isRecording ? stopAndSend : startRecording}
          disabled={mode === 'processing'}
          whileTap={{ scale: 0.93 }}
          className={`relative w-14 h-14 rounded-full flex items-center justify-center 
                     shadow-lg transition-all duration-200
            ${isRecording
              ? 'bg-blush-500 recording-pulse'
              : mode === 'processing'
                ? 'bg-ink-700'
                : 'bg-sage-500 hover:bg-sage-400 glow-sage'
            } disabled:cursor-not-allowed`}
        >
          {mode === 'processing' ? (
            <div className="flex gap-0.5 items-end h-5">
              {[1, 2, 3, 4, 5].map(i => (
                <div
                  key={i}
                  className="w-0.5 bg-ink-400 rounded-full wave-bar"
                  style={{ height: `${20 + i * 4}px`, animationDelay: `${i * 0.08}s` }}
                />
              ))}
            </div>
          ) : isRecording ? (
            <MicOff size={20} className="text-white" />
          ) : (
            <Mic size={20} className="text-white" />
          )}
        </motion.button>
      </div>

      {}
      <p className="text-ink-600 text-xs">
        {mode === 'idle' ? 'Hold to speak' 
          : mode === 'recording' ? 'Listening…'
          : 'Processing…'
        }
      </p>
    </div>
  )
}
