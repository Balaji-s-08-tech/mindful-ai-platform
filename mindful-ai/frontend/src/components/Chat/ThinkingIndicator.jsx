import React from 'react'
import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'

export default function ThinkingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      className="flex gap-3 px-2 py-1"
    >
      <div className="w-7 h-7 rounded-xl flex-shrink-0 flex items-center justify-center
                      bg-sage-500/20 border border-sage-500/30">
        <Sparkles size={12} className="text-sage-400" />
      </div>
      <div className="bg-ink-800/60 border border-ink-700/40 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-sage-400 thinking-dot"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}
