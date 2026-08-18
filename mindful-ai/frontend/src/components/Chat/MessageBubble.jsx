import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, User, Volume2, VolumeX, Mic } from 'lucide-react'
import { format } from 'date-fns'
import { speakText, stopSpeaking } from '../../services/voiceService'

const EMOTION_EMOJI = {
  happy:     '😊',
  sad:       '😢',
  angry:     '😠',
  fearful:   '😰',
  surprised: '😲',
  disgusted: '😒',
  neutral:   '😐',
  stressed:  '😤',
}

const EMOTION_COLOR = {
  happy:     'text-yellow-400/70',
  sad:       'text-blue-400/70',
  angry:     'text-red-400/70',
  fearful:   'text-purple-400/70',
  surprised: 'text-orange-400/70',
  neutral:   'text-ink-500',
}

export default function MessageBubble({ message, isStreaming = false, onPlayAudio }) {
  const isUser   = message.role === 'user'
  const isVoice  = message.inputType === 'voice'
  const [speaking, setSpeaking] = useState(false)

  const handleSpeak = () => {
    if (speaking) {
      stopSpeaking()
      setSpeaking(false)
    } else {
      const utterance = speakText(message.content)
      setSpeaking(true)
      if (utterance) {
        utterance.onend  = () => setSpeaking(false)
        utterance.onerror = () => setSpeaking(false)
      }
    }
  }

  const emotion = message.emotionContext?.combined

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: [0.34, 1.56, 0.64, 1] }}
      className={`flex gap-3 group px-2 py-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >

      {}
      <div className={`w-7 h-7 rounded-xl flex-shrink-0 flex items-center justify-center
        ${isUser
          ? 'bg-ink-700/70 border border-ink-600/40'
          : 'bg-sage-500/20 border border-sage-500/30'
        }`}
      >
        {isUser
          ? (isVoice ? <Mic size={11} className="text-sage-400" /> : <User size={12} className="text-ink-400" />)
          : <Sparkles size={12} className="text-sage-400" />
        }
      </div>

      {}
      <div className={`max-w-[75%] space-y-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>

        {}
        {isUser && emotion && (
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`text-xs px-1.5 self-end flex items-center gap-1 ${EMOTION_COLOR[emotion] || 'text-ink-600'}`}
          >
            {EMOTION_EMOJI[emotion] || ''}
            <span className="capitalize">{emotion}</span>
            {isVoice && <span className="opacity-50">· voice</span>}
          </motion.span>
        )}

        {}
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed relative
          ${isUser
            ? 'bg-sage-500/20 border border-sage-500/25 text-ink-100 rounded-tr-sm'
            : 'bg-ink-800/60 border border-ink-700/40 text-ink-100 rounded-tl-sm'
          }`}
        >
          {formatContent(message.content)}

          {}
          {isStreaming && (
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.8, repeat: Infinity }}
              className="inline-block w-0.5 h-4 bg-sage-400 ml-0.5 align-middle rounded-full"
            />
          )}
        </div>

        {}
        {!isStreaming && (
          <div className={`flex items-center gap-2 px-1 opacity-0 group-hover:opacity-100 transition-opacity
            ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <span className="text-ink-700 text-xs">
              {message.createdAt ? format(new Date(message.createdAt), 'h:mm a') : ''}
            </span>

            {!isUser && (
              <button
                onClick={handleSpeak}
                className="text-ink-600 hover:text-sage-400 transition-colors"
                title={speaking ? 'Stop speaking' : 'Listen to this response'}
              >
                {speaking ? <VolumeX size={12} /> : <Volume2 size={12} />}
              </button>
            )}

            {}
            {!isUser && message.model && message.model !== 'crisis-handler' && (
              <span className="text-ink-700 text-[10px]">
                {message.model.includes('gemma') ? '🟢' : '☁️'}
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}

function formatContent(content) {
  if (!content) return null

  const lines = content.split('\n')

  return lines.map((line, i) => {
    if (!line.trim()) return <br key={i} />

    if (/^[-*•]\s+/.test(line)) {
      const text = line.replace(/^[-*•]\s+/, '')
      return (
        <p key={i} className={`flex gap-2 ${i > 0 ? 'mt-1' : ''}`}>
          <span className="text-sage-500 font-bold mt-0.5 flex-shrink-0">·</span>
          <span>{formatInline(text)}</span>
        </p>
      )
    }

    return (
      <p key={i} className={i > 0 ? 'mt-1' : ''}>
        {formatInline(line)}
      </p>
    )
  })
}

function formatInline(text) {
  
  const parts = text.split(/\*\*(.*?)\*\*/g)
  return parts.map((part, j) =>
    j % 2 === 1
      ? <strong key={j} className="font-semibold text-sage-300">{part}</strong>
      : part
  )
}
