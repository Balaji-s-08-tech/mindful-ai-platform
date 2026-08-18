
import asyncio
import json
import logging
from typing import Any

from django.http import StreamingHttpResponse
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import ChatSession, Message
from apps.chat.selectors import (
    get_session_messages,
    get_session_with_messages,
    get_user_sessions,
)
from apps.chat.serializers import (
    ChatSessionDetailSerializer,
    ChatSessionSerializer,
    CreateSessionSerializer,
    MessageSerializer,
    SendMessageSerializer,
)
from apps.chat.services import create_session, delete_session, send_message
from apps.common.exceptions import ApplicationError
from apps.common.mixins import StandardResponseMixin
from apps.common.pagination import StandardPagination
from apps.common.permissions import IsOwner
from apps.common.responses import (
    created_response,
    error_response,
    no_content_response,
    success_response,
)

logger = logging.getLogger(__name__)

class SessionListCreateView(StandardResponseMixin, APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='List chat sessions',
        description=(
            'Returns a paginated list of all non-deleted chat sessions '
            'belonging to the authenticated user, ordered by last activity.'
        ),
        responses={
            200: OpenApiResponse(description='Paginated session list'),
            401: OpenApiResponse(description='Unauthenticated'),
        },
        tags=['Chat'],
    )
    def get(self, request: Request) -> Response:
        
        sessions_qs = get_user_sessions(str(request.user.id))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(sessions_qs, request)
        serializer = ChatSessionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary='Create chat session',
        description='Create a new chat session for the authenticated user.',
        request=CreateSessionSerializer,
        responses={
            201: OpenApiResponse(description='Session created'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Unauthenticated'),
        },
        tags=['Chat'],
    )
    def post(self, request: Request) -> Response:
        
        serializer = CreateSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = create_session(
                user=request.user,
                title=serializer.validated_data.get('title', 'New Conversation'),
            )
        except Exception as exc:
            logger.exception('[SessionListCreateView] Unexpected error: %s', exc)
            return error_response(
                message='Failed to create session.',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return created_response(
            data=ChatSessionSerializer(session).data,
            message='Session created successfully.',
        )

class SessionDetailView(StandardResponseMixin, APIView):
    
    permission_classes = [IsAuthenticated, IsOwner]

    def _get_session_or_404(self, session_id: str, user_id: str) -> ChatSession:
        
        session = get_session_with_messages(session_id, user_id)
        if not session:
            raise ApplicationError('Session not found.', status_code=404)
        return session

    @extend_schema(
        summary='Retrieve chat session',
        description='Returns full session detail with the last 50 messages.',
        responses={
            200: OpenApiResponse(description='Session detail'),
            401: OpenApiResponse(description='Unauthenticated'),
            403: OpenApiResponse(description='Forbidden — not the owner'),
            404: OpenApiResponse(description='Session not found'),
        },
        parameters=[
            OpenApiParameter(name='session_id', location='path', description='Session UUID', type=str),
        ],
        tags=['Chat'],
    )
    def get(self, request: Request, session_id: str) -> Response:
        
        try:
            session = self._get_session_or_404(str(session_id), str(request.user.id))
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)

        serializer = ChatSessionDetailSerializer(session)
        return success_response(
            data=serializer.data,
            message='Session retrieved successfully.',
        )

    @extend_schema(
        summary='Delete chat session',
        description='Soft-delete a chat session. The record is retained for auditing.',
        responses={
            200: OpenApiResponse(description='Session deleted'),
            401: OpenApiResponse(description='Unauthenticated'),
            403: OpenApiResponse(description='Forbidden — not the owner'),
            404: OpenApiResponse(description='Session not found'),
        },
        parameters=[
            OpenApiParameter(name='session_id', location='path', description='Session UUID', type=str),
        ],
        tags=['Chat'],
    )
    def delete(self, request: Request, session_id: str) -> Response:
        
        try:
            delete_session(str(session_id), str(request.user.id))
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)
        except Exception as exc:
            logger.exception('[SessionDetailView] Delete error: %s', exc)
            return error_response(
                message='Failed to delete session.',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return no_content_response(message='Session deleted successfully.')

class MessageListCreateView(StandardResponseMixin, APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='List session messages',
        description='Returns a paginated list of messages for a session, oldest-first.',
        responses={
            200: OpenApiResponse(description='Paginated messages'),
            401: OpenApiResponse(description='Unauthenticated'),
            403: OpenApiResponse(description='Forbidden'),
            404: OpenApiResponse(description='Session not found'),
        },
        parameters=[
            OpenApiParameter(name='session_id', location='path', description='Session UUID', type=str),
        ],
        tags=['Chat'],
    )
    def get(self, request: Request, session_id: str) -> Response:
        
        from apps.chat.selectors import get_session_by_id

        session = get_session_by_id(str(session_id), str(request.user.id))
        if not session:
            return error_response(message='Session not found.', status_code=status.HTTP_404_NOT_FOUND)

        messages_qs = get_session_messages(str(session_id))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(messages_qs, request)
        serializer = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary='Send a message',
        description=(
            'Send a user message to the AI and receive the full AI reply. '
            'For streaming responses use the /stream endpoint instead.'
        ),
        request=SendMessageSerializer,
        responses={
            201: OpenApiResponse(description='User + AI messages returned'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Unauthenticated'),
            404: OpenApiResponse(description='Session not found'),
            503: OpenApiResponse(description='AI service unavailable'),
        },
        parameters=[
            OpenApiParameter(name='session_id', location='path', description='Session UUID', type=str),
        ],
        tags=['Chat'],
    )
    def post(self, request: Request, session_id: str) -> Response:
        
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = send_message(
                session_id=str(session_id),
                user=request.user,
                content=serializer.validated_data['content'],
                emotion_context=serializer.validated_data.get('emotion_context'),
            )
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)
        except Exception as exc:
            logger.exception('[MessageListCreateView] Unexpected error: %s', exc)
            return error_response(
                message='Failed to process message.',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return created_response(
            data={
                'user_message': MessageSerializer(result['user_message']).data,
                'ai_message': MessageSerializer(result['ai_message']).data,
                'meta': result['meta'],
            },
            message='Message sent successfully.',
        )

class StreamMessageView(StandardResponseMixin, APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Stream AI response (SSE)',
        description=(
            'Send a user message and stream the AI reply as Server-Sent Events. '
            'Each event is a JSON object with either a "token" key (streaming) '
            'or "done": true with meta information (final event).'
        ),
        request=SendMessageSerializer,
        responses={
            200: OpenApiResponse(description='SSE stream — text/event-stream'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Unauthenticated'),
            404: OpenApiResponse(description='Session not found'),
        },
        parameters=[
            OpenApiParameter(name='session_id', location='path', description='Session UUID', type=str),
        ],
        tags=['Chat'],
    )
    def post(self, request: Request, session_id: str) -> StreamingHttpResponse:
        
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():

            return error_response(
                message='Validation error.',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        content: str = serializer.validated_data['content']
        emotion_context: dict = serializer.validated_data.get('emotion_context') or {}
        user = request.user
        sid = str(session_id)

        def event_stream():
            
            from apps.chat.selectors import get_context_window, get_session_by_id
            from apps.chat.models import ChatSession, Message

            session = get_session_by_id(sid, str(user.id))
            if not session:
                yield f'data: {json.dumps({"error": "Session not found"})}\n\n'
                return

            user_message = Message.objects.create(
                session=session,
                role=Message.Role.USER,
                content=content,
                emotion_context=emotion_context,
            )
            if session.message_count == 0:
                session.generate_title(content)

            yield f'data: {json.dumps({"start": True, "userMessageId": str(user_message.id)})}\n\n'

            history = get_context_window(sid)
            full_content: list = []

            async def run_stream():
                
                try:
                    from apps.ai.input_normalizer import build_unified_context
                    from apps.ai.services import generate_response_stream

                    unified_ctx = build_unified_context(
                        message=content,
                        user_id=str(user.id),
                        input_type='text',
                        emotion_data=emotion_context,
                        history=history,
                        session_id=sid,
                    )

                    tokens: list = []

                    async def on_token(token: str) -> None:
                        tokens.append(token)
                        full_content.append(token)

                    result = await generate_response_stream(unified_ctx, on_token)
                    return tokens, result
                except Exception as exc:
                    logger.error('[StreamMessageView] AI stream error: %s', exc)
                    return None, None

            loop = asyncio.new_event_loop()
            try:
                tokens_collected, ai_result = loop.run_until_complete(run_stream())
            finally:
                loop.close()

            if tokens_collected is None:
                yield f'data: {json.dumps({"error": "AI service unavailable"})}\n\n'
                return

            for token in tokens_collected:
                yield f'data: {json.dumps({"token": token})}\n\n'

            response_text = ai_result.content if ai_result and ai_result.content else ''.join(full_content)
            ai_message = Message.objects.create(
                session=session,
                role=Message.Role.ASSISTANT,
                content=response_text,
                tokens=ai_result.tokens if ai_result else None,
                model=ai_result.model if ai_result else '',
            )

            session.message_count += 2
            combined = emotion_context.get('combined')
            if combined:
                summary = session.emotion_summary or {'dominant': None, 'progression': []}
                summary.setdefault('progression', []).append(combined)
                summary['dominant'] = combined
                session.emotion_summary = summary
            session.save(update_fields=['message_count', 'emotion_summary', 'title', 'updated_at'])

            meta = {
                'provider': ai_result.provider if ai_result else None,
                'latency_ms': ai_result.latency_ms if ai_result else None,
                'is_crisis': ai_result.is_crisis if ai_result else False,
            }
            yield (
                f'data: {json.dumps({"done": True, "aiMessageId": str(ai_message.id), "meta": meta})}\n\n'
            )

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
