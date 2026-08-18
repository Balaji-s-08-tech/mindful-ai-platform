
import os
import time
import logging
from typing import Optional

import socketio

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=os.getenv('FRONTEND_URL', 'http://localhost:3000'),
    ping_timeout=60000,
    ping_interval=25000,
    logger=False,
    engineio_logger=False,
)

CONTEXT_WINDOW = 20

async def _authenticate(token: str):
    
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        from apps.users.models import User

        access = AccessToken(token)
        user_id = access.get('user_id')
        user = await User.objects.aget(id=user_id, is_active=True, is_deleted=False)
        return user
    except Exception as exc:
        logger.warning('[SocketIO] Auth failed: %s', exc)
        return None

async def _load_history(session_id: str) -> list:
    
    from apps.chat.models import Message

    rows = []
    async for msg in (
        Message.objects
        .filter(session_id=session_id, role__in=['user', 'assistant'])
        .order_by('-created_at')
        .values('role', 'content')[:CONTEXT_WINDOW]
    ):
        rows.append(msg)
    return list(reversed(rows))

async def _fetch_tts(text: str) -> Optional[str]:
    
    import base64
    import httpx

    api_key = os.getenv('ELEVENLABS_API_KEY')
    voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')

    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
                json={
                    'text': text[:2000],
                    'model_id': 'eleven_turbo_v2',
                    'voice_settings': {
                        'stability': 0.75,
                        'similarity_boost': 0.85,
                        'style': 0.3,
                        'use_speaker_boost': True,
                    },
                },
                headers={
                    'xi-api-key': api_key,
                    'Content-Type': 'application/json',
                    'Accept': 'audio/mpeg',
                },
            )
            response.raise_for_status()
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as exc:
        logger.warning('[SocketIO] TTS failed: %s', exc)
        return None

@sio.event
async def connect(sid: str, environ: dict, auth: dict):
    
    token = (auth or {}).get('token')
    if not token:
        logger.warning('[SocketIO] Rejected connection: no token (sid=%s)', sid)
        raise ConnectionRefusedError('Authentication required')

    user = await _authenticate(token)
    if not user:
        raise ConnectionRefusedError('Invalid or expired token')

    await sio.save_session(sid, {
        'user_id': str(user.id),
        'user_name': user.name,
    })
    await sio.enter_room(sid, f'user:{user.id}')
    logger.info('[SocketIO] Connected: %s (%s)', user.name, sid)

@sio.event
async def disconnect(sid: str):
    
    session = await sio.get_session(sid)
    logger.info('[SocketIO] Disconnected: %s (%s)', session.get('user_name', '?'), sid)

@sio.event
async def join_session(sid: str, session_id: str):
    
    await sio.enter_room(sid, f'session:{session_id}')

@sio.event
async def leave_session(sid: str, session_id: str):
    
    await sio.leave_room(sid, f'session:{session_id}')

@sio.event
async def typing_start(sid: str, data: dict):
    
    session = await sio.get_session(sid)
    await sio.emit(
        'user_typing',
        {'userId': session['user_id'], 'name': session['user_name']},
        room=f'session:{data.get("sessionId")}',
        skip_sid=sid,
    )

@sio.event
async def typing_stop(sid: str, data: dict):
    
    session = await sio.get_session(sid)
    await sio.emit(
        'user_stopped_typing',
        {'userId': session['user_id']},
        room=f'session:{data.get("sessionId")}',
        skip_sid=sid,
    )

@sio.event
async def emotion_detected(sid: str, data: dict):
    
    session = await sio.get_session(sid)
    await sio.emit(
        'emotion_update',
        {**data, 'timestamp': int(time.time() * 1000)},
        room=f'user:{session["user_id"]}',
    )

@sio.event
async def ai_stream_request(sid: str, data: dict):
    
    from apps.chat.models import ChatSession, Message
    from apps.ai.input_normalizer import build_unified_context
    from apps.ai.services import generate_response_stream

    session_data = await sio.get_session(sid)
    user_id = session_data['user_id']
    session_id = data.get('sessionId')
    content = (data.get('content') or '').strip()

    if not session_id or not content:
        return

    try:

        try:
            chat_session = await ChatSession.objects.aget(
                id=session_id, user_id=user_id, is_deleted=False
            )
        except ChatSession.DoesNotExist:
            await sio.emit(
                'ai_stream_error',
                {'sessionId': session_id, 'message': 'Session not found'},
                room=sid,
            )
            return

        emotion_context = data.get('emotionContext') or {}

        user_message = await Message.objects.acreate(
            session=chat_session,
            role=Message.Role.USER,
            content=content,
            emotion_context=emotion_context,
        )

        if chat_session.message_count == 0:
            chat_session.generate_title(content)

        await sio.emit(
            'ai_message_start',
            {
                'sessionId': session_id,
                'userMessage': {
                    'id': str(user_message.id),
                    'content': content,
                    'role': 'user',
                    'createdAt': user_message.created_at.isoformat(),
                },
            },
            room=sid,
        )

        history = await _load_history(session_id)
        unified_ctx = build_unified_context(
            message=content,
            user_id=user_id,
            input_type='text',
            emotion_data=emotion_context,
            history=history,
            session_id=session_id,
        )

        full_content = ''

        async def on_token(token: str) -> None:
            nonlocal full_content
            full_content += token
            await sio.emit('ai_token', {'sessionId': session_id, 'token': token}, room=sid)

        async def on_crisis(crisis_text: str) -> None:
            await sio.emit('ai_crisis', {'sessionId': session_id, 'content': crisis_text}, room=sid)

        ai_result = await generate_response_stream(unified_ctx, on_token, on_crisis)

        ai_message = await Message.objects.acreate(
            session=chat_session,
            role=Message.Role.ASSISTANT,
            content=ai_result.content or full_content,
            tokens=ai_result.tokens,
            model=ai_result.model,
        )

        chat_session.message_count += 2
        if emotion_context.get('combined'):
            summary = chat_session.emotion_summary or {'dominant': None, 'progression': []}
            summary.setdefault('progression', []).append(emotion_context['combined'])
            chat_session.emotion_summary = summary
        await chat_session.asave(
            update_fields=['message_count', 'emotion_summary', 'title', 'updated_at']
        )

        await sio.emit(
            'ai_message_end',
            {
                'sessionId': session_id,
                'aiMessage': {
                    'id': str(ai_message.id),
                    'content': ai_message.content,
                    'role': 'assistant',
                    'createdAt': ai_message.created_at.isoformat(),
                },
                'meta': {
                    'provider': ai_result.provider,
                    'latencyMs': ai_result.latency_ms,
                    'isCrisis': ai_result.is_crisis,
                },
            },
            room=sid,
        )

        logger.info(
            '[SocketIO] ai_stream_request done — provider=%s, latency=%dms',
            ai_result.provider,
            ai_result.latency_ms,
        )

    except Exception as exc:
        logger.error('[SocketIO] ai_stream_request error: %s', exc)
        await sio.emit(
            'ai_stream_error',
            {'sessionId': session_id, 'message': 'Failed to generate response'},
            room=sid,
        )

@sio.event
async def voice_to_ai(sid: str, data: dict):
    
    from apps.chat.models import ChatSession, Message
    from apps.ai.input_normalizer import build_unified_context
    from apps.ai.services import generate_response_stream

    session_data = await sio.get_session(sid)
    user_id = session_data['user_id']
    session_id = data.get('sessionId')
    transcript = (data.get('transcript') or '').strip()

    if not session_id or not transcript:
        return

    try:
        try:
            chat_session = await ChatSession.objects.aget(
                id=session_id, user_id=user_id, is_deleted=False
            )
        except ChatSession.DoesNotExist:
            return

        emotion_context = data.get('emotionContext') or {}
        request_tts = data.get('requestTTS', True)

        await Message.objects.acreate(
            session=chat_session,
            role=Message.Role.USER,
            content=transcript,
            emotion_context=emotion_context,
        )

        await sio.emit(
            'ai_message_start',
            {'sessionId': session_id, 'inputType': 'voice'},
            room=sid,
        )

        history = await _load_history(session_id)
        unified_ctx = build_unified_context(
            message=transcript,
            user_id=user_id,
            input_type='voice',
            emotion_data=emotion_context,
            history=history,
            raw_transcript=transcript,
            session_id=session_id,
        )

        full_content = ''

        async def on_token(token: str) -> None:
            nonlocal full_content
            full_content += token
            await sio.emit('ai_token', {'sessionId': session_id, 'token': token}, room=sid)

        ai_result = await generate_response_stream(unified_ctx, on_token)
        response_text = ai_result.content or full_content

        ai_message = await Message.objects.acreate(
            session=chat_session,
            role=Message.Role.ASSISTANT,
            content=response_text,
            tokens=ai_result.tokens,
            model=ai_result.model,
        )

        chat_session.message_count += 2
        await chat_session.asave(update_fields=['message_count', 'updated_at'])

        await sio.emit(
            'ai_message_end',
            {
                'sessionId': session_id,
                'aiMessage': {
                    'id': str(ai_message.id),
                    'content': response_text,
                    'role': 'assistant',
                },
                'meta': {'provider': ai_result.provider},
            },
            room=sid,
        )

        if request_tts and response_text:
            audio_b64 = await _fetch_tts(response_text)
            await sio.emit(
                'ai_audio_response',
                {
                    'sessionId': session_id,
                    'text': response_text,
                    'audioBase64': audio_b64,
                },
                room=sid,
            )

    except Exception as exc:
        logger.error('[SocketIO] voice_to_ai error: %s', exc)
        await sio.emit(
            'ai_stream_error',
            {'sessionId': session_id, 'message': 'Voice processing failed'},
            room=sid,
        )

@sio.event
async def ping(sid: str):
    
    await sio.emit('pong', {'timestamp': int(time.time() * 1000)}, room=sid)

def create_socketio_app() -> socketio.AsyncServer:
    
    return sio
