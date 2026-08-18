import React from 'react'
import { motion } from 'framer-motion'
import { Heart, Mic, Camera, Brain } from 'lucide-react'

const FEATURES = [
  { icon: Heart, label: 'Compassionate AI support', color: 'text-blush-400', bg: 'bg-blush-400/10' },
  { icon: Mic, label: 'Voice conversation', color: 'text-sage-400', bg: 'bg-sage-400/10' },
  { icon: Camera, label: 'Facial emotion detection', color: 'text-blue-400', bg: 'bg-blue-400/10' },
  { icon: Brain, label: 'Multi-modal understanding', color: 'text-purple-400', bg: 'bg-purple-400/10' },
]

const STARTERS = [
  "I've been feeling really overwhelmed lately…",
  "I need help managing my anxiety",
  "I'm having trouble sleeping because of stress",
  "Can you help me with a breathing exercise?",
]

export default function WelcomeScreen() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-12 px-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center max-w-lg"
      >
        {}
        <div className="relative inline-flex mb-8">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-sage-500/30 to-ink-600/30 
                         border border-sage-500/20 flex items-center justify-center glow-sage">
            <Heart size={32} className="text-sage-300" />
          </div>
          <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-sage-500/20 
                         border border-sage-500/30 animate-pulse-slow" />
        </div>

        <h2 className="font-display text-2xl text-ink-100 mb-3">
          Hello, I'm here for you
        </h2>
        <p className="text-ink-400 text-sm leading-relaxed mb-8 max-w-sm mx-auto">
          This is a safe, judgment-free space. Share what's on your mind — 
          I'll listen and offer compassionate support.
        </p>

        {}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {FEATURES.map(({ icon: Icon, label, color, bg }) => (
            <div key={label} className={`flex items-center gap-1.5 ${bg} rounded-full px-3 py-1.5`}>
              <Icon size={12} className={color} />
              <span className="text-xs text-ink-400">{label}</span>
            </div>
          ))}
        </div>

        {}
        <div className="space-y-2">
          <p className="text-ink-600 text-xs mb-3">Or start with one of these…</p>
          {STARTERS.map((starter, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * i + 0.3 }}
              onClick={() => {
                window.dispatchEvent(new CustomEvent('voice-transcript', {
                  detail: { transcript: starter }
                }))
              }}
              className="w-full text-left text-xs text-ink-400 hover:text-ink-200 
                         bg-ink-800/30 hover:bg-ink-800/60 border border-ink-700/30 
                         hover:border-ink-600/50 rounded-xl px-4 py-2.5 
                         transition-all duration-150 italic"
            >
              "{starter}"
            </motion.button>
          ))}
        </div>
      </motion.div>

      {}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-ink-700 text-xs text-center mt-10 max-w-sm leading-relaxed"
      >
        ⚠️ MindfulAI is an emotional support tool, not a licensed therapist.
        For serious mental health concerns, please consult a qualified professional.
      </motion.p>
    </div>
  )
}
