
const axios = require('axios')
const logger = require('../config/logger')

const OLLAMA_BASE  = process.env.GEMMA_SERVICE_URL || 'http://localhost:11434'
const OLLAMA_MODEL = process.env.GEMMA_MODEL || 'gemma3:4b'
const TIMEOUT_MS   = parseInt(process.env.GEMMA_TIMEOUT_MS || '30000', 10)

let _available = null   
let _lastCheck  = 0
const CACHE_TTL_MS = 30_000  

async function isAvailable() {
  const now = Date.now()
  if (_available !== null && now - _lastCheck < CACHE_TTL_MS) {
    return _available
  }

  try {
    const response = await axios.get(`${OLLAMA_BASE}/api/tags`, { timeout: 3000 })
    const models = response.data?.models || []
    const hasModel = models.some(m =>
      m.name === OLLAMA_MODEL ||
      m.name.startsWith(OLLAMA_MODEL.split(':')[0])
    )
    _available = hasModel
    _lastCheck  = now

    if (!hasModel) {
      logger.warn(`[GemmaService] Ollama running but model "${OLLAMA_MODEL}" not found. Pull with: ollama pull ${OLLAMA_MODEL}`)
    } else {
      logger.debug(`[GemmaService] ✅ Ollama available — model: ${OLLAMA_MODEL}`)
    }

    return _available
  } catch {
    _available = false
    _lastCheck  = now
    logger.debug('[GemmaService] Ollama not reachable — will use Claude fallback')
    return false
  }
}

function buildOllamaPrompt(systemPrompt, messages) {
  let prompt = `<start_of_turn>system\n${systemPrompt}<end_of_turn>\n`
  for (const msg of messages) {
    const role = msg.role === 'assistant' ? 'model' : 'user'
    prompt += `<start_of_turn>${role}\n${msg.content}<end_of_turn>\n`
  }
  prompt += '<start_of_turn>model\n'
  return prompt
}

async function generate(systemPrompt, messages, options = {}) {
  const { temperature = 0.7, max_tokens = 1024 } = options

  const prompt = buildOllamaPrompt(systemPrompt, messages)

  logger.debug(`[GemmaService] Sending request to Ollama — model: ${OLLAMA_MODEL}, tokens: ${max_tokens}`)

  const response = await axios.post(
    `${OLLAMA_BASE}/api/generate`,
    {
      model:  OLLAMA_MODEL,
      prompt,
      stream: false,
      options: {
        temperature,
        num_predict: max_tokens,
        stop: ['<end_of_turn>', '<start_of_turn>'],
      },
    },
    { timeout: TIMEOUT_MS }
  )

  const content = (response.data?.response || '').trim()
  const tokens  = response.data?.eval_count || 0

  logger.info(`[GemmaService] Response generated — ${tokens} tokens`)

  return {
    content,
    model:  `ollama/${OLLAMA_MODEL}`,
    tokens,
  }
}

async function generateStream(systemPrompt, messages, onToken, options = {}) {
  const { temperature = 0.7, max_tokens = 1024 } = options
  const prompt = buildOllamaPrompt(systemPrompt, messages)

  const response = await axios.post(
    `${OLLAMA_BASE}/api/generate`,
    {
      model:  OLLAMA_MODEL,
      prompt,
      stream: true,
      options: {
        temperature,
        num_predict: max_tokens,
        stop: ['<end_of_turn>', '<start_of_turn>'],
      },
    },
    {
      timeout:      TIMEOUT_MS,
      responseType: 'stream',
    }
  )

  return new Promise((resolve, reject) => {
    let fullContent = ''
    let tokenCount  = 0
    let buffer      = ''

    response.data.on('data', chunk => {
      buffer += chunk.toString()
      const lines = buffer.split('\n')
      buffer = lines.pop() 

      for (const line of lines) {
        if (!line.trim()) continue
        try {
          const parsed = JSON.parse(line)
          const token  = parsed.response || ''
          if (token) {
            fullContent += token
            tokenCount++
            onToken(token)
          }
          if (parsed.done) {
            resolve({
              content: fullContent.trim(),
              model:   `ollama/${OLLAMA_MODEL}`,
              tokens:  parsed.eval_count || tokenCount,
            })
          }
        } catch {
          
        }
      }
    })

    response.data.on('error', err => {
      logger.error('[GemmaService] Stream error:', err.message)
      reject(err)
    })

    response.data.on('end', () => {
      
      resolve({
        content: fullContent.trim(),
        model:   `ollama/${OLLAMA_MODEL}`,
        tokens:  tokenCount,
      })
    })
  })
}

function resetAvailabilityCache() {
  _available = null
  _lastCheck  = 0
}

module.exports = { isAvailable, generate, generateStream, resetAvailabilityCache }
