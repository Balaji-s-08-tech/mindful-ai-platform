
const logger = require('../config/logger')

const EMOTION_WEIGHTS = {
  facial: 0.5,
  voice:  0.3,
  text:   0.2,
}

const VALID_EMOTIONS = ['happy', 'sad', 'angry', 'fearful', 'surprised', 'disgusted', 'neutral']

function normalizeEmotionLabel(raw) {
  if (!raw || typeof raw !== 'string') return null
  const lower = raw.toLowerCase().trim()
  
  const aliases = {
    fear:       'fearful',
    scared:     'fearful',
    anxious:    'fearful',
    anxiety:    'fearful',
    surprise:   'surprised',
    disgust:    'disgusted',
    stress:     'fearful',
    stressed:   'fearful',
    calm:       'neutral',
    unknown:    'neutral',
  }
  if (VALID_EMOTIONS.includes(lower)) return lower
  return aliases[lower] || 'neutral'
}

function fuseEmotions(signals = {}) {
  const { facial, voice, text } = signals

  const scores = {}

  const addScore = (rawLabel, weight) => {
    const label = normalizeEmotionLabel(rawLabel)
    if (!label) return
    scores[label] = (scores[label] || 0) + weight
  }

  addScore(facial, EMOTION_WEIGHTS.facial)
  addScore(voice,  EMOTION_WEIGHTS.voice)
  addScore(text,   EMOTION_WEIGHTS.text)

  const entries = Object.entries(scores)
  if (entries.length === 0) return { emotion: 'neutral', confidence: 0.5 }

  const totalWeight = Object.values(EMOTION_WEIGHTS).reduce((a, b) => a + b, 0)
  entries.sort((a, b) => b[1] - a[1])

  const [dominant, score] = entries[0]
  const confidence = Math.min(score / totalWeight, 1.0)

  return { emotion: dominant, confidence: parseFloat(confidence.toFixed(3)) }
}

function buildUnifiedContext({
  message,
  userId,
  inputType = 'text',
  rawTranscript = null,
  emotionData = {},
  history = [],
}) {
  
  const cleanMessage = (message || '').toString().trim().slice(0, 8000)
  if (!cleanMessage) {
    throw new Error('Message content is empty after normalization')
  }

  const facialRaw  = emotionData?.facial   || null
  const voiceRaw   = emotionData?.voice    || null
  const textRaw    = emotionData?.text     || null
  const combinedRaw = emotionData?.combined || null

  let dominantEmotion, confidence

  if (combinedRaw) {
    dominantEmotion = normalizeEmotionLabel(combinedRaw)
    confidence      = emotionData?.facialConfidence
      ? parseFloat(emotionData.facialConfidence.toFixed(3))
      : 0.6
  } else {
    const fused = fuseEmotions({ facial: facialRaw, voice: voiceRaw, text: textRaw })
    dominantEmotion = fused.emotion
    confidence      = fused.confidence
  }

  const normalizedHistory = (history || [])
    .filter(m => m && m.role && m.content)
    .map(m => ({
      role:    m.role === 'assistant' ? 'assistant' : 'user',
      content: (m.content || '').toString().slice(0, 4000),
    }))

  const ctx = {
    message:     cleanMessage,
    emotion:     dominantEmotion,
    confidence,
    emotionContext: {
      facial:   normalizeEmotionLabel(facialRaw),
      voice:    normalizeEmotionLabel(voiceRaw),
      text:     normalizeEmotionLabel(textRaw),
      combined: dominantEmotion,
    },
    input_type: inputType === 'voice' ? 'voice' : 'text',
    timestamp:  new Date().toISOString(),
    user_id:    userId ? userId.toString() : 'anonymous',
    history:    normalizedHistory,
    meta: {
      rawTranscript:    rawTranscript || null,
      audioProcessed:   inputType === 'voice',
      facialConfidence: emotionData?.facialConfidence || null,
    },
  }

  logger.info(`[InputNormalizer] Built context — emotion: ${ctx.emotion} (${ctx.confidence}), input: ${ctx.input_type}, history: ${ctx.history.length} msgs`)
  return ctx
}

function validateContext(ctx) {
  const required = ['message', 'emotion', 'confidence', 'input_type', 'timestamp', 'user_id']
  for (const field of required) {
    if (ctx[field] === undefined || ctx[field] === null) {
      throw new Error(`UnifiedContext missing required field: ${field}`)
    }
  }
  if (!['text', 'voice'].includes(ctx.input_type)) {
    throw new Error(`Invalid input_type: ${ctx.input_type}`)
  }
  if (ctx.confidence < 0 || ctx.confidence > 1) {
    throw new Error(`Confidence out of range: ${ctx.confidence}`)
  }
}

module.exports = { buildUnifiedContext, fuseEmotions, normalizeEmotionLabel, validateContext }
