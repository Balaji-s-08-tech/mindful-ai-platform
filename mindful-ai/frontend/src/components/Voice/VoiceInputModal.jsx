import React, { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, X, Send, RotateCcw } from 'lucide-react'

export default function VoiceInputModal({ onComplete, onClose }) {
  const [state, setState]             = useState('idle')     
  const [transcript, setTranscript]   = useState('')         
  const [duration, setDuration]       = useState(0)          
  const [waveform, setWaveform]       = useState(Array(24).fill(4))
  const [audioBlob, setAudioBlob]     = useState(null)
  const [errorMsg, setErrorMsg]       = useState('')

  const mediaRecorderRef = useRef(null)
  const chunksRef        = useRef([])
  const timerRef         = useRef(null)
  const analyserRef      = useRef(null)
  const animFrameRef     = useRef(null)
  const recognitionRef   = useRef(null)
  const streamRef        = useRef(null)

  const startRecording = useCallback(async () => {
    setState('requesting')
    chunksRef.current  = []
    setTranscript('')
    setDuration(0)
    setAudioBlob(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const audioCtx = new AudioContext()
      const source   = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 64
      source.connect(analyser)
      analyserRef.current = analyser

      const updateWaveform = () => {
        const data = new Uint8Array(analyser.frequencyBinCount)
        analyser.getByteFrequencyData(data)
        const bars = Array.from({ length: 24 }, (_, i) => {
          const idx = Math.floor(i * data.length / 24)
          return Math.max(3, Math.round((data[idx] / 255) * 40))
        })
        setWaveform(bars)
        animFrameRef.current = requestAnimationFrame(updateWaveform)
      }
      updateWaveform()

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        setState('stopped')
      }

      recorder.start(100)

      timerRef.current = setInterval(() => {
        setDuration(d => {
          if (d >= 120) {
            stopRecording()  
            return d
          }
          return d + 1
        })
      }, 1000)

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.continuous      = true
        recognition.interimResults  = true
        recognition.lang            = 'en-US'
        recognitionRef.current       = recognition

        recognition.onresult = (event) => {
          let interim = ''
          let final   = ''
          for (const res of event.results) {
            if (res.isFinal) final   += res[0].transcript
            else             interim += res[0].transcript
          }
          setTranscript((final || interim).trim())
        }

        recognition.onerror = (e) => {
          if (e.error !== 'no-speech') console.warn('STT error:', e.error)
        }

        recognition.start()
      }

      setState('recording')
    } catch (err) {
      setErrorMsg(
        err.name === 'NotAllowedError'
          ? 'Microphone access denied. Please allow microphone access in your browser settings.'
          : `Microphone error: ${err.message}`
      )
      setState('error')
    }
  }, [])

  const stopRecording = useCallback(() => {
    clearInterval(timerRef.current)
    cancelAnimationFrame(animFrameRef.current)

    recognitionRef.current?.stop()
    mediaRecorderRef.current?.stop()

    streamRef.current?.getTracks().forEach(track => track.stop())

    setWaveform(Array(24).fill(4))
  }, [])

  const handleSend = () => {
    if (state === 'recording') stopRecording()
    setTimeout(() => onComplete(audioBlob), 100)
  }

  const handleRetake = () => {
    setAudioBlob(null)
    setTranscript('')
    setDuration(0)
    setState('idle')
    startRecording()
  }

  const handleClose = () => {
    if (state === 'recording') stopRecording()
    onComplete(null)
    onClose()
  }

  useEffect(() => {
    startRecording()
    return () => {
      clearInterval(timerRef.current)
      cancelAnimationFrame(animFrameRef.current)
      recognitionRef.current?.stop()
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [startRecording])

  const formatTime = (secs) => `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      {}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {}
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1,   y: 0  }}
        exit={{   opacity: 0, scale: 0.9, y: 20  }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        className="relative z-10 w-full max-w-md mx-4 bg-ink-900 border border-ink-700/60
                   rounded-3xl p-8 flex flex-col items-center gap-6 shadow-2xl shadow-black/60"
      >
        {}
        <button
          onClick={handleClose}
          id="voice-modal-close"
          className="absolute top-4 right-4 w-8 h-8 rounded-xl bg-ink-800 border border-ink-700/50
                     flex items-center justify-center text-ink-500 hover:text-ink-200
                     hover:bg-ink-700 transition-all"
        >
          <X size={14} />
        </button>

        {}
        <div className="text-center">
          <h2 className="text-ink-100 font-semibold text-lg">Voice Message</h2>
          <p className="text-ink-500 text-xs mt-1">
            {state === 'recording' && 'Listening… speak naturally'}
            {state === 'stopped'   && 'Recording complete — send or retake'}
            {state === 'idle'      && 'Starting microphone…'}
            {state === 'requesting' && 'Requesting microphone access…'}
            {state === 'error'     && 'Microphone error'}
          </p>
        </div>

        {}
        <div className="flex items-center justify-center gap-[3px] h-12 w-full">
          {waveform.map((height, i) => (
            <motion.div
              key={i}
              animate={{ height: `${height}px` }}
              transition={{ duration: 0.08, ease: 'linear' }}
              className={`w-1.5 rounded-full ${
                state === 'recording' ? 'bg-sage-400' : 'bg-ink-600'
              }`}
            />
          ))}
        </div>

        {}
        <div className="flex items-center gap-3">
          {state === 'recording' && (
            <motion.div
              animate={{ scale: [1, 1.15, 1], opacity: [1, 0.7, 1] }}
              transition={{ duration: 1.2, repeat: Infinity }}
              className="w-3 h-3 rounded-full bg-red-500"
            />
          )}
          <span className={`font-mono text-lg font-semibold ${
            state === 'recording' ? 'text-ink-100' : 'text-ink-500'
          }`}>
            {formatTime(duration)}
          </span>
        </div>

        {}
        {state === 'error' && (
          <p className="text-red-400 text-sm text-center">{errorMsg}</p>
        )}

        {}
        {transcript && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full bg-ink-800/60 border border-ink-700/40 rounded-xl px-4 py-3"
          >
            <p className="text-ink-300 text-sm leading-relaxed italic">"{transcript}"</p>
          </motion.div>
        )}

        {}
        <div className="flex items-center gap-3 w-full">
          {}
          {state === 'recording' && (
            <button
              id="voice-stop-btn"
              onClick={stopRecording}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl
                         bg-ink-800 border border-ink-700/50 text-ink-300
                         hover:bg-ink-700 transition-all text-sm"
            >
              <MicOff size={15} />
              Stop
            </button>
          )}

          {state === 'stopped' && (
            <button
              id="voice-retake-btn"
              onClick={handleRetake}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl
                         bg-ink-800 border border-ink-700/50 text-ink-300
                         hover:bg-ink-700 transition-all text-sm"
            >
              <RotateCcw size={15} />
              Retake
            </button>
          )}

          {}
          {(state === 'recording' || state === 'stopped') && (
            <motion.button
              id="voice-send-btn"
              onClick={handleSend}
              whileTap={{ scale: 0.95 }}
              disabled={state === 'stopped' && !audioBlob}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl
                         bg-sage-500 hover:bg-sage-400 text-white font-medium
                         disabled:opacity-40 disabled:cursor-not-allowed
                         transition-all text-sm"
            >
              <Send size={15} />
              Send
            </motion.button>
          )}

          {state === 'error' && (
            <button
              onClick={startRecording}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl
                         bg-sage-500 hover:bg-sage-400 text-white transition-all text-sm"
            >
              <Mic size={15} />
              Try Again
            </button>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
