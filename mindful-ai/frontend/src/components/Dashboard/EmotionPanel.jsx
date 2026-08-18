import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Lightbulb, Activity } from 'lucide-react'
import { useEmotionStore } from '../../store/emotionStore'

const EMOTION_CONFIG = {
  happy:     { emoji: '😊', label: 'Happy',     color: 'emotion-happy' },
  sad:       { emoji: '😢', label: 'Sad',       color: 'emotion-sad' },
  angry:     { emoji: '😠', label: 'Angry',     color: 'emotion-angry' },
  fearful:   { emoji: '😰', label: 'Anxious',   color: 'emotion-fearful' },
  surprised: { emoji: '😲', label: 'Surprised', color: 'emotion-surprised' },
  disgusted: { emoji: '😒', label: 'Uneasy',    color: 'emotion-disgusted' },
  neutral:   { emoji: '😐', label: 'Neutral',   color: 'emotion-neutral' },
  stressed:  { emoji: '😤', label: 'Stressed',  color: 'emotion-angry' },
}

function EmotionBadge({ emotion, label, icon }) {
  const cfg = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.neutral
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-500 text-xs">{label}</span>
      {emotion ? (
        <span className={`text-xs px-2 py-0.5 rounded-full border ${cfg.color} flex items-center gap-1`}>
          {cfg.emoji} {cfg.label}
        </span>
      ) : (
        <span className="text-xs px-2 py-0.5 rounded-full border border-ink-700/50 text-ink-600">
          Detecting…
        </span>
      )}
    </div>
  )
}

export default function EmotionPanel() {
  const { facialEmotion, voiceTone, textSentiment, combinedEmotion, suggestions, cameraActive } = useEmotionStore()

  const combined = EMOTION_CONFIG[combinedEmotion] || null

  return (
    <div className="space-y-3">
      {}
      <div className="glass rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Brain size={14} className="text-sage-400" />
          <h3 className="text-ink-300 text-xs font-semibold uppercase tracking-wider">
            Emotional State
          </h3>
        </div>

        {}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-ink-800/60 border border-ink-700/40 
                         flex items-center justify-center text-2xl">
            {combined ? combined.emoji : '🔍'}
          </div>
          <div>
            <p className="text-ink-100 font-medium">
              {combined ? combined.label : 'Analysing…'}
            </p>
            <p className="text-ink-500 text-xs">Multi-modal detection</p>
          </div>
        </div>

        {}
        <div className="space-y-2">
          <EmotionBadge emotion={facialEmotion} label="Facial" />
          <EmotionBadge emotion={voiceTone} label="Voice" />
          <EmotionBadge emotion={textSentiment} label="Text" />
        </div>
      </div>

      {}
      <div className="glass rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={14} className="text-sage-400" />
          <h3 className="text-ink-300 text-xs font-semibold uppercase tracking-wider">
            Signal Inputs
          </h3>
        </div>
        <div className="space-y-2">
          {[
            { label: 'Camera', active: cameraActive, weight: '50%' },
            { label: 'Voice', active: !!voiceTone, weight: '30%' },
            { label: 'Text', active: !!textSentiment, weight: '20%' },
          ].map(({ label, active, weight }) => (
            <div key={label} className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-sage-400' : 'bg-ink-700'}`} />
              <span className="text-ink-400 text-xs flex-1">{label}</span>
              <span className="text-ink-600 text-xs font-mono">{weight}</span>
              <div className="w-16 h-1 bg-ink-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${active ? 'bg-sage-400' : 'bg-ink-700'}`}
                  style={{ width: active ? weight : '0%' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {}
      <AnimatePresence>
        {suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="glass rounded-2xl p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb size={14} className="text-amber-400" />
              <h3 className="text-ink-300 text-xs font-semibold uppercase tracking-wider">
                Suggestions
              </h3>
            </div>
            <div className="space-y-2">
              {suggestions.slice(0, 2).map((s, i) => (
                <div key={i} className="flex items-start gap-2 bg-ink-800/40 rounded-xl p-2.5">
                  <span className="text-base leading-none mt-0.5">{s.icon}</span>
                  <p className="text-ink-300 text-xs leading-relaxed">{s.text}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
