const { createClient } = require('redis')

let client = null

async function connectRedis() {
  try {
    client = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
    })

    client.on('error', (err) => {
      console.warn('Redis error (non-fatal):', err.message)
    })

    client.on('connect', () => {
      console.log('✅ Redis connected')
    })

    await client.connect()
  } catch (err) {
    console.warn('⚠️  Redis unavailable — sessions will use in-memory store:', err.message)
    client = null
  }
}

function getRedis() {
  return client
}

async function cacheGet(key) {
  if (!client) return null
  try {
    const val = await client.get(key)
    return val ? JSON.parse(val) : null
  } catch { return null }
}

async function cacheSet(key, value, ttlSeconds = 3600) {
  if (!client) return
  try {
    await client.setEx(key, ttlSeconds, JSON.stringify(value))
  } catch (err) {
    console.warn('Cache set failed:', err.message)
  }
}

async function cacheDel(key) {
  if (!client) return
  try {
    await client.del(key)
  } catch {}
}

module.exports = { connectRedis: connectRedis, getRedis, cacheGet, cacheSet, cacheDel }

module.exports.default = connectRedis
