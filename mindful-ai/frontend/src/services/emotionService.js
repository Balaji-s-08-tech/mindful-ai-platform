
let detectionInterval = null
let canvas = null
let ctx = null

function initCanvas() {
  canvas = document.createElement('canvas')
  canvas.width = 320
  canvas.height = 240
  ctx = canvas.getContext('2d')
}

function captureFrame(videoElement) {
  if (!canvas) initCanvas()
  ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.7).split(',')[1] 
}

export async function detectEmotion(base64Frame) {
  try {
    const token = localStorage.getItem('mindful_token')
    const response = await fetch('/api/emotion/detect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ image: base64Frame }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  } catch (err) {
    
    console.warn('Emotion service unavailable, using mock:', err.message)
    return mockEmotionDetection()
  }
}

export function startEmotionDetection(videoElement, onEmotion, intervalMs = 3000) {
  stopEmotionDetection()

  detectionInterval = setInterval(async () => {
    try {
      if (!videoElement || videoElement.readyState < 2) return
      const frame = captureFrame(videoElement)
      const result = await detectEmotion(frame)
      if (result && result.dominant_emotion) {
        onEmotion(result)
      }
    } catch (err) {
      console.error('Emotion detection error:', err)
    }
  }, intervalMs)

  return detectionInterval
}

export function stopEmotionDetection() {
  if (detectionInterval) {
    clearInterval(detectionInterval)
    detectionInterval = null
  }
}

export function analyzeTextSentiment(text) {
  const lower = text.toLowerCase()
  
  const emotionPatterns = {
    sad: /\b(sad|depressed|unhappy|cry|tears|lonely|hopeless|worthless|empty|hurt)\b/,
    angry: /\b(angry|furious|rage|hate|annoyed|frustrated|mad|upset)\b/,
    fearful: /\b(scared|afraid|anxious|worried|nervous|panic|fear|terrified)\b/,
    happy: /\b(happy|joyful|excited|great|wonderful|amazing|love|grateful|thankful)\b/,
    stressed: /\b(stressed|overwhelmed|exhausted|tired|burnout|pressure|deadline)\b/,
  }

  for (const [emotion, pattern] of Object.entries(emotionPatterns)) {
    if (pattern.test(lower)) return emotion
  }
  return 'neutral'
}

const MOCK_EMOTIONS = ['happy', 'neutral', 'sad', 'surprised', 'neutral', 'neutral']
let mockIndex = 0

function mockEmotionDetection() {
  const dominant = MOCK_EMOTIONS[mockIndex % MOCK_EMOTIONS.length]
  mockIndex++
  return {
    dominant_emotion: dominant,
    confidence: 0.7 + Math.random() * 0.25,
    emotions: {
      happy: dominant === 'happy' ? 0.8 : 0.1,
      sad: dominant === 'sad' ? 0.75 : 0.05,
      neutral: dominant === 'neutral' ? 0.85 : 0.15,
      angry: 0.02,
      fearful: 0.02,
      surprised: dominant === 'surprised' ? 0.7 : 0.03,
      disgusted: 0.01,
    },
    mock: true,
  }
}
