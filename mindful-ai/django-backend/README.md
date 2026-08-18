# MindfulAI — Django Backend

A production-ready Django + Django REST Framework backend for MindfulAI, ported from the original Node.js/Express/MongoDB stack.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | Django 5.1 + Django REST Framework 3.15 |
| Database | PostgreSQL 16 |
| Auth | SimpleJWT (access + refresh + blacklist) |
| Cache / Queue Broker | Redis 7 |
| Async Tasks | Celery 5 |
| WebSocket | python-socketio 5 (ASGI, Socket.IO protocol compatible) |
| ASGI Server | Uvicorn + uvloop |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| AI | Gemma via Ollama (local) → Claude Sonnet (fallback) |
| TTS | ElevenLabs |
| STT | OpenAI Whisper |

---

## Quick Start (Local Development)

### 1. Prerequisites

- Python 3.13+
- PostgreSQL 16 running locally
- Redis running locally
- (Optional) Ollama with `gemma3:4b` pulled

### 2. Setup

```bash
# Navigate to the backend directory
cd mindful-ai/django-backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Copy example and fill in your values
copy .env.example .env
```

Edit `.env` and set at minimum:
```env
DJANGO_SECRET_KEY=your-secret-key-min-50-chars
DJANGO_DEBUG=True
DB_NAME=mindful_ai
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Database setup

```bash
# Create the PostgreSQL database
createdb mindful_ai

# Run migrations
python manage.py migrate

# Create a superuser (for /admin)
python manage.py createsuperuser
```

### 5. Run the server

```bash
# Development — Uvicorn ASGI (required for Socket.IO)
uvicorn config.asgi:application --reload --port 8000
```

---

## API Endpoints

All responses follow the standardised envelope:
```json
{ "success": true, "message": "...", "data": {} }
{ "success": false, "message": "...", "errors": {} }
```

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login → JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | Blacklist refresh token |
| GET  | `/api/auth/me` | Get current user |
| POST | `/api/auth/forgot-password` | Request reset link |
| POST | `/api/auth/reset-password` | Confirm reset |

### Users
| Method | Path | Description |
|--------|------|-------------|
| GET/PATCH | `/api/users/profile` | Get or update profile |
| POST | `/api/users/change-password` | Change password |
| DELETE | `/api/users/profile` | Deactivate account |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/chat/sessions` | List sessions |
| POST | `/api/chat/sessions` | Create session |
| DELETE | `/api/chat/sessions/<id>` | Delete session |
| GET | `/api/chat/sessions/<id>/messages` | Get messages |
| POST | `/api/chat/sessions/<id>/messages` | Send message (non-streaming) |
| POST | `/api/chat/sessions/<id>/messages/stream` | Send message (SSE streaming) |

### Voice
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/voice/transcribe` | Whisper STT |
| POST | `/api/voice/tts` | ElevenLabs TTS |
| POST | `/api/voice/process` | Full pipeline (STT → AI → TTS) |

### Emotion
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/emotion/detect` | Detect emotion from image |
| GET  | `/api/emotion/health` | Emotion service health check |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Backend health check |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/redoc/` | ReDoc |
| GET | `/admin/` | Django Admin |

---

## WebSocket (Socket.IO)

Connects at `ws://localhost:8000/socket.io/` — fully compatible with the existing React frontend.

**Authentication:** Pass JWT in the `auth` option:
```js
const socket = io('http://localhost:8000', {
  auth: { token: accessToken }
})
```

**Events (Client → Server):**
- `join_session` / `leave_session`
- `ai_stream_request` → streaming AI response
- `voice_to_ai` → voice transcript → AI → optional TTS
- `emotion_detected`
- `typing_start` / `typing_stop`
- `ping`

**Events (Server → Client):**
- `ai_message_start` / `ai_token` / `ai_message_end`
- `ai_audio_response` (base64 TTS)
- `ai_crisis`
- `ai_stream_error`
- `emotion_update`
- `pong`

---

## Docker Deployment

```bash
# Copy and configure
copy .env.example .env
# (edit .env with production values)

# Build and start all services
docker-compose up --build -d

# Run migrations
docker-compose exec django-backend python manage.py migrate

# Create superuser
docker-compose exec django-backend python manage.py createsuperuser
```

Services started:
- `mindful-django` → `http://localhost:8000`
- `mindful-postgres` → port 5432
- `mindful-redis` → port 6379
- `mindful-celery-worker`
- `mindful-celery-beat`

---

## Running Tests

```bash
# Run all tests
python manage.py test apps

# Run tests for a specific app
python manage.py test apps.users

# With coverage
pip install coverage
coverage run manage.py test apps
coverage report -m
```

---

## Project Structure

```
django-backend/
├── config/                     # Django project config
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── development.py      # Dev overrides
│   │   └── production.py       # Production overrides
│   ├── urls.py
│   ├── asgi.py                 # ASGI + Socket.IO entry point
│   └── wsgi.py
│
├── apps/
│   ├── common/                 # Shared: models, responses, exceptions, pagination
│   ├── users/                  # Auth + user profiles
│   ├── chat/                   # Sessions, messages, SSE, Socket.IO consumers
│   ├── voice/                  # STT (Whisper) + TTS (ElevenLabs) pipeline
│   ├── emotion/                # Emotion detection proxy
│   ├── ai/                     # AI engine: prompt_builder, gemma_service, services
│   ├── notifications/          # Notification models + Celery task stubs
│   └── analytics/              # Analytics model stubs
│
├── logs/                       # Rotating log files (git-ignored)
├── media/                      # User uploads (git-ignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── .env.example
```

---

## Environment Variables Reference

See [`.env.example`](.env.example) for the full list with documentation.

---

## License

MIT — See the project root LICENSE file.
