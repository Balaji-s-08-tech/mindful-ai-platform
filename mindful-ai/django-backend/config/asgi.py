
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

django.setup()

from django.core.asgi import get_asgi_application

import socketio

from apps.chat.consumers import create_socketio_app

django_app = get_asgi_application()

sio_app: socketio.AsyncServer = create_socketio_app()

application = socketio.ASGIApp(
    socketio_server=sio_app,
    other_asgi_app=django_app,
    socketio_path="socket.io",
)
