import { create } from 'zustand'
import api from '../services/api'

export const useChatStore = create((set, get) => ({
  messages:         [],
  sessions:         [],
  currentSessionId: null,
  isLoading:        false,
  isThinking:       false,
  inputMode:        'text',           
  streamingMessage: null,             
  lastProvider:     null,             

  setInputMode: (mode) => set({ inputMode: mode }),

  loadSessions: async () => {
    try {
      const { data } = await api.get('/chat/sessions')
      set({ sessions: data.sessions })
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  },

  createSession: async () => {
    try {
      const { data } = await api.post('/chat/sessions')
      set(state => ({
        sessions:         [data.session, ...state.sessions],
        currentSessionId: data.session._id,
        messages:         [],
        streamingMessage: null,
      }))
      return data.session._id
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  },

  loadMessages: async (sessionId) => {
    set({ isLoading: true, streamingMessage: null })
    try {
      const { data } = await api.get(`/chat/sessions/${sessionId}/messages`)
      set({ messages: data.messages, currentSessionId: sessionId, isLoading: false })
    } catch (err) {
      set({ isLoading: false })
      console.error('Failed to load messages:', err)
    }
  },

  sendMessage: async (content, emotionContext = null) => {
    const { currentSessionId } = get()
    if (!currentSessionId) return

    const userMsg = {
      _id: `temp_${Date.now()}`,
      role: 'user',
      content,
      emotionContext,
      createdAt: new Date().toISOString(),
    }
    set(state => ({ messages: [...state.messages, userMsg], isThinking: true }))

    try {
      const { data } = await api.post(
        `/chat/sessions/${currentSessionId}/messages`,
        { content, emotionContext }
      )
      set(state => ({
        messages: [
          ...state.messages.filter(m => m._id !== userMsg._id),
          data.userMessage,
          data.aiMessage,
        ],
        isThinking:   false,
        lastProvider: data.meta?.provider || null,
      }))
      return data.aiMessage
    } catch (err) {
      set(state => ({
        messages:   state.messages.filter(m => m._id !== userMsg._id),
        isThinking: false,
      }))
      throw err
    }
  },

  sendMessageStream: async (content, emotionContext = null) => {
    const { currentSessionId } = get()
    if (!currentSessionId) return

    const token = localStorage.getItem('token')

    const userMsg = {
      _id: `temp_${Date.now()}`,
      role: 'user',
      content,
      emotionContext,
      createdAt: new Date().toISOString(),
    }
    set(state => ({
      messages:         [...state.messages, userMsg],
      isThinking:       true,
      streamingMessage: { content: '' },
    }))

    try {
      const response = await fetch(
        `/api/chat/sessions/${currentSessionId}/messages/stream`,
        {
          method:  'POST',
          headers: {
            'Content-Type':  'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ content, emotionContext }),
        }
      )

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader  = response.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ''

      let userMsgReplaced = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() 

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))

            if (event.type === 'user_saved' && !userMsgReplaced) {
              set(state => ({
                messages: [
                  ...state.messages.filter(m => m._id !== userMsg._id),
                  event.userMessage,
                ],
              }))
              userMsgReplaced = true
            }

            if (event.type === 'token') {
              set(state => ({
                isThinking:       false,
                streamingMessage: {
                  content: (state.streamingMessage?.content || '') + event.token,
                },
              }))
            }

            if (event.type === 'done') {
              set(state => ({
                messages: [...state.messages, event.aiMessage],
                streamingMessage: null,
                lastProvider:     event.meta?.provider || null,
              }))
            }

            if (event.type === 'error') {
              set({ streamingMessage: null, isThinking: false })
              throw new Error(event.message)
            }
          } catch {  }
        }
      }
    } catch (err) {
      set(state => ({
        messages:         state.messages.filter(m => m._id !== userMsg._id),
        isThinking:       false,
        streamingMessage: null,
      }))
      throw err
    }
  },

  sendVoiceMessage: async (audioBlob, emotionContext = null) => {
    const { currentSessionId } = get()
    if (!currentSessionId || !audioBlob) return

    set({ isThinking: true, streamingMessage: { content: '' } })

    try {
      const formData = new FormData()
      formData.append('audio',          audioBlob, 'recording.webm')
      formData.append('sessionId',      currentSessionId)
      formData.append('emotionContext', JSON.stringify(emotionContext || {}))
      formData.append('requestTTS',     'true')

      const token    = localStorage.getItem('token')
      const response = await fetch('/api/voice/process', {
        method:  'POST',
        headers: { Authorization: `Bearer ${token}` },
        body:    formData,
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()

      const transcriptMsg = {
        _id:       `voice_${Date.now()}`,
        role:      'user',
        content:   data.transcript,
        inputType: 'voice',
        emotionContext,
        createdAt: new Date().toISOString(),
      }
      const aiMsg = {
        _id:      `ai_${Date.now()}`,
        role:     'assistant',
        content:  data.aiText,
        createdAt: new Date().toISOString(),
      }

      set(state => ({
        messages: [...state.messages, transcriptMsg, aiMsg],
        isThinking:       false,
        streamingMessage: null,
        lastProvider:     data.provider || null,
      }))

      return data  
    } catch (err) {
      set({ isThinking: false, streamingMessage: null })
      throw err
    }
  },

  onSocketUserSaved: (userMessage) => {
    set(state => ({ messages: [...state.messages, userMessage] }))
  },

  onSocketToken: (token) => {
    set(state => ({
      isThinking:       false,
      streamingMessage: {
        content: (state.streamingMessage?.content || '') + token,
      },
    }))
  },

  onSocketMessageEnd: (aiMessage, meta) => {
    set(state => ({
      messages:         [...state.messages, aiMessage],
      streamingMessage: null,
      lastProvider:     meta?.provider || null,
    }))
  },

  addMessage: (message) => {
    set(state => ({ messages: [...state.messages, message] }))
  },

  clearChat: () => set({ messages: [], currentSessionId: null, streamingMessage: null }),

  deleteSession: async (sessionId) => {
    try {
      await api.delete(`/chat/sessions/${sessionId}`)
      set(state => ({
        sessions: state.sessions.filter(s => s._id !== sessionId),
        ...(state.currentSessionId === sessionId
          ? { currentSessionId: null, messages: [] }
          : {}),
      }))
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  },
}))
