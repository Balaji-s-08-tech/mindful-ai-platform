
const Anthropic  = require('@anthropic-ai/sdk')
const logger     = require('../config/logger')
const gemma      = require('./gemmaService')
const { buildPromptPackage, getCrisisResponse } = require('./promptBuilder')

let _anthropic = null
function getClaudeClient() {
  if (!_anthropic) {
    if (!process.env.ANTHROPIC_API_KEY) {
      throw new Error('ANTHROPIC_API_KEY is not set — configure it in .env')
    }
    _anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
  }
  return _anthropic
}

const CLAUDE_MODEL    = process.env.CLAUDE_MODEL    || 'claude-sonnet-4-20250514'
const LLM_PRIMARY     = process.env.LLM_PRIMARY     || 'gemma'   
const MAX_TOKENS      = parseInt(process.env.AI_MAX_TOKENS || '1024', 10)
const TEMPERATURE     = parseFloat(process.env.AI_TEMPERATURE || '0.7')

const FALLBACK_RESPONSE = "I'm having a moment of difficulty processing your message. I'm still here with you — please try again in a moment, or share what's on your mind in a different way."

async function generateResponse(unifiedContext) {
  const start = Date.now()

  const pkg = buildPromptPackage(unifiedContext)

  if (pkg.isCrisis) {
    return {
      content:   pkg.crisisResponse,
      model:     'crisis-handler',
      tokens:    0,
      isCrisis:  true,
      provider:  'crisis-handler',
      latencyMs: Date.now() - start,
    }
  }

  const { systemPrompt, messages } = pkg

  if (LLM_PRIMARY === 'gemma') {
    const gemmaAvailable = await gemma.isAvailable()
    if (gemmaAvailable) {
      try {
        const result = await gemma.generate(systemPrompt, messages, {
          temperature: TEMPERATURE,
          max_tokens:  MAX_TOKENS,
        })
        logger.info(`[AIService] Gemma response — ${result.tokens} tokens, ${Date.now() - start}ms`)
        return { ...result, isCrisis: false, provider: 'gemma', latencyMs: Date.now() - start }
      } catch (err) {
        logger.warn(`[AIService] Gemma failed: ${err.message} — falling back to Claude`)
      }
    } else {
      logger.info('[AIService] Gemma unavailable — routing to Claude')
    }
  }

  return generateClaude(systemPrompt, messages, start)
}

async function generateClaude(systemPrompt, messages, startTime = Date.now()) {
  try {
    const client   = getClaudeClient()
    const response = await client.messages.create({
      model:      CLAUDE_MODEL,
      max_tokens: MAX_TOKENS,
      system:     systemPrompt,
      messages,
    })

    const content  = response.content[0]?.text || ''
    const tokens   = (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0)

    logger.info(`[AIService] Claude response — model: ${response.model}, tokens: ${tokens}, ${Date.now() - startTime}ms`)

    return {
      content,
      model:     response.model,
      tokens,
      isCrisis:  false,
      provider:  'claude',
      latencyMs: Date.now() - startTime,
    }
  } catch (err) {
    logger.error(`[AIService] Claude failed: ${err.message}`)
    return {
      content:   FALLBACK_RESPONSE,
      model:     'fallback',
      tokens:    0,
      isCrisis:  false,
      provider:  'fallback',
      latencyMs: Date.now() - startTime,
    }
  }
}

async function generateResponseStream(unifiedContext, onToken, onCrisis) {
  const start = Date.now()
  const pkg   = buildPromptPackage(unifiedContext)

  if (pkg.isCrisis) {
    if (onCrisis) onCrisis(pkg.crisisResponse)
    return {
      content:   pkg.crisisResponse,
      model:     'crisis-handler',
      tokens:    0,
      isCrisis:  true,
      provider:  'crisis-handler',
      latencyMs: Date.now() - start,
    }
  }

  const { systemPrompt, messages } = pkg

  if (LLM_PRIMARY === 'gemma') {
    const gemmaAvailable = await gemma.isAvailable()
    if (gemmaAvailable) {
      try {
        const result = await gemma.generateStream(systemPrompt, messages, onToken, {
          temperature: TEMPERATURE,
          max_tokens:  MAX_TOKENS,
        })
        return { ...result, isCrisis: false, provider: 'gemma', latencyMs: Date.now() - start }
      } catch (err) {
        logger.warn(`[AIService] Gemma stream failed: ${err.message} — falling back to Claude stream`)
      }
    }
  }

  return generateClaudeStream(systemPrompt, messages, onToken, start)
}

async function generateClaudeStream(systemPrompt, messages, onToken, startTime = Date.now()) {
  try {
    const client = getClaudeClient()
    let fullContent = ''
    let totalTokens = 0

    const stream = await client.messages.stream({
      model:      CLAUDE_MODEL,
      max_tokens: MAX_TOKENS,
      system:     systemPrompt,
      messages,
    })

    for await (const event of stream) {
      if (event.type === 'content_block_delta' && event.delta?.type === 'text_delta') {
        const token = event.delta.text || ''
        fullContent += token
        if (token) onToken(token)
      }
    }

    const finalMsg = await stream.finalMessage()
    totalTokens = (finalMsg.usage?.input_tokens || 0) + (finalMsg.usage?.output_tokens || 0)

    logger.info(`[AIService] Claude stream done — model: ${finalMsg.model}, tokens: ${totalTokens}, ${Date.now() - startTime}ms`)

    return {
      content:   fullContent,
      model:     finalMsg.model,
      tokens:    totalTokens,
      isCrisis:  false,
      provider:  'claude',
      latencyMs: Date.now() - startTime,
    }
  } catch (err) {
    logger.error(`[AIService] Claude stream failed: ${err.message}`)
    
    onToken(FALLBACK_RESPONSE)
    return {
      content:   FALLBACK_RESPONSE,
      model:     'fallback',
      tokens:    0,
      isCrisis:  false,
      provider:  'fallback',
      latencyMs: Date.now() - startTime,
    }
  }
}

async function getStatus() {
  const gemmaUp = await gemma.isAvailable()
  const claudeConfigured = !!process.env.ANTHROPIC_API_KEY

  return {
    primary:          LLM_PRIMARY,
    gemma: {
      available:      gemmaUp,
      model:          process.env.GEMMA_MODEL || 'gemma3:4b',
      endpoint:       process.env.GEMMA_SERVICE_URL || 'http://localhost:11434',
    },
    claude: {
      configured:     claudeConfigured,
      model:          CLAUDE_MODEL,
    },
    streamEnabled:    process.env.STREAM_ENABLED !== 'false',
  }
}

module.exports = {
  generateResponse,
  generateResponseStream,
  getStatus,
}
