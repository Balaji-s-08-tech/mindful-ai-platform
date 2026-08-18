
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from apps.ai.input_normalizer import EmotionData, UnifiedContext

logger = logging.getLogger(__name__)

CRISIS_PATTERNS: List[str] = [
    r"\bsuicid\w*\b",
    r"\bkill\s+myself\b",
    r"\bwant\s+to\s+die\b",
    r"\bend\s+my\s+life\b",
    r"\bself.?harm\b",
    r"\bhurt\s+myself\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bcan't\s+go\s+on\b",
    r"\bcannot\s+go\s+on\b",
    r"\boverdose\b",
]

_COMPILED_CRISIS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CRISIS_PATTERNS]

CRISIS_RESPONSE: str = (
    "I'm really concerned about what you've shared. "
    "Please know that you're not alone.\n\n"
    "🔴 If you're in immediate danger, please call emergency services (911).\n"
    "📞 You can also call or text the **988 Suicide & Crisis Lifeline** "
    "(call or text **988**) — available 24/7.\n\n"
    "I'm here with you right now. Can you tell me more about what's happening?"
)

BASE_SYSTEM_PROMPT: str = 

@dataclass
class PromptPackage:
    
    system_prompt: str
    messages: List[Dict[str, str]]
    is_crisis: bool = False
    crisis_response: Optional[str] = None

def detect_crisis(text: str) -> bool:
    
    for pattern in _COMPILED_CRISIS_PATTERNS:
        if pattern.search(text):
            logger.warning("[PromptBuilder] Crisis language detected in user message.")
            return True
    return False

def build_emotion_context_prompt(emotion: Optional[EmotionData]) -> str:
    
    if not emotion:
        return ""

    parts: List[str] = []

    if emotion.combined:
        parts.append(f"Current detected emotion: {emotion.combined}")
    if emotion.facial:
        parts.append(f"Facial expression: {emotion.facial}")
    if emotion.voice:
        parts.append(f"Voice tone: {emotion.voice}")
    if emotion.text and emotion.text != emotion.combined:

        parts.append(f"Text sentiment: {emotion.text}")
    if emotion.confidence and emotion.confidence > 0.0:
        parts.append(f"Detection confidence: {emotion.confidence:.0%}")

    if not parts:
        return ""

    lines = "\n".join(f"- {p}" for p in parts)
    return f"\n\nEmotion context:\n{lines}"

def build_prompt_package(context: UnifiedContext) -> PromptPackage:
    
    if detect_crisis(context.message):
        return PromptPackage(
            system_prompt=BASE_SYSTEM_PROMPT,
            messages=[],
            is_crisis=True,
            crisis_response=CRISIS_RESPONSE,
        )

    emotion_block = build_emotion_context_prompt(context.emotion)
    system_prompt = BASE_SYSTEM_PROMPT + emotion_block

    valid_roles = {"user", "assistant"}
    messages: List[Dict[str, str]] = [
        {"role": m.role, "content": m.content}
        for m in context.history
        if m.role in valid_roles and m.content.strip()
    ]

    messages.append({"role": "user", "content": context.message})

    return PromptPackage(
        system_prompt=system_prompt,
        messages=messages,
        is_crisis=False,
    )
