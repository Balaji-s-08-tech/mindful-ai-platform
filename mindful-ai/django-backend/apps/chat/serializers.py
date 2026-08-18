
from __future__ import annotations

from typing import Any, Dict, List

from rest_framework import serializers

from apps.chat.models import ChatSession, Message

class MessageSerializer(serializers.ModelSerializer):
    
    session_id = serializers.UUIDField(source='session.id', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'session_id',
            'role',
            'content',
            'emotion_context',
            'tokens',
            'model',
            'created_at',
        ]
        read_only_fields = fields

class ChatSessionSerializer(serializers.ModelSerializer):
    
    user_id = serializers.UUIDField(source='user.id', read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'user_id',
            'title',
            'emotion_summary',
            'message_count',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

class ChatSessionDetailSerializer(serializers.ModelSerializer):
    
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'user_id',
            'title',
            'emotion_summary',
            'message_count',
            'is_active',
            'is_deleted',
            'created_at',
            'updated_at',
            'messages',
        ]
        read_only_fields = fields

    def get_messages(self, obj: ChatSession) -> List[Dict[str, Any]]:
        
        if hasattr(obj, 'prefetched_messages'):
            msgs = obj.prefetched_messages
        else:
            msgs = (
                obj.messages
                .order_by('created_at')
                .select_related()[:50]
            )
        return MessageSerializer(msgs, many=True).data

class SendMessageSerializer(serializers.Serializer):
    
    content = serializers.CharField(
        min_length=1,
        max_length=10_000,
        trim_whitespace=True,
        help_text='The user message text. Required; 1–10 000 characters.',
    )
    emotion_context = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
        default=dict,
        help_text=(
            'Optional emotion snapshot from frontend sensors. '
            'Keys: facial, voice, text, combined.'
        ),
    )

    def validate_content(self, value: str) -> str:
        
        if not value.strip():
            raise serializers.ValidationError('Message content may not be blank.')
        return value.strip()

    def validate_emotion_context(self, value: Dict[str, Any]) -> Dict[str, Any]:
        
        if not isinstance(value, dict):
            raise serializers.ValidationError('emotion_context must be a JSON object.')
        return value

class CreateSessionSerializer(serializers.Serializer):
    
    title = serializers.CharField(
        max_length=200,
        required=False,
        default='New Conversation',
        trim_whitespace=True,
        help_text='Optional display title for the new session.',
    )

    def validate_title(self, value: str) -> str:
        
        stripped = value.strip()
        return stripped if stripped else 'New Conversation'
