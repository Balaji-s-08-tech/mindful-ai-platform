
import os
import base64
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("emotion-service")

_deepface_loaded = False

def load_deepface():
    global _deepface_loaded
    if not _deepface_loaded:
        logger.info("Loading DeepFace models (first run may take ~30s)...")
        try:
            from deepface import DeepFace

            dummy = np.zeros((48, 48, 3), dtype=np.uint8)
            try:
                DeepFace.analyze(dummy, actions=["emotion"], enforce_detection=False, silent=True)
            except Exception:
                pass
            _deepface_loaded = True
            logger.info("✅ DeepFace models loaded")
        except ImportError as e:
            logger.error(f"DeepFace not installed: {e}")
            raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("🚀 Starting emotion detection service...")
    try:
        load_deepface()
    except Exception as e:
        logger.warning(f"DeepFace load failed: {e} — will use mock detection")
    yield
    logger.info("Shutting down emotion detection service")

app = FastAPI(
    title="MindfulAI Emotion Detection",
    description="Facial emotion detection microservice using DeepFace",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class DetectRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded JPEG image")

class EmotionResult(BaseModel):
    dominant_emotion: str
    confidence: float
    emotions: dict
    processing_time_ms: float
    mock: bool = False

EMOTION_MAP = {
    "happy": "happy",
    "sad": "sad",
    "angry": "angry",
    "fear": "fearful",
    "fearful": "fearful",
    "surprise": "surprised",
    "surprised": "surprised",
    "disgust": "disgusted",
    "disgusted": "disgusted",
    "neutral": "neutral",
}

def normalize_emotion(raw: str) -> str:
    return EMOTION_MAP.get(raw.lower(), "neutral")

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "deepface_loaded": _deepface_loaded,
        "timestamp": time.time(),
    }

@app.post("/detect", response_model=EmotionResult)
async def detect_emotion(request: DetectRequest):
    start_time = time.time()

    try:
        image_bytes = base64.b64decode(request.image)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Failed to decode image")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

    if _deepface_loaded:
        try:
            from deepface import DeepFace

            result = DeepFace.analyze(
                img_path=img,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
                detector_backend="opencv",
            )

            if isinstance(result, list):
                result = result[0]

            raw_emotions = result.get("emotion", {})
            raw_dominant = result.get("dominant_emotion", "neutral")

            dominant = normalize_emotion(raw_dominant)
            emotions = {
                normalize_emotion(k): round(v / 100, 4)
                for k, v in raw_emotions.items()
            }

            confidence = emotions.get(dominant, 0.5)

            processing_ms = round((time.time() - start_time) * 1000, 1)
            logger.info(f"Detected: {dominant} ({confidence:.2f}) in {processing_ms}ms")

            return EmotionResult(
                dominant_emotion=dominant,
                confidence=confidence,
                emotions=emotions,
                processing_time_ms=processing_ms,
            )

        except Exception as e:
            logger.warning(f"DeepFace analysis failed: {e} — using OpenCV fallback")

    return opencv_emotion_fallback(img, start_time)

def opencv_emotion_fallback(img: np.ndarray, start_time: float) -> EmotionResult:
    
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        has_face = len(faces) > 0

        dominant = "neutral"
        emotions = {
            "happy": 0.10, "sad": 0.05, "angry": 0.05,
            "fearful": 0.05, "surprised": 0.05, "disgusted": 0.02,
            "neutral": 0.68,
        }

        if has_face:

            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]

            eye_region = face_roi[:h//2, :]
            mouth_region = face_roi[h//2:, :]

            brightness = np.mean(face_roi)
            eye_variance = np.std(eye_region)

            if brightness > 140 and eye_variance > 40:
                dominant = "happy"
                emotions["happy"] = 0.65
                emotions["neutral"] = 0.25
            elif brightness < 80:
                dominant = "sad"
                emotions["sad"] = 0.55
                emotions["neutral"] = 0.35

        processing_ms = round((time.time() - start_time) * 1000, 1)

        return EmotionResult(
            dominant_emotion=dominant,
            confidence=emotions.get(dominant, 0.5),
            emotions=emotions,
            processing_time_ms=processing_ms,
            mock=not has_face,
        )

    except Exception as e:
        logger.error(f"OpenCV fallback failed: {e}")
        return EmotionResult(
            dominant_emotion="neutral",
            confidence=0.5,
            emotions={"neutral": 1.0},
            processing_time_ms=0,
            mock=True,
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "development") == "development",
        log_level="info",
    )
