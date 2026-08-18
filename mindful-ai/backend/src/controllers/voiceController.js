
const multer  = require('multer')
const FormData = require('form-data')
const axios   = require('axios')
const logger  = require('../config/logger')
const { buildUnifiedContext }    = require('../services/inputNormalizer')
const { generateResponse }       = require('../services/aiService')
const { ChatSession, Message }   = require('../models/ChatSession')
const { cacheDel }               = require('../config/redis')

const upload = multer({
  storage: multer.memoryStorage(),
  limits:  { fileSize: 25 * 1024 * 1024 }, 
  fileFilter: (req, file, cb) => {
    const allowedMimes = ['audio/webm', 'audio/mp4', 'audio/mpeg', 'audio/wav', 'audio/ogg']
    const allowedExts  = /\.(webm|mp3|mp4|wav|ogg|m4a)$/i
    if (allowedMimes.includes(file.mimetype) || allowedExts.test(file.originalname)) {
      cb(null, true)
    } else {
      cb(new Error('Invalid audio format'))
    }
  },
}).single('audio')

async function runWhisper(fileBuffer, originalName, mimeType) {
  if (!process.env.OPENAI_API_KEY) {
    return { transcript: '', whisperUsed: false }
  }

  const formData = new FormData()
  formData.append('file', fileBuffer, {
    filename:    originalName || 'audio.webm',
    contentType: mimeType || 'audio/webm',
  })
  formData.append('model',           'whisper-1')
  formData.append('language',        'en')
  formData.append('response_format', 'json')

  const response = await axios.post(
    'https://api.openai.com/v1/audio/transcriptions',
    formData,
    {
      headers: {
        ...formData.getHeaders(),
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      timeout: 30000,
    }
  )

  return { transcript: response.data.text || '', whisperUsed: true }
}

async function runTTS(text) {
  if (!process.env.ELEVENLABS_API_KEY || !text?.trim()) {
    return { audioBase64: null, ttsUsed: false }
  }

  const voiceId = process.env.ELEVENLABS_VOICE_ID || 'EXAVITQu4vr4xnSDxMaL'
  const response = await axios.post(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
    {
      text: text.slice(0, 2000),
      model_id: 'eleven_turbo_v2',
      voice_settings: {
        stability:        0.75,
        similarity_boost: 0.85,
        style:            0.3,
        use_speaker_boost: true,
      },
    },
    {
      headers: {
        'xi-api-key':   process.env.ELEVENLABS_API_KEY,
        'Content-Type': 'application/json',
        Accept:         'audio/mpeg',
      },
      responseType: 'arraybuffer',
      timeout:      15000,
    }
  )

  return {
    audioBase64: Buffer.from(response.data).toString('base64'),
    ttsUsed:     true,
  }
}

async function transcribe(req, res) {
  upload(req, res, async (err) => {
    if (err) return res.status(400).json({ message: err.message })
    if (!req.file) return res.status(400).json({ message: 'No audio file provided' })

    try {
      const { transcript, whisperUsed } = await runWhisper(
        req.file.buffer,
        req.file.originalname,
        req.file.mimetype
      )

      if (!whisperUsed) {
        return res.json({ transcript: '', message: 'Whisper not configured — use browser STT' })
      }

      res.json({ transcript })
    } catch (apiErr) {
      logger.error('Whisper API error:', apiErr.response?.data || apiErr.message)
      res.status(500).json({ message: 'Transcription failed', transcript: '' })
    }
  })
}

async function textToSpeech(req, res) {
  const { text } = req.body

  if (!text?.trim()) return res.status(400).json({ message: 'Text is required' })
  if (text.length > 2000) return res.status(400).json({ message: 'Text too long (max 2000 chars)' })

  if (process.env.ELEVENLABS_API_KEY) {
    try {
      const { audioBase64 } = await runTTS(text)
      const audioBuffer     = Buffer.from(audioBase64, 'base64')

      res.set({
        'Content-Type':   'audio/mpeg',
        'Content-Length': audioBuffer.byteLength,
        'Cache-Control':  'no-cache',
      })
      return res.send(audioBuffer)
    } catch (err) {
      logger.error('ElevenLabs TTS error:', err.response?.status, err.message)
    }
  }

  res.status(503).json({ message: 'TTS service not configured — use browser TTS', fallback: true })
}

async function processVoiceMessage(req, res) {
  upload(req, res, async (multerErr) => {
    if (multerErr) return res.status(400).json({ message: multerErr.message })

    const start = Date.now()

    try {
      const sessionId      = req.body?.sessionId  || null
      const requestTTS     = req.body?.requestTTS !== 'false'
      const providedTrans  = req.body?.transcript || null

      let emotionContext = {}
      try {
        emotionContext = JSON.parse(req.body?.emotionContext || '{}')
      } catch {  }

      let transcript   = providedTrans
      let whisperUsed  = false

      if (!transcript && req.file) {
        try {
          const result = await runWhisper(req.file.buffer, req.file.originalname, req.file.mimetype)
          transcript  = result.transcript
          whisperUsed = result.whisperUsed
        } catch (err) {
          logger.warn(`[VoiceController] Whisper failed: ${err.message} — proceeding without transcript`)
          transcript = ''
        }
      }

      if (!transcript?.trim()) {
        return res.status(400).json({
          message:    'Could not transcribe audio — please try again or type your message',
          transcript: '',
        })
      }

      const history = []

      if (sessionId && req.user) {
        try {
          const msgs = await Message.find({ sessionId })
            .sort({ createdAt: -1 })
            .limit(20)
            .lean()
          history.push(...msgs.reverse().map(m => ({ role: m.role, content: m.content })))
        } catch {  }
      }

      const unifiedCtx = buildUnifiedContext({
        message:       transcript.trim(),
        userId:        req.user?._id || 'anonymous',
        inputType:     'voice',
        rawTranscript: transcript,
        emotionData:   emotionContext,
        history,
      })

      const aiResult = await generateResponse(unifiedCtx)

      if (sessionId && req.user) {
        try {
          const session = await ChatSession.findOne({ _id: sessionId, userId: req.user._id })
          if (session) {
            await Message.create({ sessionId, role: 'user',      content: transcript.trim(), emotionContext })
            await Message.create({ sessionId, role: 'assistant', content: aiResult.content, tokens: aiResult.tokens, model: aiResult.model })
            session.messageCount += 2
            await session.save()
            await cacheDel(`ctx_history_${sessionId}`)
          }
        } catch (err) {
          logger.warn(`[VoiceController] Session save failed: ${err.message}`)
        }
      }

      let audioBase64 = null
      let ttsUsed     = false

      if (requestTTS && aiResult.content) {
        try {
          const ttsResult = await runTTS(aiResult.content)
          audioBase64 = ttsResult.audioBase64
          ttsUsed     = ttsResult.ttsUsed
        } catch (err) {
          logger.warn(`[VoiceController] TTS failed: ${err.message}`)
        }
      }

      const totalLatency = Date.now() - start
      logger.info(`[VoiceController] Pipeline complete — whisper: ${whisperUsed}, tts: ${ttsUsed}, ai: ${aiResult.provider}, total: ${totalLatency}ms`)

      res.json({
        transcript,
        aiText:      aiResult.content,
        audioBase64,
        whisperUsed,
        ttsUsed,
        provider:    aiResult.provider,
        isCrisis:    aiResult.isCrisis,
        latencyMs:   totalLatency,
      })

    } catch (err) {
      logger.error('[VoiceController] processVoiceMessage error:', err)
      res.status(500).json({ message: 'Voice processing failed' })
    }
  })
}

module.exports = { transcribe, textToSpeech, processVoiceMessage }
