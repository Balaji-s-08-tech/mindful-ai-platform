
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GEMMA_SERVICE_URL: str = os.getenv("GEMMA_SERVICE_URL", "http://localhost:1234")
GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", "google/gemma-4-e4b")
GEMMA_TIMEOUT_MS: int = int(os.getenv("GEMMA_TIMEOUT_MS", "60000"))

_AVAILABILITY_TIMEOUT_S: float = 5.0

_CHAT_COMPLETIONS_PATH: str = "/v1/chat/completions"
_MODELS_PATH: str = "/v1/models"

async def is_available() -> bool:
    
    try:
        async with httpx.AsyncClient(timeout=_AVAILABILITY_TIMEOUT_S) as client:
            response = await client.get(f"{GEMMA_SERVICE_URL}{_MODELS_PATH}")
            available = response.status_code == 200
            if not available:
                logger.debug(
                    "[LMStudioService] Availability probe returned HTTP %d",
                    response.status_code,
                )
            return available
    except Exception as exc:
        logger.debug("[LMStudioService] Availability probe failed: %s", exc)
        return False

async def generate(
    system_prompt: str,
    messages: List[Dict[str, str]],
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    
    opts = options or {}
    payload: Dict[str, Any] = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "stream": False,
        "temperature": float(opts.get("temperature", 0.7)),
        "max_tokens": int(opts.get("max_tokens", 1024)),
    }

    timeout_s = GEMMA_TIMEOUT_MS / 1000.0
    logger.debug(
        "[LMStudioService] Sending non-stream request (model=%s, timeout=%.1fs)",
        GEMMA_MODEL,
        timeout_s,
    )

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        response = await client.post(
            f"{GEMMA_SERVICE_URL}{_CHAT_COMPLETIONS_PATH}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

    choices = data.get("choices", [])
    content: str = ""
    if choices:
        content = choices[0].get("message", {}).get("content", "")

    usage = data.get("usage", {})
    tokens: int = int(usage.get("total_tokens", 0))

    logger.debug("[LMStudioService] Non-stream response received: %d tokens", tokens)

    return {
        "content": content,
        "model": data.get("model", GEMMA_MODEL),
        "tokens": tokens,
    }

async def generate_stream(
    system_prompt: str,
    messages: List[Dict[str, str]],
    options: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[str, None]:
    
    opts = options or {}
    payload: Dict[str, Any] = {
        "model": GEMMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "stream": True,
        "temperature": float(opts.get("temperature", 0.7)),
        "max_tokens": int(opts.get("max_tokens", 1024)),
    }

    timeout_s = GEMMA_TIMEOUT_MS / 1000.0
    logger.debug(
        "[LMStudioService] Starting streaming request (model=%s, timeout=%.1fs)",
        GEMMA_MODEL,
        timeout_s,
    )

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        async with client.stream(
            "POST",
            f"{GEMMA_SERVICE_URL}{_CHAT_COMPLETIONS_PATH}",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():

                if not line or not line.startswith("data:"):
                    continue

                raw = line[len("data:"):].strip()

                if raw == "[DONE]":
                    logger.debug("[LMStudioService] Stream completed ([DONE] received).")
                    break

                try:
                    import json
                    chunk = json.loads(raw)
                except Exception:
                    logger.debug("[LMStudioService] Skipping malformed SSE chunk: %r", raw)
                    continue

                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    token: str = delta.get("content", "")
                    if token:
                        yield token
