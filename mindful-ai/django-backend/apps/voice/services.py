
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

OPENAI_WHISPER_URL: str = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_CHAT_URL: str = "https://api.openai.com/v1/chat/completions"
ELEVENLABS_TTS_URL: str = (
    "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
)

WHISPER_TIMEOUT: float = 60.0
TTS_TIMEOUT: float = 30.0
CHAT_TIMEOUT: float = 30.0

def transcribe_audio(audio_file: Any) -> str:
    
    from apps.common.exceptions import ApplicationError

    if not OPENAI_API_KEY:
        raise ApplicationError("OpenAI API key is not configured.", 500)

    file_name: str = getattr(audio_file, "name", "audio.webm")
    content_type: str = getattr(audio_file, "content_type", "audio/webm")

    try:
        logger.info("[Voice] Sending audio to Whisper – file=%s", file_name)
        audio_file.seek(0)
        response = httpx.post(
            OPENAI_WHISPER_URL,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": (file_name, audio_file.read(), content_type)},
            data={"model": "whisper-1"},
            timeout=WHISPER_TIMEOUT,
        )
        response.raise_for_status()
        payload: Dict[str, Any] = response.json()
        transcript: str = payload.get("text", "").strip()
        logger.info("[Voice] Whisper transcript obtained (%d chars).", len(transcript))
        return transcript

    except httpx.TimeoutException as exc:
        logger.error("[Voice] Whisper timed out: %s", exc)
        raise ApplicationError("Speech-to-text service timed out.", 504)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[Voice] Whisper HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise ApplicationError(
            f"Speech-to-text service returned an error: {exc.response.status_code}",
            502,
        )
    except httpx.RequestError as exc:
        logger.error("[Voice] Whisper request error: %s", exc)
        raise ApplicationError("Could not reach the speech-to-text service.", 502)
    except Exception as exc:
        logger.exception("[Voice] Unexpected Whisper error: %s", exc)
        raise ApplicationError("Transcription failed unexpectedly.", 500)

def text_to_speech(text: str) -> bytes:
    
    from apps.common.exceptions import ApplicationError

    if not ELEVENLABS_API_KEY:
        raise ApplicationError("ElevenLabs API key is not configured.", 500)

    url: str = ELEVENLABS_TTS_URL.format(voice_id=ELEVENLABS_VOICE_ID)
    payload: Dict[str, Any] = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    try:
        logger.info("[Voice] Sending text to ElevenLabs TTS (%d chars).", len(text))
        response = httpx.post(
            url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json=payload,
            timeout=TTS_TIMEOUT,
        )
        response.raise_for_status()
        audio_bytes: bytes = response.content
        logger.info("[Voice] TTS audio received (%d bytes).", len(audio_bytes))
        return audio_bytes

    except httpx.TimeoutException as exc:
        logger.error("[Voice] ElevenLabs TTS timed out: %s", exc)
        raise ApplicationError("Text-to-speech service timed out.", 504)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[Voice] ElevenLabs HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise ApplicationError(
            f"Text-to-speech service returned an error: {exc.response.status_code}",
            502,
        )
    except httpx.RequestError as exc:
        logger.error("[Voice] ElevenLabs request error: %s", exc)
        raise ApplicationError("Could not reach the text-to-speech service.", 502)
    except Exception as exc:
        logger.exception("[Voice] Unexpected TTS error: %s", exc)
        raise ApplicationError("Text-to-speech failed unexpectedly.", 500)

def _get_ai_response(transcript: str, emotion_context: Optional[Dict[str, Any]]) -> str:
    
    from apps.common.exceptions import ApplicationError

    if not OPENAI_API_KEY:
        raise ApplicationError("OpenAI API key is not configured.", 500)

    system_message: str = (
        "You are MindfulAI, a compassionate mental-health support assistant. "
        "Respond with empathy, clarity, and actionable mindfulness techniques."
    )

    if emotion_context:
        emotion: str = emotion_context.get("emotion", "unknown")
        confidence: float = emotion_context.get("confidence", 0.0)
        system_message += (
            f"\n\nThe user's detected emotion is '{emotion}' "
            f"(confidence: {confidence:.0%}). "
            "Tailor your response accordingly."
        )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": transcript},
    ]

    try:
        response = httpx.post(
            OPENAI_CHAT_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=CHAT_TIMEOUT,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        ai_text: str = data["choices"][0]["message"]["content"].strip()
        logger.info("[Voice] AI response obtained (%d chars).", len(ai_text))
        return ai_text

    except httpx.TimeoutException as exc:
        logger.error("[Voice] OpenAI Chat timed out: %s", exc)
        raise ApplicationError("AI service timed out.", 504)
    except httpx.HTTPStatusError as exc:
        logger.error("[Voice] OpenAI Chat HTTP error %s: %s", exc.response.status_code, exc.response.text)
        raise ApplicationError(f"AI service returned an error: {exc.response.status_code}", 502)
    except (KeyError, IndexError) as exc:
        logger.error("[Voice] Unexpected OpenAI Chat response shape: %s", exc)
        raise ApplicationError("Unexpected AI response format.", 502)
    except httpx.RequestError as exc:
        logger.error("[Voice] OpenAI Chat request error: %s", exc)
        raise ApplicationError("Could not reach the AI service.", 502)
    except Exception as exc:
        logger.exception("[Voice] Unexpected Chat error: %s", exc)
        raise ApplicationError("AI processing failed unexpectedly.", 500)

def process_voice_pipeline(
    audio_file: Any,
    user: Any,
    session_id: Optional[str] = None,
    emotion_context: Optional[Dict[str, Any]] = None,
    tts_enabled: bool = False,
) -> Dict[str, Any]:
    
    import base64

    logger.info(
        "[Voice] Pipeline start – user=%s session=%s tts=%s",
        getattr(user, "id", "?"),
        session_id,
        tts_enabled,
    )

    transcript: str = transcribe_audio(audio_file)

    if not transcript:
        from apps.common.exceptions import ApplicationError
        raise ApplicationError(
            "No speech detected in the audio. Please try again.", 422
        )

    ai_response: str = _get_ai_response(transcript, emotion_context)

    audio_b64: Optional[str] = None
    if tts_enabled:
        try:
            audio_bytes: bytes = text_to_speech(ai_response)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as exc:

            logger.warning("[Voice] TTS step failed (non-fatal): %s", exc)

    result: Dict[str, Any] = {
        "transcript": transcript,
        "ai_response": ai_response,
        "audio_b64": audio_b64,
        "session_id": session_id or None,
    }
    logger.info("[Voice] Pipeline complete – user=%s", getattr(user, "id", "?"))
    return result
