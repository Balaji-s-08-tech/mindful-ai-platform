
from django.urls import path

from .views import DetectEmotionView, EmotionHealthView

app_name = "emotion"

urlpatterns = [

    path("health", EmotionHealthView.as_view(), name="health"),

    path("detect", DetectEmotionView.as_view(), name="detect"),
]
