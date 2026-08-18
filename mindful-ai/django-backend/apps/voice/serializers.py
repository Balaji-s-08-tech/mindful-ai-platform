
from rest_framework import serializers

class TranscribeSerializer(serializers.Serializer):
    
    audio = serializers.FileField(
        required=True,
        help_text="Audio file to transcribe (mp3, wav, webm, m4a, etc.).",
    )

class TextToSpeechSerializer(serializers.Serializer):
    
    text = serializers.CharField(
        required=True,
        max_length=5000,
        help_text="Text to synthesise into speech (max 5 000 characters).",
    )

class ProcessVoiceSerializer(serializers.Serializer):
    
    audio = serializers.FileField(
        required=True,
        help_text="Audio file containing the user's spoken message.",
    )
    emotion_context = serializers.DictField(
        required=False,
        default=dict,
        help_text="Optional emotion context dict (e.g. {'emotion': 'sad', 'confidence': 0.9}).",
    )
    session_id = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=100,
        help_text="Optional chat session ID to continue an existing conversation.",
    )
    tts_enabled = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If true, the AI response will also be synthesised to audio.",
    )
