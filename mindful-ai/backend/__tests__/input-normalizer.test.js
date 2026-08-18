
const {
  buildUnifiedContext,
  fuseEmotions,
  normalizeEmotionLabel,
  validateContext,
} = require('../src/services/inputNormalizer')

describe('normalizeEmotionLabel', () => {
  test('maps exact valid labels', () => {
    expect(normalizeEmotionLabel('happy')).toBe('happy')
    expect(normalizeEmotionLabel('sad')).toBe('sad')
    expect(normalizeEmotionLabel('angry')).toBe('angry')
    expect(normalizeEmotionLabel('neutral')).toBe('neutral')
  })

  test('maps aliases to normalized labels', () => {
    expect(normalizeEmotionLabel('fear')).toBe('fearful')
    expect(normalizeEmotionLabel('scared')).toBe('fearful')
    expect(normalizeEmotionLabel('surprise')).toBe('surprised')
    expect(normalizeEmotionLabel('calm')).toBe('neutral')
    expect(normalizeEmotionLabel('unknown')).toBe('neutral')
  })

  test('handles case-insensitive input', () => {
    expect(normalizeEmotionLabel('SAD')).toBe('sad')
    expect(normalizeEmotionLabel('Happy')).toBe('happy')
    expect(normalizeEmotionLabel('ANGRY')).toBe('angry')
  })

  test('returns neutral for null/undefined/empty', () => {
    expect(normalizeEmotionLabel(null)).toBeNull()
    expect(normalizeEmotionLabel(undefined)).toBeNull()
    expect(normalizeEmotionLabel('')).toBeNull()
  })
})

describe('fuseEmotions', () => {
  test('returns neutral with 0.5 confidence for empty signals', () => {
    const result = fuseEmotions({})
    expect(result.emotion).toBe('neutral')
    expect(result.confidence).toBe(0.5)
  })

  test('uses highest-weight signal when all agree', () => {
    const result = fuseEmotions({ facial: 'sad', voice: 'sad', text: 'sad' })
    expect(result.emotion).toBe('sad')
    expect(result.confidence).toBeGreaterThan(0.9)
  })

  test('facial emotion wins when signals conflict', () => {

    const result = fuseEmotions({ facial: 'angry', voice: 'sad', text: 'happy' })
    expect(result.emotion).toBe('angry')
  })

  test('handles partial signals (facial + voice only)', () => {
    const result = fuseEmotions({ facial: 'fearful', voice: 'fearful' })
    expect(result.emotion).toBe('fearful')
    expect(result.confidence).toBeGreaterThan(0.7)
  })

  test('normalizes alias labels before fusing', () => {
    const result = fuseEmotions({ facial: 'fear', voice: 'fearful' })
    expect(result.emotion).toBe('fearful')
  })
})

describe('buildUnifiedContext', () => {
  const BASE = {
    message:   'Hello, I need some support.',
    userId:    'user_abc123',
    inputType: 'text',
  }

  test('builds a valid UnifiedContext with minimal inputs', () => {
    const ctx = buildUnifiedContext(BASE)
    expect(ctx.message).toBe('Hello, I need some support.')
    expect(ctx.input_type).toBe('text')
    expect(ctx.user_id).toBe('user_abc123')
    expect(ctx.emotion).toBe('neutral')
    expect(ctx.confidence).toBe(0.5)
    expect(ctx.timestamp).toBeTruthy()
    expect(Array.isArray(ctx.history)).toBe(true)
  })

  test('Scenario 1 — sad user + text input', () => {
    const ctx = buildUnifiedContext({
      ...BASE,
      message:     'I feel so hopeless and empty inside.',
      inputType:   'text',
      emotionData: { combined: 'sad', facial: 'sad', facialConfidence: 0.85 },
    })

    expect(ctx.emotion).toBe('sad')
    expect(ctx.confidence).toBe(0.85)
    expect(ctx.emotionContext.combined).toBe('sad')
    expect(ctx.input_type).toBe('text')
    expect(ctx.meta.audioProcessed).toBe(false)
  })

  test('Scenario 2 — angry user + voice input', () => {
    const ctx = buildUnifiedContext({
      ...BASE,
      message:       'This is so frustrating! Nothing ever works!',
      inputType:     'voice',
      rawTranscript: 'This is so frustrating! Nothing ever works!',
      emotionData:   { combined: 'angry', facial: 'angry', voice: 'angry', facialConfidence: 0.72 },
    })

    expect(ctx.emotion).toBe('angry')
    expect(ctx.input_type).toBe('voice')
    expect(ctx.meta.audioProcessed).toBe(true)
    expect(ctx.meta.rawTranscript).toBe('This is so frustrating! Nothing ever works!')
  })

  test('Scenario 3 — neutral user + no emotion data', () => {
    const ctx = buildUnifiedContext({
      ...BASE,
      message:     'Can you help me with something today?',
      inputType:   'text',
      emotionData: {},
    })

    expect(ctx.emotion).toBe('neutral')
    expect(ctx.confidence).toBe(0.5)
    expect(ctx.emotionContext.facial).toBeNull()
    expect(ctx.emotionContext.voice).toBeNull()
    expect(ctx.emotionContext.text).toBeNull()
  })

  test('trims and caps overly long messages', () => {
    const longMsg = 'a'.repeat(10000)
    const ctx     = buildUnifiedContext({ ...BASE, message: longMsg })
    expect(ctx.message.length).toBeLessThanOrEqual(8000)
  })

  test('throws on empty message', () => {
    expect(() => buildUnifiedContext({ ...BASE, message: '   ' })).toThrow()
  })

  test('normalizes history messages', () => {
    const history = [
      { role: 'user',      content: 'First message' },
      { role: 'assistant', content: 'First response' },
      { role: 'user',      content: 'Second message' },
    ]
    const ctx = buildUnifiedContext({ ...BASE, history })
    expect(ctx.history).toHaveLength(3)
    expect(ctx.history[1].role).toBe('assistant')
  })
})

describe('validateContext', () => {
  const validCtx = {
    message:       'Test message',
    emotion:       'neutral',
    confidence:    0.5,
    input_type:    'text',
    timestamp:     new Date().toISOString(),
    user_id:       'test_user',
    emotionContext: {},
    history:        [],
    meta:           {},
  }

  test('passes for a valid context', () => {
    expect(() => validateContext(validCtx)).not.toThrow()
  })

  test('throws for missing required field', () => {
    const { emotion, ...missing } = validCtx
    expect(() => validateContext(missing)).toThrow(/emotion/)
  })

  test('throws for invalid input_type', () => {
    expect(() => validateContext({ ...validCtx, input_type: 'keyboard' })).toThrow(/input_type/)
  })

  test('throws for out-of-range confidence', () => {
    expect(() => validateContext({ ...validCtx, confidence: 1.5 })).toThrow(/Confidence/)
  })
})
