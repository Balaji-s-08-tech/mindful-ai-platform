
from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

EMOTION_SERVICE_URL: str = os.getenv("EMOTION_SERVICE_URL", "http://localhost:8000")

_HEALTH_TIMEOUT: float = 5.0
_DETECT_TIMEOUT: float = 10.0

def get_emotion_service_health() -> Dict[str, Any]:
    
    try:
        response = httpx.get(
            f"{EMOTION_SERVICE_URL}/health",
            timeout=_HEALTH_TIMEOUT,
        )
        if response.status_code == 200:
            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text}
            return {"available": True, "status": body}
        return {
            "available": False,
            "error": f"Service returned HTTP {response.status_code}",
        }
    except httpx.TimeoutException as exc:
        logger.warning("[EmotionService] Health check timed out: %s", exc)
        return {"available": False, "error": "Health check timed out"}
    except Exception as exc:
        logger.warning("[EmotionService] Health check failed: %s", exc)
        return {"available": False, "error": str(exc)}

def detect_emotion(image_data: bytes, content_type: str = "image/jpeg") -> Dict[str, Any]:
    
    from apps.common.exceptions import ApplicationError

    if not image_data:
        raise ApplicationError("No image data provided for emotion detection.", 400)

    extension_map: Dict[str, str] = {
        "image/jpeg": "image.jpg",
        "image/jpg": "image.jpg",
        "image/png": "image.png",
        "image/webp": "image.webp",
    }
    filename: str = extension_map.get(content_type.lower(), "image.jpg")

    try:
        logger.info(
            "[EmotionService] Sending %d bytes (%s) for detection.",
            len(image_data),
            content_type,
        )
        response = httpx.post(
            f"{EMOTION_SERVICE_URL}/detect",
            files={"file": (filename, image_data, content_type)},
            timeout=_DETECT_TIMEOUT,
        )
        response.raise_for_status()
        result: Dict[str, Any] = response.json()
        logger.info("[EmotionService] Detection result: %s", result)
        return result

    except httpx.TimeoutException as exc:
        logger.error("[EmotionService] Detection timed out: %s", exc)
        raise ApplicationError("Emotion service timed out.", 503)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[EmotionService] HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise ApplicationError(
            f"Emotion service returned HTTP {exc.response.status_code}.",
            503,
        )
    except httpx.RequestError as exc:
        logger.error("[EmotionService] Request error: %s", exc)
        raise ApplicationError("Could not reach the emotion detection service.", 503)
    except Exception as exc:
        logger.exception("[EmotionService] Unexpected error: %s", exc)
        raise ApplicationError("Emotion detection failed unexpectedly.", 500)
