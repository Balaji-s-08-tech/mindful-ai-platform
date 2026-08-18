import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, X } from 'lucide-react'

export default function DisclaimerBanner({ onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex items-start gap-3 bg-amber-500/10 border-b border-amber-500/20 px-4 py-3"
    >
      <AlertTriangle size={15} className="text-amber-400 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-amber-300/90 text-xs leading-relaxed">
          <span className="font-semibold">Important: </span>
          MindfulAI provides emotional support and is not a substitute for professional mental health 
          care. If you are experiencing a mental health crisis, please contact the{' '}
          <a href="tel:988" className="underline hover:text-amber-200">988 Suicide & Crisis Lifeline</a>{' '}
          or emergency services immediately.
        </p>
      </div>
      <button
        onClick={onClose}
        className="text-amber-500/60 hover:text-amber-400 flex-shrink-0 transition-colors"
      >
        <X size={14} />
      </button>
    </motion.div>
  )
}
