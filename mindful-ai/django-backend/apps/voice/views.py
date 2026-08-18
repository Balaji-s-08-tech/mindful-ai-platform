
from __future__ import annotations

import logging

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.responses import error_response, success_response

from .serializers import ProcessVoiceSerializer, TextToSpeechSerializer, TranscribeSerializer
from .services import process_voice_pipeline, text_to_speech, transcribe_audio

logger = logging.getLogger(__name__)

class TranscribeView(APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TranscribeSerializer,
        responses={
            200: OpenApiResponse(description="Transcription successful"),
            400: OpenApiResponse(description="Validation error"),
            502: OpenApiResponse(description="Upstream service error"),
        },
        summary="Transcribe audio to text",
        tags=["Voice"],
    )
    def post(self, request: Request) -> HttpResponse:
        
        serializer = TranscribeSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request data.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        audio_file = serializer.validated_data["audio"]

        try:
            transcript = transcribe_audio(audio_file)
            logger.info(
                "[TranscribeView] Success – user=%s len=%d",
                request.user.id,
                len(transcript),
            )
            return success_response(
                message="Audio transcribed successfully.",
                data={"transcript": transcript},
                status_code=status.HTTP_200_OK,
            )
        except ApplicationError as exc:
            logger.warning("[TranscribeView] ApplicationError: %s", exc)
            return error_response(
                message=str(exc),
                status_code=exc.status_code,
            )
        except Exception as exc:
            logger.exception("[TranscribeView] Unexpected error: %s", exc)
            return error_response(
                message="An unexpected error occurred during transcription.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class TextToSpeechView(APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TextToSpeechSerializer,
        responses={
            200: OpenApiResponse(description="Audio file (audio/mpeg)"),
            400: OpenApiResponse(description="Validation error"),
            502: OpenApiResponse(description="Upstream service error"),
        },
        summary="Convert text to speech",
        tags=["Voice"],
    )
    def post(self, request: Request) -> HttpResponse:
        
        serializer = TextToSpeechSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request data.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        text: str = serializer.validated_data["text"]

        try:
            audio_bytes = text_to_speech(text)
            logger.info(
                "[TextToSpeechView] Success – user=%s bytes=%d",
                request.user.id,
                len(audio_bytes),
            )
            response = HttpResponse(audio_bytes, content_type="audio/mpeg")
            response["Content-Disposition"] = 'attachment; filename="speech.mp3"'
            response["Content-Length"] = str(len(audio_bytes))
            return response
        except ApplicationError as exc:
            logger.warning("[TextToSpeechView] ApplicationError: %s", exc)
            return error_response(
                message=str(exc),
                status_code=exc.status_code,
            )
        except Exception as exc:
            logger.exception("[TextToSpeechView] Unexpected error: %s", exc)
            return error_response(
                message="An unexpected error occurred during text-to-speech conversion.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ProcessVoiceView(APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ProcessVoiceSerializer,
        responses={
            200: OpenApiResponse(description="Pipeline result"),
            400: OpenApiResponse(description="Validation error"),
            422: OpenApiResponse(description="No speech detected"),
            502: OpenApiResponse(description="Upstream service error"),
        },
        summary="Process voice through the full AI pipeline",
        tags=["Voice"],
    )
    def post(self, request: Request) -> HttpResponse:
        
        serializer = ProcessVoiceSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request data.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        audio_file = validated["audio"]
        emotion_context = validated.get("emotion_context") or {}
        session_id: str = validated.get("session_id", "")
        tts_enabled: bool = validated.get("tts_enabled", False)

        try:
            result = process_voice_pipeline(
                audio_file=audio_file,
                user=request.user,
                session_id=session_id or None,
                emotion_context=emotion_context or None,
                tts_enabled=tts_enabled,
            )
            logger.info(
                "[ProcessVoiceView] Success – user=%s session=%s",
                request.user.id,
                session_id,
            )
            return success_response(
                message="Voice processed successfully.",
                data=result,
                status_code=status.HTTP_200_OK,
            )
        except ApplicationError as exc:
            logger.warning("[ProcessVoiceView] ApplicationError: %s", exc)
            return error_response(
                message=str(exc),
                status_code=exc.status_code,
            )
        except Exception as exc:
            logger.exception("[ProcessVoiceView] Unexpected error: %s", exc)
            return error_response(
                message="An unexpected error occurred during voice processing.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
