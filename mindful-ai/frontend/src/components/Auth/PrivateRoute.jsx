import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export default function PrivateRoute({ children }) {
  const { token, isInitialized } = useAuthStore()

  if (!isInitialized) {
    
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-950">
        <div className="flex gap-2">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-sage-400 thinking-dot"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      </div>
    )
  }

  return token ? children : <Navigate to="/login" replace />
}
