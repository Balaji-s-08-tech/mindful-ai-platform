import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('mindful_token')
      localStorage.removeItem('mindful_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
