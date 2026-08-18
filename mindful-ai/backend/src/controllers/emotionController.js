const axios = require('axios')

const EMOTION_SERVICE_URL = process.env.EMOTION_SERVICE_URL || 'http://localhost:8000'

async function detectEmotion(req, res) {
  const { image } = req.body

  if (!image) {
    return res.status(400).json({ message: 'Image data is required' })
  }

  if (typeof image !== 'string' || image.length < 100) {
    return res.status(400).json({ message: 'Invalid image data' })
  }

  try {
    const response = await axios.post(
      `${EMOTION_SERVICE_URL}/detect`,
      { image },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 8000, 
      }
    )

    res.json(response.data)
  } catch (err) {
    if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
      
      console.warn('Emotion service unavailable — returning mock response')
      return res.json({
        dominant_emotion: 'neutral',
        confidence: 0.5,
        emotions: {
          happy: 0.1, sad: 0.05, neutral: 0.7,
          angry: 0.05, fearful: 0.05, surprised: 0.03, disgusted: 0.02,
        },
        mock: true,
        message: 'Emotion service offline',
      })
    }

    if (err.response?.status === 422) {
      return res.status(400).json({ message: 'Could not detect face in image' })
    }

    console.error('Emotion detection error:', err.message)
    res.status(500).json({ message: 'Emotion detection failed' })
  }
}

async function healthCheck(req, res) {
  try {
    const response = await axios.get(`${EMOTION_SERVICE_URL}/health`, { timeout: 3000 })
    res.json({ status: 'online', ...response.data })
  } catch {
    res.json({ status: 'offline', message: 'Emotion service not running' })
  }
}

module.exports = { detectEmotion, healthCheck }
