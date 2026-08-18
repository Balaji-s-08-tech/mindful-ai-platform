
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class EmotionData:
    
    facial: Optional[str] = None
    voice: Optional[str] = None
    text: Optional[str] = None
    combined: Optional[str] = None
    confidence: float = 0.0

@dataclass
class HistoryMessage:
    
    role: str
    content: str

@dataclass
class UnifiedContext:
    
    message: str
    user_id: str
    input_type: str
    emotion: EmotionData = field(default_factory=EmotionData)
    history: List[HistoryMessage] = field(default_factory=list)
    raw_transcript: Optional[str] = None
    session_id: Optional[str] = None

def build_unified_context(
    message: str,
    user_id: str,
    input_type: str = "text",
    emotion_data: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    raw_transcript: Optional[str] = None,
    session_id: Optional[str] = None,
) -> UnifiedContext:
    
    emotion = EmotionData(
        facial=emotion_data.get("facial") if emotion_data else None,
        voice=emotion_data.get("voice") if emotion_data else None,
        text=emotion_data.get("text") if emotion_data else None,
        combined=emotion_data.get("combined") if emotion_data else None,
        confidence=float(emotion_data.get("confidence", 0.0)) if emotion_data else 0.0,
    )

    history_messages: List[HistoryMessage] = [
        HistoryMessage(
            role=m.get("role", "user"),
            content=m.get("content", ""),
        )
        for m in (history or [])
    ]

    return UnifiedContext(
        message=message.strip(),
        user_id=str(user_id),
        input_type=input_type,
        emotion=emotion,
        history=history_messages,
        raw_transcript=raw_transcript,
        session_id=session_id,
    )
