import { create } from 'zustand'
import api from '../services/api'

export const useAuthStore = create((set, get) => ({
  user: null,
  token: null,
  isLoading: false,
  isInitialized: false,

  initAuth: () => {
    const token = localStorage.getItem('mindful_token')
    const user = localStorage.getItem('mindful_user')
    if (token && user) {
      set({ token, user: JSON.parse(user), isInitialized: true })
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      set({ isInitialized: true })
    }
  },

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const { data } = await api.post('/auth/login', { email, password })
      const { token, user } = data
      localStorage.setItem('mindful_token', token)
      localStorage.setItem('mindful_user', JSON.stringify(user))
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      set({ user, token, isLoading: false })
      return { success: true }
    } catch (err) {
      set({ isLoading: false })
      return { success: false, error: err.response?.data?.message || 'Login failed' }
    }
  },

  register: async (name, email, password) => {
    set({ isLoading: true })
    try {
      const { data } = await api.post('/auth/register', { name, email, password })
      const { token, user } = data
      localStorage.setItem('mindful_token', token)
      localStorage.setItem('mindful_user', JSON.stringify(user))
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      set({ user, token, isLoading: false })
      return { success: true }
    } catch (err) {
      set({ isLoading: false })
      return { success: false, error: err.response?.data?.message || 'Registration failed' }
    }
  },

  logout: () => {
    localStorage.removeItem('mindful_token')
    localStorage.removeItem('mindful_user')
    delete api.defaults.headers.common['Authorization']
    set({ user: null, token: null })
  },
}))
