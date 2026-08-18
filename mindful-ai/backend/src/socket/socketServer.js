
const { Server }    = require('socket.io')
const jwt           = require('jsonwebtoken')
const User          = require('../models/User')
const { ChatSession, Message } = require('../models/ChatSession')
const { buildUnifiedContext } = require('../services/inputNormalizer')
const { generateResponseStream } = require('../services/aiService')
const { cacheGet, cacheDel } = require('../config/redis')
const axios         = require('axios')
const logger        = require('../config/logger')

const CONTEXT_WINDOW = 20

async function loadHistory(sessionId) {
  const messages = await Message.find({ sessionId })
    .sort({ createdAt: -1 })
    .limit(CONTEXT_WINDOW)
    .lean()
  return messages.reverse().map(m => ({ role: m.role, content: m.content }))
}

async function fetchTTS(text) {
  try {
    const ELEVENLABS_KEY  = process.env.ELEVENLABS_API_KEY
    const ELEVENLABS_VOICE = process.env.ELEVENLABS_VOICE_ID || 'EXAVITQu4vr4xnSDxMaL'

    if (!ELEVENLABS_KEY) return null

    const response = await axios.post(
      `https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE}`,
      {
        text: text.slice(0, 2000),
        model_id: 'eleven_turbo_v2',
        voice_settings: { stability: 0.75, similarity_boost: 0.85, style: 0.3, use_speaker_boost: true },
      },
      {
        headers: {
          'xi-api-key': ELEVENLABS_KEY,
          'Content-Type': 'application/json',
          Accept: 'audio/mpeg',
        },
        responseType: 'arraybuffer',
        timeout: 15000,
      }
    )
    return Buffer.from(response.data).toString('base64')
  } catch (err) {
    logger.warn(`[SocketServer] TTS failed: ${err.message}`)
    return null
  }
}

function initSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: {
      origin:      process.env.FRONTEND_URL || 'http://localhost:3000',
      credentials: true,
    },
    pingTimeout:  60000,
    pingInterval: 25000,
  })

  io.use(async (socket, next) => {
    try {
      const token = socket.handshake.auth?.token
      if (!token) return next(new Error('Authentication required'))

      const decoded = jwt.verify(token, process.env.JWT_SECRET)
      const user    = await User.findById(decoded.userId).select('_id name email')
      if (!user) return next(new Error('User not found'))

      socket.user = user
      next()
    } catch {
      next(new Error('Invalid token'))
    }
  })

  io.on('connection', (socket) => {
    logger.info(`Socket connected: ${socket.user.name} (${socket.id})`)

    socket.join(`user:${socket.user._id}`)

    socket.on('join_session', (sessionId) => {
      socket.join(`session:${sessionId}`)
      logger.debug(`  ↳ ${socket.user.name} joined session: ${sessionId}`)
    })

    socket.on('leave_session', (sessionId) => {
      socket.leave(`session:${sessionId}`)
    })

    socket.on('typing_start', ({ sessionId }) => {
      socket.to(`session:${sessionId}`).emit('user_typing', {
        userId: socket.user._id,
        name:   socket.user.name,
      })
    })

    socket.on('typing_stop', ({ sessionId }) => {
      socket.to(`session:${sessionId}`).emit('user_stopped_typing', {
        userId: socket.user._id,
      })
    })

    socket.on('emotion_detected', (data) => {
      io.to(`user:${socket.user._id}`).emit('emotion_update', {
        ...data,
        timestamp: Date.now(),
      })
    })

    socket.on('ai_stream_request', async ({ sessionId, content, emotionContext }) => {
      if (!sessionId || !content?.trim()) return

      try {
        
        const session = await ChatSession.findOne({ _id: sessionId, userId: socket.user._id })
        if (!session) {
          return socket.emit('ai_stream_error', { sessionId, message: 'Session not found' })
        }

        const userMessage = await Message.create({
          sessionId,
          role:         'user',
          content:      content.trim(),
          emotionContext,
        })

        if (session.messageCount === 0) session.generateTitle(content)

        socket.emit('ai_message_start', { sessionId, userMessage })

        const history    = await loadHistory(sessionId)
        const unifiedCtx = buildUnifiedContext({
          message:     content.trim(),
          userId:      socket.user._id,
          inputType:   'text',
          emotionData: emotionContext || {},
          history,
        })

        let fullContent = ''
        const aiResult  = await generateResponseStream(
          unifiedCtx,
          (token) => {
            fullContent += token
            socket.emit('ai_token', { sessionId, token })
          },
          (crisisText) => {
            socket.emit('ai_crisis', { sessionId, content: crisisText })
          }
        )

        const aiMessage = await Message.create({
          sessionId,
          role:    'assistant',
          content: aiResult.content || fullContent,
          tokens:  aiResult.tokens,
          model:   aiResult.model,
        })

        session.messageCount += 2
        session.updatedAt     = new Date()
        if (emotionContext?.combined) {
          if (!session.emotionSummary) session.emotionSummary = { dominant: null, progression: [] }
          session.emotionSummary.progression.push(emotionContext.combined)
        }
        await session.save()
        await cacheDel(`ctx_history_${sessionId}`)

        socket.emit('ai_message_end', {
          sessionId,
          aiMessage,
          meta: { provider: aiResult.provider, latencyMs: aiResult.latencyMs, isCrisis: aiResult.isCrisis },
        })

        logger.info(`[SocketServer] AI stream complete — ${aiResult.provider}, ${aiResult.latencyMs}ms`)
      } catch (err) {
        logger.error('[SocketServer] ai_stream_request error:', err)
        socket.emit('ai_stream_error', { sessionId, message: 'Failed to generate response' })
      }
    })

    socket.on('voice_to_ai', async ({ sessionId, transcript, emotionContext, requestTTS = true }) => {
      if (!sessionId || !transcript?.trim()) return

      try {
        const session = await ChatSession.findOne({ _id: sessionId, userId: socket.user._id })
        if (!session) return

        await Message.create({
          sessionId,
          role:         'user',
          content:      transcript.trim(),
          emotionContext,
        })

        socket.emit('ai_message_start', { sessionId, inputType: 'voice' })

        const history    = await loadHistory(sessionId)
        const unifiedCtx = buildUnifiedContext({
          message:       transcript.trim(),
          userId:        socket.user._id,
          inputType:     'voice',
          rawTranscript: transcript,
          emotionData:   emotionContext || {},
          history,
        })

        let fullContent = ''
        const aiResult  = await generateResponseStream(
          unifiedCtx,
          (token) => {
            fullContent += token
            
            socket.emit('ai_token', { sessionId, token })
          }
        )

        const responseText = aiResult.content || fullContent

        const aiMessage = await Message.create({
          sessionId,
          role:    'assistant',
          content: responseText,
          tokens:  aiResult.tokens,
          model:   aiResult.model,
        })

        session.messageCount += 2
        await session.save()
        await cacheDel(`ctx_history_${sessionId}`)

        socket.emit('ai_message_end', { sessionId, aiMessage, meta: { provider: aiResult.provider } })

        if (requestTTS && responseText) {
          const audioBase64 = await fetchTTS(responseText)
          socket.emit('ai_audio_response', {
            sessionId,
            text:        responseText,
            audioBase64,   
          })
        }

      } catch (err) {
        logger.error('[SocketServer] voice_to_ai error:', err)
        socket.emit('ai_stream_error', { sessionId, message: 'Voice processing failed' })
      }
    })

    socket.on('ping', () => {
      socket.emit('pong', { timestamp: Date.now() })
    })

    socket.on('disconnect', (reason) => {
      logger.info(`Socket disconnected: ${socket.user?.name} — ${reason}`)
    })
  })

  io.emitToUser    = (userId, event, data) => io.to(`user:${userId}`).emit(event, data)
  io.emitToSession = (sessionId, event, data) => io.to(`session:${sessionId}`).emit(event, data)

  logger.info('✅ WebSocket server initialized with AI streaming support')
  return io
}

module.exports = initSocket
