# 🌿 MindfulAI — AI Emotional Support Companion

A production-grade, multi-modal AI emotional support web application combining:
- **Chat-based LLM** (Claude / Anthropic API)
- **Real-time voice** (Speech-to-Text + Text-to-Speech)
- **Facial emotion detection** (OpenCV + DeepFace microservice)
- **Multi-modal decision engine** fusing all three signals

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (React)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   Chat   │  │  Camera  │  │  Voice   │              │
│  │Interface │  │  Panel   │  │  Button  │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                   │
│  ┌────▼──────────────▼──────────────▼──────────────┐   │
│  │         Zustand State (chat/emotion/auth)        │   │
│  └─────────────────────┬────────────────────────────┘   │
└────────────────────────┼────────────────────────────────┘
                         │ HTTP / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Node.js + Express Backend                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ /api/auth│  │/api/chat │  │/api/voice│              │
│  └──────────┘  └────┬─────┘  └────┬─────┘              │
│  ┌──────────┐       │              │                   │
│  │Socket.IO │  ┌────▼─────┐  ┌────▼─────┐              │
│  │  Server  │  │ AI Svc   │  │Whisper / │              │
│  └──────────┘  │ (Claude) │  │ElevenLabs│              │
│                └──────────┘  └──────────┘              │
│  ┌────────────────────────────────────────────────┐    │
│  │  MongoDB (sessions/messages)  Redis (cache)    │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────┐
│   Python FastAPI — Emotion Detection     │
│   OpenCV + DeepFace → 7 emotions         │
└──────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
mindful-ai/
├── frontend/                  # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth/          # PrivateRoute
│   │   │   ├── Camera/        # CameraPanel (webcam + emotion overlay)
│   │   │   ├── Chat/          # ChatInterface, MessageBubble, WelcomeScreen
│   │   │   ├── Dashboard/     # Sidebar, EmotionPanel
│   │   │   ├── UI/            # DisclaimerBanner
│   │   │   └── Voice/         # VoiceButton (STT + TTS)
│   │   ├── pages/             # LoginPage, RegisterPage, DashboardPage
│   │   ├── services/          # api.js, socketService.js, voiceService.js, emotionService.js
│   │   └── store/             # authStore.js, chatStore.js, emotionStore.js
│   ├── .env.example
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/                   # Node.js + Express
│   ├── src/
│   │   ├── config/            # database.js, redis.js
│   │   ├── controllers/       # authController, chatController, voiceController, emotionController
│   │   ├── middleware/        # auth.js (JWT protect)
│   │   ├── models/            # User.js, ChatSession.js
│   │   ├── routes/            # auth, chat, voice, emotion
│   │   ├── services/          # aiService.js (Claude API + crisis detection)
│   │   ├── socket/            # socketServer.js (Socket.IO + JWT)
│   │   └── index.js           # App entry point
│   ├── .env.example
│   └── Dockerfile
│
├── emotion-service/           # Python FastAPI
│   ├── main.py                # DeepFace emotion detection + OpenCV fallback
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml         # Full stack orchestration
└── README.md                  # This file
```

---

## 🚀 Quick Start (Development)

### Prerequisites
- Node.js 20+
- Python 3.11+
- MongoDB (local or Atlas)
- Redis (optional — gracefully degraded)

### Step 1 — Clone and configure

```bash
git clone <repo-url>
cd mindful-ai
```

### Step 2 — Backend setup

```bash
cd backend

# Install dependencies
npm install

# Copy and configure environment
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY and MongoDB URI

# Start backend
npm run dev
# ✅ Running on http://localhost:5000
```

### Step 3 — Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment (defaults work for local dev)
cp .env.example .env

# Start dev server
npm run dev
# ✅ Running on http://localhost:3000
```

### Step 4 — Emotion Detection Service (optional but recommended)

```bash
cd emotion-service

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies (first install ~500MB due to TensorFlow)
pip install -r requirements.txt

# Copy env
cp .env.example .env

# Start service
python main.py
# ✅ Running on http://localhost:8000
# ⚠️  First startup downloads DeepFace model weights (~500MB)
```

### Step 5 — Open the app

Navigate to **http://localhost:3000**, create an account, and start a conversation.

---

## 🐳 Docker Compose (Full Stack)

```bash
# 1. Configure environment files
cp backend/.env.example backend/.env
cp emotion-service/.env.example emotion-service/.env
# Edit both .env files with your API keys

# 2. Build and start all services
docker compose up --build

# ✅ Frontend:         http://localhost:3000
# ✅ Backend API:      http://localhost:5000
# ✅ Emotion Service:  http://localhost:8000
# ✅ MongoDB:          localhost:27017
# ✅ Redis:            localhost:6379
```

---

## 🔑 Required API Keys

| Service | Key | Required | Notes |
|---------|-----|----------|-------|
| Anthropic Claude | `ANTHROPIC_API_KEY` | ✅ Yes | Core LLM |
| OpenAI Whisper | `OPENAI_API_KEY` | ⚠️ Optional | Falls back to browser STT |
| ElevenLabs TTS | `ELEVENLABS_API_KEY` | ⚠️ Optional | Falls back to browser TTS |

---

## 🧠 Multi-Modal Emotion Fusion

The system combines three input channels with weighted fusion:

| Channel | Weight | Source |
|---------|--------|--------|
| Facial expression | **50%** | Webcam → DeepFace |
| Voice tone | **30%** | Speech analysis heuristics |
| Text sentiment | **20%** | Real-time keyword analysis |

The **combined emotion** drives:
1. System prompt customization for the LLM
2. Wellness suggestions (breathing, journaling, movement)
3. Crisis detection and resource escalation

---

## 🔐 Security

- JWT authentication with 7-day expiry
- Passwords hashed with bcrypt (12 rounds)
- Rate limiting: 100 req/15min (global), 20 req/min (AI endpoints)
- Helmet.js security headers
- Input validation on all endpoints
- Non-root Docker containers

---

## 🚨 Safety Features

- **Crisis detection**: Regex patterns detect self-harm/suicidal language
- **Immediate escalation**: Auto-responds with 988 Lifeline and crisis resources
- **Disclaimer banner**: Prominent UI notice on first login
- **No therapist impersonation**: System prompt explicitly limits AI scope
- **Distress indicator**: Banner appears when combined emotion is fearful/sad/angry

---

## 🌍 Detected Emotions

| Emotion | Description |
|---------|-------------|
| 😊 Happy | Positive, content |
| 😢 Sad | Low mood, grief |
| 😠 Angry | Frustration, rage |
| 😰 Fearful | Anxiety, fear |
| 😲 Surprised | Startled, shocked |
| 😒 Disgusted | Aversion, unease |
| 😐 Neutral | Calm, resting |

---

## 📜 License

MIT License — see LICENSE file.

---

> ⚠️ **Disclaimer**: MindfulAI is an emotional support tool and is NOT a substitute for professional mental health care. If you or someone you know is in crisis, please contact the **988 Suicide & Crisis Lifeline** (call or text 988) or emergency services.
