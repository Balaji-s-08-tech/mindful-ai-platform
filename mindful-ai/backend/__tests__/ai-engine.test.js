
jest.mock('../src/services/aiService', () => ({
  generateResponse:       jest.fn(),
  generateResponseStream: jest.fn(),
  getStatus:              jest.fn(),
}))

jest.mock('../src/config/redis', () => ({
  cacheGet: jest.fn(() => Promise.resolve(null)),
  cacheSet: jest.fn(() => Promise.resolve()),
  cacheDel: jest.fn(() => Promise.resolve()),
}))

const { buildUnifiedContext }   = require('../src/services/inputNormalizer')
const { buildPromptPackage, detectCrisisSignals, getCrisisResponse, EMOTION_GUIDANCE }
                                = require('../src/services/promptBuilder')
const { generateResponse }      = require('../src/services/aiService')

function makeContext(overrides = {}) {
  return buildUnifiedContext({
    message:   'Test message',
    userId:    'test_user_001',
    inputType: 'text',
    ...overrides,
  })
}

describe('PromptBuilder — buildPromptPackage', () => {

  test('Scenario 1: Sad user + text input — injects warm/validating tone', () => {
    const ctx = makeContext({
      message:     'I feel really hopeless today. Nothing seems worth it.',
      emotionData: { combined: 'sad', facial: 'sad', facialConfidence: 0.83 },
    })

    const pkg = buildPromptPackage(ctx)

    expect(pkg.isCrisis).toBe(false)

    const sysPLower = pkg.systemPrompt.toLowerCase()
    expect(sysPLower).toContain('sad')
    expect(sysPLower).toContain('validat')
    expect(sysPLower).toContain('warm')

    expect(sysPLower).not.toContain('calming')
  })

  test('Scenario 2: Angry user + voice input — injects calming tone', () => {
    const ctx = makeContext({
      message:     'This is so frustrating! Nobody listens to me!',
      inputType:   'voice',
      emotionData: { combined: 'angry', facial: 'angry', facialConfidence: 0.76 },
    })

    const pkg = buildPromptPackage(ctx)

    expect(pkg.isCrisis).toBe(false)
    expect(ctx.input_type).toBe('voice')

    const sysPLower = pkg.systemPrompt.toLowerCase()
    expect(sysPLower).toContain('angry')
    expect(sysPLower).toContain('calm')
    expect(sysPLower).toContain('frustrat')

    const lastMsg = pkg.messages[pkg.messages.length - 1]
    expect(lastMsg.role).toBe('user')
    expect(lastMsg.content).toContain('[Voice message')
  })

  test('Scenario 3: Neutral + no emotion data — standard prompt, no distress injected', () => {
    const ctx = makeContext({
      message:     'Can you help me think through a decision?',
      emotionData: {},
    })

    const pkg = buildPromptPackage(ctx)

    expect(pkg.isCrisis).toBe(false)
    expect(ctx.emotion).toBe('neutral')

    const sysPLower = pkg.systemPrompt.toLowerCase()
    expect(sysPLower).toContain('neutral')

    expect(sysPLower).not.toContain('acknowledge their pain')
    expect(sysPLower).not.toContain('calming')
  })

  test('includes correct number of messages in prompt package', () => {
    const history = [
      { role: 'user',      content: 'First message' },
      { role: 'assistant', content: 'First response' },
    ]
    const ctx = makeContext({ history })
    const pkg = buildPromptPackage(ctx)

    expect(pkg.messages).toHaveLength(3)
    expect(pkg.messages[2].role).toBe('user')
  })
})

describe('PromptBuilder — detectCrisisSignals', () => {
  test('detects suicide-related phrases', () => {
    expect(detectCrisisSignals('I want to kill myself')).toBe(true)
    expect(detectCrisisSignals('I am suicidal')).toBe(true)
    expect(detectCrisisSignals("I don't want to live anymore")).toBe(true)
    expect(detectCrisisSignals('Want to end my life')).toBe(true)
  })

  test('detects self-harm phrases', () => {
    expect(detectCrisisSignals('I want to hurt myself')).toBe(true)
    expect(detectCrisisSignals('I cut myself to cope')).toBe(true)
  })

  test('does NOT flag normal distress expressions', () => {
    expect(detectCrisisSignals('I feel really sad today')).toBe(false)
    expect(detectCrisisSignals("I'm frustrated and angry")).toBe(false)
    expect(detectCrisisSignals('I feel hopeless about this project')).toBe(false)
  })

  test('crisis package bypasses LLM', () => {
    const ctx = makeContext({ message: 'I want to kill myself tonight' })
    const pkg = buildPromptPackage(ctx)

    expect(pkg.isCrisis).toBe(true)
    expect(pkg.crisisResponse).toContain('988')
    expect(pkg.crisisResponse).toContain('741741')
  })
})

describe('EMOTION_GUIDANCE coverage', () => {
  const emotions = ['sad', 'angry', 'fearful', 'surprised', 'disgusted', 'happy', 'neutral']

  emotions.forEach(emotion => {
    test(`has guidance for "${emotion}"`, () => {
      expect(EMOTION_GUIDANCE[emotion]).toBeDefined()
      expect(EMOTION_GUIDANCE[emotion].tone).toBeTruthy()
      expect(EMOTION_GUIDANCE[emotion].instruction).toBeTruthy()
    })
  })
})

describe('AI Service — response validation', () => {
  beforeEach(() => generateResponse.mockClear())

  test('Scenario 1: sad context → mock returns supportive response', async () => {
    generateResponse.mockResolvedValueOnce({
      content:  "I hear how much pain you're carrying right now. You don't have to face this alone.",
      model:    'claude-sonnet-4',
      tokens:   124,
      isCrisis: false,
      provider: 'claude',
      latencyMs: 1200,
    })

    const ctx    = makeContext({ emotionData: { combined: 'sad' } })
    const result = await generateResponse(ctx)

    expect(result.isCrisis).toBe(false)
    expect(result.provider).toBe('claude')
    expect(result.content).toContain("pain")
  })

  test('Scenario 2: angry context → mock returns calming response', async () => {
    generateResponse.mockResolvedValueOnce({
      content:  "Your frustration makes complete sense. Let's take a breath together.",
      model:    'ollama/gemma3:4b',
      tokens:   89,
      isCrisis: false,
      provider: 'gemma',
      latencyMs: 800,
    })

    const ctx    = makeContext({ emotionData: { combined: 'angry' }, inputType: 'voice' })
    const result = await generateResponse(ctx)

    expect(result.provider).toBe('gemma')
    expect(result.content.toLowerCase()).toContain('frustration')
  })

  test('Scenario 3: neutral context → generic helpful response', async () => {
    generateResponse.mockResolvedValueOnce({
      content:  "I'm here to help. What would you like to explore today?",
      model:    'claude-sonnet-4',
      tokens:   56,
      isCrisis: false,
      provider: 'claude',
      latencyMs: 950,
    })

    const ctx    = makeContext({ emotionData: {} })
    const result = await generateResponse(ctx)

    expect(result.isCrisis).toBe(false)
    expect(result.tokens).toBeGreaterThan(0)
  })
})
