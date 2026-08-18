
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import anthropic

from apps.ai import gemma_service as gemma
from apps.ai.input_normalizer import UnifiedContext
from apps.ai.prompt_builder import PromptPackage, build_prompt_package

logger = logging.getLogger(__name__)

CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
LLM_PRIMARY: str = os.getenv("LLM_PRIMARY", "gemma")
MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))

FALLBACK_RESPONSE: str = (
    "I'm having a moment of difficulty processing your message. "
    "I'm still here with you — please try again in a moment, or share "
    "what's on your mind in a different way."
)

_LLM_OPTIONS: Dict[str, Any] = {"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}

@dataclass
class AIResponse:
    
    content: str
    model: str
    tokens: int
    is_crisis: bool
    provider: str
    latency_ms: int

def _elapsed_ms(start: float) -> int:
    
    return int((time.time() - start) * 1000)

def _get_claude_client() -> anthropic.Anthropic:
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured.  "
            "Set it in your environment or .env file."
        )
    return anthropic.Anthropic(api_key=api_key)

async def generate_response(context: UnifiedContext) -> AIResponse:
    
    start = time.time()
    pkg: PromptPackage = build_prompt_package(context)

    if pkg.is_crisis:
        logger.info("[AIService] Crisis response returned without LLM call.")
        return AIResponse(
            content=pkg.crisis_response or "",
            model="crisis-handler",
            tokens=0,
            is_crisis=True,
            provider="crisis-handler",
            latency_ms=_elapsed_ms(start),
        )

    if LLM_PRIMARY == "gemma":
        if await gemma.is_available():
            try:
                result = await gemma.generate(pkg.system_prompt, pkg.messages, _LLM_OPTIONS)
                logger.info(
                    "[AIService] Gemma responded: model=%s tokens=%d latency=%dms",
                    result["model"],
                    result["tokens"],
                    _elapsed_ms(start),
                )
                return AIResponse(
                    content=result["content"],
                    model=result["model"],
                    tokens=result["tokens"],
                    is_crisis=False,
                    provider="gemma",
                    latency_ms=_elapsed_ms(start),
                )
            except Exception as exc:
                logger.warning(
                    "[AIService] Gemma generate failed (%s) — falling back to Claude.", exc
                )
        else:
            logger.info("[AIService] Gemma unavailable — routing to Claude.")

    return await _generate_claude(pkg.system_prompt, pkg.messages, start)

async def _generate_claude(
    system_prompt: str,
    messages: List[Dict[str, str]],
    start_time: float,
) -> AIResponse:
    
    try:
        client = _get_claude_client()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )
        content: str = response.content[0].text if response.content else ""
        tokens: int = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
        logger.info(
            "[AIService] Claude responded: model=%s tokens=%d latency=%dms",
            response.model,
            tokens,
            _elapsed_ms(start_time),
        )
        return AIResponse(
            content=content,
            model=response.model,
            tokens=tokens,
            is_crisis=False,
            provider="claude",
            latency_ms=_elapsed_ms(start_time),
        )
    except Exception as exc:
        logger.error("[AIService] Claude generate failed: %s — returning fallback.", exc)
        return AIResponse(
            content=FALLBACK_RESPONSE,
            model="fallback",
            tokens=0,
            is_crisis=False,
            provider="fallback",
            latency_ms=_elapsed_ms(start_time),
        )

async def generate_response_stream(
    context: UnifiedContext,
    on_token: Callable[[str], None],
    on_crisis: Optional[Callable[[str], None]] = None,
) -> AIResponse:
    
    start = time.time()
    pkg: PromptPackage = build_prompt_package(context)

    if pkg.is_crisis:
        logger.info("[AIService] Crisis stream response returned without LLM call.")
        crisis_text = pkg.crisis_response or ""
        if on_crisis:
            on_crisis(crisis_text)
        else:
            on_token(crisis_text)
        return AIResponse(
            content=crisis_text,
            model="crisis-handler",
            tokens=0,
            is_crisis=True,
            provider="crisis-handler",
            latency_ms=_elapsed_ms(start),
        )

    if LLM_PRIMARY == "gemma":
        if await gemma.is_available():
            try:
                full_content = ""
                async for token in gemma.generate_stream(
                    pkg.system_prompt, pkg.messages, _LLM_OPTIONS
                ):
                    full_content += token
                    on_token(token)
                logger.info(
                    "[AIService] Gemma stream complete: latency=%dms", _elapsed_ms(start)
                )
                return AIResponse(
                    content=full_content,
                    model=gemma.GEMMA_MODEL,
                    tokens=0,
                    is_crisis=False,
                    provider="gemma",
                    latency_ms=_elapsed_ms(start),
                )
            except Exception as exc:
                logger.warning(
                    "[AIService] Gemma stream failed (%s) — falling back to Claude.", exc
                )
        else:
            logger.info("[AIService] Gemma unavailable for streaming — routing to Claude.")

    return await _generate_claude_stream(pkg.system_prompt, pkg.messages, on_token, start)

async def _generate_claude_stream(
    system_prompt: str,
    messages: List[Dict[str, str]],
    on_token: Callable[[str], None],
    start_time: float,
) -> AIResponse:
    
    try:
        client = _get_claude_client()
        full_content = ""
        total_tokens = 0
        final_model = CLAUDE_MODEL

        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                full_content += text
                on_token(text)

            final_msg = stream.get_final_message()
            total_tokens = (
                (final_msg.usage.input_tokens or 0)
                + (final_msg.usage.output_tokens or 0)
            )
            final_model = final_msg.model

        logger.info(
            "[AIService] Claude stream complete: model=%s tokens=%d latency=%dms",
            final_model,
            total_tokens,
            _elapsed_ms(start_time),
        )
        return AIResponse(
            content=full_content,
            model=final_model,
            tokens=total_tokens,
            is_crisis=False,
            provider="claude",
            latency_ms=_elapsed_ms(start_time),
        )
    except Exception as exc:
        logger.error("[AIService] Claude stream failed: %s — returning fallback.", exc)
        on_token(FALLBACK_RESPONSE)
        return AIResponse(
            content=FALLBACK_RESPONSE,
            model="fallback",
            tokens=0,
            is_crisis=False,
            provider="fallback",
            latency_ms=_elapsed_ms(start_time),
        )

async def get_status() -> Dict[str, Any]:
    
    gemma_up = await gemma.is_available()
    return {
        "primary": LLM_PRIMARY,
        "gemma": {
            "available": gemma_up,
            "model": gemma.GEMMA_MODEL,
            "endpoint": gemma.GEMMA_SERVICE_URL,
        },
        "claude": {
            "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "model": CLAUDE_MODEL,
        },
        "stream_enabled": os.getenv("STREAM_ENABLED", "true").lower() != "false",
    }
