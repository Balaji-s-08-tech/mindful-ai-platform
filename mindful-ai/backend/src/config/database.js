const mongoose = require('mongoose')

let isConnected = false

async function connectDB() {
  if (isConnected) return

  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    })
    isConnected = true
    console.log(`✅ MongoDB connected: ${conn.connection.host}`)
  } catch (err) {
    console.error('❌ MongoDB connection failed:', err.message)
    
    setTimeout(connectDB, 5000)
  }
}

mongoose.connection.on('disconnected', () => {
  isConnected = false
  console.warn('MongoDB disconnected. Reconnecting...')
  connectDB()
})

module.exports = connectDB
