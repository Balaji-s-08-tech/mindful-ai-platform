
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.cache import never_cache
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

@never_cache
def health_check(request) -> JsonResponse:
    
    return JsonResponse(
        {
            "success": True,
            "message": "OK",
            "data": {
                "status": "healthy",
                "service": "MindfulAI Django API",
            },
        },
        status=200,
    )

urlpatterns = [

    path("admin/", admin.site.urls),

    path("api/health", health_check, name="health-check"),

    path("api/auth/", include("apps.users.urls")),

    path("api/users/", include("apps.users.profile_urls")),

    path("api/chat/", include("apps.chat.urls")),

    path("api/voice/", include("apps.voice.urls")),

    path("api/emotion/", include("apps.emotion.urls")),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
