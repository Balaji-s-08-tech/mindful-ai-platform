import React, { useRef, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Camera, CameraOff, Loader } from 'lucide-react'
import { useEmotionStore } from '../../store/emotionStore'
import { startEmotionDetection, stopEmotionDetection } from '../../services/emotionService'

const EMOTION_EMOJI = {
  happy: '😊', sad: '😢', angry: '😠', fearful: '😰',
  surprised: '😲', disgusted: '😒', neutral: '😐', stressed: '😤',
}

export default function CameraPanel() {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [isActive, setIsActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastResult, setLastResult] = useState(null)

  const { setCameraActive, updateFacialEmotion, facialEmotion } = useEmotionStore()

  const startCamera = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setIsActive(true)
      setCameraActive(true)

      startEmotionDetection(videoRef.current, (result) => {
        setLastResult(result)
        updateFacialEmotion(result.dominant_emotion)
      }, 3000)
    } catch (err) {
      setError(err.name === 'NotAllowedError'
        ? 'Camera permission denied'
        : 'Camera not available'
      )
    } finally {
      setIsLoading(false)
    }
  }, [setCameraActive, updateFacialEmotion])

  const stopCamera = useCallback(() => {
    stopEmotionDetection()
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setIsActive(false)
    setCameraActive(false)
    setLastResult(null)
  }, [setCameraActive])

  useEffect(() => {
    return () => stopCamera()
  }, [stopCamera])

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-ink-800/50">
        <div className="flex items-center gap-2">
          <Camera size={13} className={isActive ? 'text-sage-400' : 'text-ink-500'} />
          <span className="text-xs font-medium text-ink-300">Facial Detection</span>
        </div>
        <button
          onClick={isActive ? stopCamera : startCamera}
          disabled={isLoading}
          className={`text-xs px-2.5 py-1 rounded-lg transition-all duration-200 font-medium
            ${isActive
              ? 'bg-blush-500/15 text-blush-400 hover:bg-blush-500/25 border border-blush-500/25'
              : 'bg-sage-500/15 text-sage-400 hover:bg-sage-500/25 border border-sage-500/25'
            } disabled:opacity-40`}
        >
          {isLoading ? 'Starting…' : isActive ? 'Stop' : 'Start'}
        </button>
      </div>

      {}
      <div className="relative aspect-[4/3] bg-ink-950">
        {}
        <video
          ref={videoRef}
          className={`w-full h-full object-cover transition-opacity duration-300 ${isActive ? 'opacity-100' : 'opacity-0'}`}
          playsInline
          muted
          style={{ transform: 'scaleX(-1)' }} 
        />

        {}
        {!isActive && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            {isLoading ? (
              <Loader size={20} className="text-ink-500 animate-spin" />
            ) : (
              <>
                <CameraOff size={20} className="text-ink-700" />
                {error ? (
                  <p className="text-ink-600 text-xs text-center px-4">{error}</p>
                ) : (
                  <p className="text-ink-600 text-xs">Camera off</p>
                )}
              </>
            )}
          </div>
        )}

        {}
        <AnimatePresence>
          {isActive && lastResult && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="absolute bottom-2 left-2 right-2 flex items-center justify-between"
            >
              {}
              <div className="flex items-center gap-1.5 bg-ink-950/80 backdrop-blur-sm 
                             border border-ink-700/50 rounded-lg px-2 py-1">
                <span className="text-sm">{EMOTION_EMOJI[lastResult.dominant_emotion] || '😐'}</span>
                <span className="text-xs text-ink-200 capitalize">{lastResult.dominant_emotion}</span>
              </div>

              {}
              <div className="bg-ink-950/80 backdrop-blur-sm border border-ink-700/50 rounded-lg px-2 py-1">
                <span className="text-ink-400 text-xs font-mono">
                  {Math.round((lastResult.confidence || 0) * 100)}%
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {}
        {isActive && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <motion.div
              animate={{ y: ['0%', '100%', '0%'] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
              className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-sage-400/30 to-transparent"
            />
            {}
            <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-sage-400/40 rounded-tl" />
            <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-sage-400/40 rounded-tr" />
            <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-sage-400/40 rounded-bl" />
            <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-sage-400/40 rounded-br" />
          </div>
        )}
      </div>

      {}
      {isActive && lastResult?.emotions && (
        <div className="p-3 space-y-1.5 border-t border-ink-800/50">
          {Object.entries(lastResult.emotions)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 4)
            .map(([emotion, score]) => (
              <div key={emotion} className="flex items-center gap-2">
                <span className="text-ink-500 text-xs w-14 capitalize">{emotion}</span>
                <div className="flex-1 h-1 bg-ink-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.round(score * 100)}%` }}
                    transition={{ duration: 0.5 }}
                    className={`h-full rounded-full ${
                      emotion === lastResult.dominant_emotion ? 'bg-sage-400' : 'bg-ink-600'
                    }`}
                  />
                </div>
                <span className="text-ink-600 text-xs font-mono w-8 text-right">
                  {Math.round(score * 100)}%
                </span>
              </div>
            ))
          }
        </div>
      )}
    </div>
  )
}
