require('dotenv').config()
const express = require('express')
const http = require('http')
const cors = require('cors')
const helmet = require('helmet')
const morgan = require('morgan')
const rateLimit = require('express-rate-limit')

const connectDB = require('./config/database')
const connectRedis = require('./config/redis')
const initSocket = require('./socket/socketServer')

const authRoutes = require('./routes/auth')
const chatRoutes = require('./routes/chat')
const voiceRoutes = require('./routes/voice')
const emotionRoutes = require('./routes/emotion')

const app = express()
const server = http.createServer(app)

connectDB()
connectRedis()

app.use(helmet({
  crossOriginEmbedderPolicy: false,
  contentSecurityPolicy: false, 
}))

app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}))

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, 
  max: 100,
  message: { error: 'Too many requests, please try again later.' },
})
app.use('/api/', limiter)

const aiLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, 
  max: 20,
  message: { error: 'AI rate limit reached. Please wait a moment.' },
})
app.use('/api/chat', aiLimiter)

app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true, limit: '10mb' }))

if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('dev'))
}

app.use('/api/auth', authRoutes)
app.use('/api/chat', chatRoutes)
app.use('/api/voice', voiceRoutes)
app.use('/api/emotion', emotionRoutes)

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    env: process.env.NODE_ENV,
  })
})

app.use('*', (req, res) => {
  res.status(404).json({ error: 'Endpoint not found' })
})

app.use((err, req, res, next) => {
  console.error('Unhandled error:', err)
  res.status(err.status || 500).json({
    error: process.env.NODE_ENV === 'production'
      ? 'Internal server error'
      : err.message,
  })
})

initSocket(server)

const PORT = process.env.PORT || 5000
server.listen(PORT, () => {
  console.log(`\n🌿 MindfulAI server running on http://localhost:${PORT}`)
  console.log(`   Environment: ${process.env.NODE_ENV || 'development'}\n`)
})

module.exports = { app, server }
