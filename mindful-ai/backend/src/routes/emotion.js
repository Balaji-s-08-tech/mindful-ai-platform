const express = require('express')
const { protect } = require('../middleware/auth')
const { detectEmotion, healthCheck } = require('../controllers/emotionController')

const router = express.Router()

router.get('/health', healthCheck) 
router.post('/detect', protect, detectEmotion)

module.exports = router
