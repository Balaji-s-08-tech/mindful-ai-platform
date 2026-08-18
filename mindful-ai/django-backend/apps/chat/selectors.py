
from typing import List, Optional

from django.db.models import Prefetch, QuerySet

from apps.chat.models import ChatSession, Message

CONTEXT_WINDOW: int = 20

def get_user_sessions(user_id: str) -> QuerySet:
    
    return (
        ChatSession.objects
        .filter(user_id=user_id, is_deleted=False)
        .select_related('user')
        .order_by('-updated_at')
    )

def get_session_by_id(session_id: str, user_id: str) -> Optional[ChatSession]:
    
    try:
        return ChatSession.objects.get(
            id=session_id,
            user_id=user_id,
            is_deleted=False,
        )
    except ChatSession.DoesNotExist:
        return None

def get_session_with_messages(session_id: str, user_id: str) -> Optional[ChatSession]:
    
    messages_qs = (
        Message.objects
        .order_by('created_at')
        .filter(session_id=session_id)[:50]
    )
    try:
        return (
            ChatSession.objects
            .prefetch_related(
                Prefetch('messages', queryset=messages_qs, to_attr='prefetched_messages')
            )
            .select_related('user')
            .get(id=session_id, user_id=user_id, is_deleted=False)
        )
    except ChatSession.DoesNotExist:
        return None

def get_session_messages(session_id: str) -> QuerySet:
    
    return Message.objects.filter(session_id=session_id).order_by('created_at')

def get_context_window(session_id: str) -> List[dict]:
    
    messages = list(
        Message.objects
        .filter(session_id=session_id, role__in=['user', 'assistant'])
        .order_by('-created_at')
        .values('role', 'content')[:CONTEXT_WINDOW]
    )
    return list(reversed(messages))
