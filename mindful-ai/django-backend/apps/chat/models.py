
import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel

class ChatSession(TimeStampedModel):
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        db_index=True,
        help_text='The user who owns this conversation session.',
    )
    title = models.CharField(
        max_length=200,
        default='New Conversation',
        help_text='Display title for the conversation, auto-generated from the first message.',
    )
    emotion_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Aggregated emotion data for this session. '
            'Schema: {"dominant": str | null, "progression": [str, ...]}'
        ),
    )
    message_count = models.PositiveIntegerField(
        default=0,
        help_text='Denormalised count of user + assistant messages in this session.',
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether this session is currently active.',
    )

    class Meta:
        db_table = 'chat_sessions'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='chat_session_user_created_idx'),
            models.Index(fields=['user', 'is_active'], name='chat_session_user_active_idx'),
        ]
        ordering = ['-created_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def __str__(self) -> str:
        
        return f'Session {self.id} — {self.user}: {self.title}'

    def generate_title(self, first_message: str) -> None:
        
        max_len = 60
        if len(first_message) > max_len:
            self.title = first_message[:max_len] + '\u2026'
        else:
            self.title = first_message

class Message(models.Model):
    
    class Role(models.TextChoices):
        
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for this message (UUID v4).',
    )
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True,
        help_text='The parent conversation session.',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        help_text='Sender role: user, assistant, or system.',
    )
    content = models.TextField(
        max_length=10_000,
        help_text='Text body of the message (max 10 000 characters).',
    )
    emotion_context = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Emotion snapshot at the time this message was sent. '
            'Keys: facial, voice, text, combined.'
        ),
    )
    tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Token count consumed by the LLM to produce this message (AI messages only).',
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='LLM model identifier used to generate this message (AI messages only).',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when this message was created (UTC).',
    )

    class Meta:
        db_table = 'chat_messages'
        indexes = [
            models.Index(fields=['session', 'created_at'], name='chat_msg_session_created_idx'),
            models.Index(fields=['session', 'role'], name='chat_msg_session_role_idx'),
        ]
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self) -> str:
        
        return f'[{self.role}] {self.content[:50]}'
