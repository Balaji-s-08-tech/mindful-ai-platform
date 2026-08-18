
from django.urls import path
from apps.chat import views

urlpatterns = [

    path('sessions', views.SessionListCreateView.as_view(), name='chat-sessions'),
    path('sessions/<uuid:session_id>', views.SessionDetailView.as_view(), name='chat-session-detail'),

    path('sessions/<uuid:session_id>/messages', views.MessageListCreateView.as_view(), name='chat-messages'),

    path('sessions/<uuid:session_id>/messages/stream', views.StreamMessageView.as_view(), name='chat-stream'),
]
