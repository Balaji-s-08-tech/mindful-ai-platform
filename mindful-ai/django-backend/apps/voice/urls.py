
from django.urls import path

from .views import ProcessVoiceView, TextToSpeechView, TranscribeView

app_name = "voice"

urlpatterns = [

    path("transcribe", TranscribeView.as_view(), name="transcribe"),

    path("tts", TextToSpeechView.as_view(), name="tts"),

    path("process", ProcessVoiceView.as_view(), name="process"),
]
