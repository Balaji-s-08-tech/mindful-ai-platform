const express = require('express')
const { protect } = require('../middleware/auth')
const {
  getSessions,
  createSession,
  getMessages,
  sendMessage,
  streamMessage,
  deleteSession,
} = require('../controllers/chatController')

const router = express.Router()

router.use(protect)

router.get('/sessions',                              getSessions)
router.post('/sessions',                             createSession)
router.delete('/sessions/:sessionId',                deleteSession)

router.get('/sessions/:sessionId/messages',          getMessages)
router.post('/sessions/:sessionId/messages',         sendMessage)

router.post('/sessions/:sessionId/messages/stream',  streamMessage)

module.exports = router
