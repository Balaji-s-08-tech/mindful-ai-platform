
const { createLogger, format, transports } = require('winston')
const { combine, timestamp, colorize, printf, errors } = format

const isProduction = process.env.NODE_ENV === 'production'

const logFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} [${level}]: ${stack || message}`
})

const logger = createLogger({
  level: isProduction ? 'info' : 'debug',
  format: combine(
    errors({ stack: true }),
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    isProduction ? format.json() : combine(colorize(), logFormat)
  ),
  transports: [
    new transports.Console(),
    ...(isProduction
      ? [
          new transports.File({ filename: 'logs/error.log', level: 'error' }),
          new transports.File({ filename: 'logs/combined.log' }),
        ]
      : []),
  ],
})

module.exports = logger
