
let recognition = null
let mediaRecorder = null
let audioChunks = []

export function isSpeechRecognitionSupported() {
  return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
}

export function startBrowserSTT(onTranscript, onEnd, onError) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    onError?.('Speech recognition not supported in this browser')
    return null
  }

  recognition = new SpeechRecognition()
  recognition.continuous = false
  recognition.interimResults = true
  recognition.lang = 'en-US'
  recognition.maxAlternatives = 1

  recognition.onresult = (event) => {
    let interim = ''
    let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) final += transcript
      else interim += transcript
    }
    onTranscript?.(final || interim, !!final)
  }

  recognition.onend = () => onEnd?.()
  recognition.onerror = (event) => onError?.(event.error)

  recognition.start()
  return recognition
}

export function stopBrowserSTT() {
  if (recognition) {
    recognition.stop()
    recognition = null
  }
}

export async function startWhisperRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  audioChunks = []
  mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data)
  }

  mediaRecorder.start(250) 
  return mediaRecorder
}

export async function stopWhisperRecording() {
  return new Promise((resolve, reject) => {
    if (!mediaRecorder) return reject('No recording in progress')

    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      const formData = new FormData()
      formData.append('audio', blob, 'recording.webm')

      try {
        const token = localStorage.getItem('mindful_token')
        const response = await fetch('/api/voice/transcribe', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        })
        const data = await response.json()
        resolve(data.transcript || '')
      } catch (err) {
        reject(err)
      }
    }

    mediaRecorder.stop()
    mediaRecorder.stream.getTracks().forEach(t => t.stop())
  })
}

let currentUtterance = null

export function speakText(text, { rate = 0.95, pitch = 1.0, volume = 1.0 } = {}) {
  if (!window.speechSynthesis) return

  stopSpeaking()

  currentUtterance = new SpeechSynthesisUtterance(text)
  currentUtterance.rate = rate
  currentUtterance.pitch = pitch
  currentUtterance.volume = volume

  const voices = window.speechSynthesis.getVoices()
  const preferred = voices.find(v =>
    v.name.includes('Samantha') ||
    v.name.includes('Karen') ||
    v.name.includes('Google US English') ||
    v.name.includes('Microsoft Aria')
  ) || voices.find(v => v.lang.startsWith('en'))

  if (preferred) currentUtterance.voice = preferred

  window.speechSynthesis.speak(currentUtterance)
  return currentUtterance
}

export function stopSpeaking() {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
  currentUtterance = null
}

export function isSpeaking() {
  return window.speechSynthesis?.speaking || false
}

export async function speakWithElevenLabs(text) {
  try {
    const token = localStorage.getItem('mindful_token')
    const response = await fetch('/api/voice/tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text }),
    })

    if (!response.ok) throw new Error('TTS request failed')

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => URL.revokeObjectURL(url)
    audio.play()
    return audio
  } catch (err) {
    console.error('ElevenLabs TTS failed, falling back to browser TTS:', err)
    speakText(text)
  }
}
