const express = require('express')
const { protect } = require('../middleware/auth')
const { transcribe, textToSpeech, processVoiceMessage } = require('../controllers/voiceController')

const router = express.Router()

router.use(protect)

router.post('/transcribe', transcribe)

router.post('/tts', textToSpeech)

router.post('/process', processVoiceMessage)

module.exports = router
