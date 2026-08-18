import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { Eye, EyeOff, Sparkles } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register, isLoading } = useAuthStore()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    const result = await register(name, email, password)
    if (result.success) {
      toast.success('Welcome to MindfulAI 💙')
      navigate('/dashboard')
    } else {
      toast.error(result.error)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink-950 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-sage-500/8 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/3 left-1/4 w-80 h-80 bg-ink-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
        className="w-full max-w-md mx-4"
      >
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-sage-500/15 border border-sage-500/30 mb-4 glow-sage">
            <Sparkles className="w-7 h-7 text-sage-400" />
          </div>
          <h1 className="font-display text-3xl text-ink-50 mb-2">MindfulAI</h1>
          <p className="text-ink-400 text-sm">Begin your journey to emotional wellness</p>
        </div>

        <div className="glass rounded-2xl p-8">
          <h2 className="font-display text-xl text-ink-100 mb-6">Create account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-ink-400 text-xs font-medium mb-2 tracking-wide uppercase">
                Your name
              </label>
              <input
                type="text"
                className="input-base"
                placeholder="Alex"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-ink-400 text-xs font-medium mb-2 tracking-wide uppercase">
                Email address
              </label>
              <input
                type="email"
                className="input-base"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-ink-400 text-xs font-medium mb-2 tracking-wide uppercase">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  className="input-base pr-10"
                  placeholder="Minimum 8 characters"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-500 hover:text-ink-300 transition-colors"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full mt-2 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account…
                </>
              ) : 'Create account'}
            </button>
          </form>

          <p className="text-center text-ink-500 text-sm mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-sage-400 hover:text-sage-300 transition-colors">
              Sign in
            </Link>
          </p>
        </div>

        <p className="text-center text-ink-600 text-xs mt-6 px-4 leading-relaxed">
          MindfulAI is not a substitute for professional mental health care.
          In a crisis, please contact emergency services or a mental health professional.
        </p>
      </motion.div>
    </div>
  )
}
