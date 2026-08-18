import { create } from 'zustand'

export const useEmotionStore = create((set, get) => ({
  
  facialEmotion: null,
  voiceTone: null,
  textSentiment: null,

  emotionHistory: [],

  combinedEmotion: null,

  isDetecting: false,
  cameraActive: false,
  micActive: false,

  suggestions: [],

  setCameraActive: (val) => set({ cameraActive: val }),
  setMicActive: (val) => set({ micActive: val }),
  setIsDetecting: (val) => set({ isDetecting: val }),

  updateFacialEmotion: (emotion) => {
    set(state => {
      const history = [...state.emotionHistory, { type: 'facial', emotion, time: Date.now() }]
        .slice(-20)
      const combined = computeCombinedEmotion({
        facial: emotion,
        voice: state.voiceTone,
        text: state.textSentiment,
      })
      return {
        facialEmotion: emotion,
        emotionHistory: history,
        combinedEmotion: combined,
        suggestions: generateSuggestions(combined),
      }
    })
  },

  updateVoiceTone: (tone) => {
    set(state => {
      const combined = computeCombinedEmotion({
        facial: state.facialEmotion,
        voice: tone,
        text: state.textSentiment,
      })
      return {
        voiceTone: tone,
        combinedEmotion: combined,
        suggestions: generateSuggestions(combined),
      }
    })
  },

  updateTextSentiment: (sentiment) => {
    set(state => {
      const combined = computeCombinedEmotion({
        facial: state.facialEmotion,
        voice: state.voiceTone,
        text: sentiment,
      })
      return {
        textSentiment: sentiment,
        combinedEmotion: combined,
        suggestions: generateSuggestions(combined),
      }
    })
  },

  reset: () => set({
    facialEmotion: null,
    voiceTone: null,
    textSentiment: null,
    combinedEmotion: null,
    suggestions: [],
  }),
}))

function computeCombinedEmotion({ facial, voice, text }) {
  const signals = [facial, voice, text].filter(Boolean)
  if (signals.length === 0) return null

  const weights = { facial: 0.5, voice: 0.3, text: 0.2 }
  const emotionScores = {}

  if (facial) emotionScores[facial] = (emotionScores[facial] || 0) + weights.facial
  if (voice) emotionScores[voice] = (emotionScores[voice] || 0) + weights.voice
  if (text) emotionScores[text] = (emotionScores[text] || 0) + weights.text

  const dominant = Object.entries(emotionScores).sort((a, b) => b[1] - a[1])[0]
  return dominant ? dominant[0] : 'neutral'
}

function generateSuggestions(emotion) {
  const suggestionMap = {
    sad: [
      { icon: '🫁', text: 'Try box breathing — inhale 4s, hold 4s, exhale 4s', type: 'breathing' },
      { icon: '📓', text: 'Write down three things you appreciate today', type: 'journal' },
      { icon: '🎵', text: 'Listen to calming music for 5 minutes', type: 'activity' },
    ],
    angry: [
      { icon: '🫁', text: '4-7-8 breathing — inhale 4s, hold 7s, exhale 8s', type: 'breathing' },
      { icon: '🚶', text: 'Take a 5-minute walk to reset', type: 'movement' },
      { icon: '💧', text: 'Drink a glass of cold water slowly', type: 'activity' },
    ],
    fearful: [
      { icon: '🌱', text: 'Ground yourself — name 5 things you can see', type: 'grounding' },
      { icon: '🫁', text: 'Slow diaphragmatic breathing to calm your nervous system', type: 'breathing' },
      { icon: '📞', text: 'Consider reaching out to someone you trust', type: 'social' },
    ],
    stressed: [
      { icon: '⏸️', text: 'Take a 10-minute break from screens', type: 'break' },
      { icon: '🫁', text: 'Progressive muscle relaxation — tense and release each muscle', type: 'breathing' },
      { icon: '📝', text: 'Write your worries down — it reduces mental load', type: 'journal' },
    ],
    happy: [
      { icon: '✨', text: 'Capture this feeling — write what\'s making you smile', type: 'journal' },
      { icon: '💌', text: 'Share your positivity with someone you care about', type: 'social' },
    ],
    surprised: [
      { icon: '🫁', text: 'Take a few deep breaths to center yourself', type: 'breathing' },
    ],
    neutral: [
      { icon: '🧘', text: 'A good time for mindful reflection or journaling', type: 'mindfulness' },
    ],
  }
  return suggestionMap[emotion] || suggestionMap.neutral
}
