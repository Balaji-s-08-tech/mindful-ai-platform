
const { ChatSession, Message } = require('../models/ChatSession')
const { generateResponse, generateResponseStream } = require('../services/aiService')
const { buildUnifiedContext } = require('../services/inputNormalizer')
const { cacheGet, cacheSet, cacheDel } = require('../config/redis')
const logger = require('../config/logger')

const CONTEXT_WINDOW = 20

async function loadContextHistory(sessionId, limit = CONTEXT_WINDOW) {
  const cacheKey = `ctx_history_${sessionId}`
  const cached   = await cacheGet(cacheKey)
  if (cached) return JSON.parse(cached)

  const messages = await Message.find({ sessionId })
    .sort({ createdAt: -1 })
    .limit(limit)
    .lean()

  const history = messages
    .reverse()
    .map(m => ({ role: m.role, content: m.content }))

  await cacheSet(cacheKey, JSON.stringify(history), 60) 
  return history
}

async function updateSessionMeta(session, emotionContext) {
  session.messageCount += 2  
  session.updatedAt = new Date()

  if (emotionContext?.combined) {
    if (!session.emotionSummary) session.emotionSummary = { dominant: null, progression: [] }
    session.emotionSummary.progression.push(emotionContext.combined)
    const freq = {}
    session.emotionSummary.progression.forEach(e => { freq[e] = (freq[e] || 0) + 1 })
    session.emotionSummary.dominant = Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0]
  }

  await session.save()
}

async function getSessions(req, res) {
  try {
    const sessions = await ChatSession.find({ userId: req.user._id, isActive: true })
      .sort({ updatedAt: -1 })
      .limit(50)
      .lean()
    res.json({ sessions })
  } catch (err) {
    logger.error('getSessions error:', err)
    res.status(500).json({ message: 'Failed to load sessions' })
  }
}

async function createSession(req, res) {
  try {
    const session = await ChatSession.create({
      userId: req.user._id,
      title:  'New Conversation',
    })
    res.status(201).json({ session })
  } catch (err) {
    logger.error('createSession error:', err)
    res.status(500).json({ message: 'Failed to create session' })
  }
}

async function getMessages(req, res) {
  try {
    const { sessionId } = req.params
    const session = await ChatSession.findOne({ _id: sessionId, userId: req.user._id })
    if (!session) return res.status(404).json({ message: 'Session not found' })

    const messages = await Message.find({ sessionId })
      .sort({ createdAt: 1 })
      .limit(100)
      .lean()

    res.json({ messages })
  } catch (err) {
    logger.error('getMessages error:', err)
    res.status(500).json({ message: 'Failed to load messages' })
  }
}

async function sendMessage(req, res) {
  try {
    const { sessionId }    = req.params
    const { content, emotionContext } = req.body

    if (!content?.trim()) {
      return res.status(400).json({ message: 'Message content is required' })
    }

    const session = await ChatSession.findOne({ _id: sessionId, userId: req.user._id })
    if (!session) return res.status(404).json({ message: 'Session not found' })

    const userMessage = await Message.create({
      sessionId,
      role:         'user',
      content:      content.trim(),
      emotionContext,
    })

    if (session.messageCount === 0) session.generateTitle(content)

    const history       = await loadContextHistory(sessionId)
    const unifiedCtx    = buildUnifiedContext({
      message:      content.trim(),
      userId:       req.user._id,
      inputType:    'text',
      emotionData:  emotionContext || {},
      history,
    })

    const aiResult = await generateResponse(unifiedCtx)

    const aiMessage = await Message.create({
      sessionId,
      role:    'assistant',
      content: aiResult.content,
      tokens:  aiResult.tokens,
      model:   aiResult.model,
    })

    await updateSessionMeta(session, emotionContext)

    await cacheDel(`ctx_history_${sessionId}`)

    logger.info(`[ChatController] Message processed — session: ${sessionId}, provider: ${aiResult.provider}, latency: ${aiResult.latencyMs}ms`)

    res.json({ userMessage, aiMessage, meta: { provider: aiResult.provider, latencyMs: aiResult.latencyMs } })
  } catch (err) {
    logger.error('sendMessage error:', err)
    res.status(500).json({ message: 'Failed to process message' })
  }
}

async function streamMessage(req, res) {
  const { sessionId }              = req.params
  const { content, emotionContext } = req.body

  if (!content?.trim()) {
    return res.status(400).json({ message: 'Message content is required' })
  }

  const session = await ChatSession.findOne({ _id: sessionId, userId: req.user._id })
  if (!session) return res.status(404).json({ message: 'Session not found' })

  res.setHeader('Content-Type',  'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection',    'keep-alive')
  res.setHeader('X-Accel-Buffering', 'no')  
  res.flushHeaders()

  const sendEvent = (data) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`)
    if (res.flush) res.flush()  
  }

  try {
    
    const userMessage = await Message.create({
      sessionId,
      role:         'user',
      content:      content.trim(),
      emotionContext,
    })

    if (session.messageCount === 0) session.generateTitle(content)
    sendEvent({ type: 'user_saved', userMessage })

    const history    = await loadContextHistory(sessionId)
    const unifiedCtx = buildUnifiedContext({
      message:     content.trim(),
      userId:      req.user._id,
      inputType:   'text',
      emotionData: emotionContext || {},
      history,
    })

    let fullContent = ''
    const aiResult  = await generateResponseStream(
      unifiedCtx,
      
      (token) => {
        fullContent += token
        sendEvent({ type: 'token', token })
      },
      
      (crisisText) => {
        sendEvent({ type: 'crisis', content: crisisText })
      }
    )

    const aiMessage = await Message.create({
      sessionId,
      role:    'assistant',
      content: aiResult.content || fullContent,
      tokens:  aiResult.tokens,
      model:   aiResult.model,
    })

    await updateSessionMeta(session, emotionContext)
    await cacheDel(`ctx_history_${sessionId}`)

    logger.info(`[ChatController] Stream complete — provider: ${aiResult.provider}, latency: ${aiResult.latencyMs}ms`)

    sendEvent({
      type:      'done',
      aiMessage,
      meta: { provider: aiResult.provider, latencyMs: aiResult.latencyMs, isCrisis: aiResult.isCrisis },
    })

    res.end()
  } catch (err) {
    logger.error('[ChatController] Stream error:', err)
    sendEvent({ type: 'error', message: 'An error occurred while generating your response.' })
    res.end()
  }
}

async function deleteSession(req, res) {
  try {
    const { sessionId } = req.params
    await ChatSession.findOneAndUpdate(
      { _id: sessionId, userId: req.user._id },
      { isActive: false }
    )
    await cacheDel(`ctx_history_${sessionId}`)
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ message: 'Failed to delete session' })
  }
}

module.exports = { getSessions, createSession, getMessages, sendMessage, streamMessage, deleteSession }
