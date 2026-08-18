
import asyncio
import logging
from typing import Any, Dict, Optional

from apps.chat.models import ChatSession, Message
from apps.chat.selectors import get_context_window, get_session_by_id
from apps.common.exceptions import ApplicationError

logger = logging.getLogger(__name__)

def create_session(user: Any, title: str = 'New Conversation') -> ChatSession:
    
    session = ChatSession.objects.create(user=user, title=title.strip() or 'New Conversation')
    logger.info('[ChatService] Created session %s for user %s', session.id, user.id)
    return session

def delete_session(session_id: str, user_id: str) -> None:
    
    session = get_session_by_id(session_id, user_id)
    if not session:
        raise ApplicationError('Session not found.', status_code=404)
    session.soft_delete()
    logger.info('[ChatService] Soft-deleted session %s for user %s', session_id, user_id)

def send_message(
    session_id: str,
    user: Any,
    content: str,
    emotion_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    
    emotion_context = emotion_context or {}

    session = get_session_by_id(session_id, str(user.id))
    if not session:
        raise ApplicationError('Session not found.', status_code=404)

    user_message = Message.objects.create(
        session=session,
        role=Message.Role.USER,
        content=content,
        emotion_context=emotion_context,
    )
    logger.debug('[ChatService] Saved user message %s in session %s', user_message.id, session_id)

    is_first_message = session.message_count == 0
    if is_first_message:
        session.generate_title(content)

    history = get_context_window(session_id)

    try:
        from apps.ai.input_normalizer import build_unified_context
        from apps.ai.services import generate_response

        unified_ctx = build_unified_context(
            message=content,
            user_id=str(user.id),
            input_type='text',
            emotion_data=emotion_context,
            history=history,
            session_id=session_id,
        )

        ai_result = asyncio.run(generate_response(unified_ctx))

    except Exception as exc:
        logger.error('[ChatService] AI service error for session %s: %s', session_id, exc)
        raise ApplicationError(
            'AI service is temporarily unavailable. Please try again.',
            status_code=503,
        ) from exc

    ai_message = Message.objects.create(
        session=session,
        role=Message.Role.ASSISTANT,
        content=ai_result.content,
        tokens=ai_result.tokens,
        model=ai_result.model,
    )
    logger.debug('[ChatService] Saved AI message %s in session %s', ai_message.id, session_id)

    session.message_count += 2

    combined_emotion: Optional[str] = emotion_context.get('combined')
    if combined_emotion:
        summary: Dict[str, Any] = session.emotion_summary or {'dominant': None, 'progression': []}
        summary.setdefault('progression', []).append(combined_emotion)

        summary['dominant'] = combined_emotion
        session.emotion_summary = summary

    session.save(update_fields=['message_count', 'emotion_summary', 'title', 'updated_at'])

    logger.info(
        '[ChatService] Completed turn in session %s — provider=%s latency=%sms crisis=%s',
        session_id,
        ai_result.provider,
        ai_result.latency_ms,
        ai_result.is_crisis,
    )

    return {
        'user_message': user_message,
        'ai_message': ai_message,
        'meta': {
            'provider': ai_result.provider,
            'latency_ms': ai_result.latency_ms,
            'is_crisis': ai_result.is_crisis,
        },
    }
