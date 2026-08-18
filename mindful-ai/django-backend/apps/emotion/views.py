
from __future__ import annotations

import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.responses import error_response, success_response

from .services import detect_emotion, get_emotion_service_health

logger = logging.getLogger(__name__)

class EmotionHealthView(APIView):
    
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Service health status"),
        },
        summary="Check emotion service health",
        tags=["Emotion"],
    )
    def get(self, request: Request) -> Response:
        
        health = get_emotion_service_health()
        logger.info("[EmotionHealthView] Health: %s", health)
        return success_response(
            message="Emotion service health retrieved.",
            data=health,
            status_code=status.HTTP_200_OK,
        )

class DetectEmotionView(APIView):
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "format": "binary",
                        "description": "Image file (JPEG / PNG / WEBP).",
                    }
                },
                "required": ["image"],
            }
        },
        responses={
            200: OpenApiResponse(description="Emotion detection result"),
            400: OpenApiResponse(description="No image provided"),
            503: OpenApiResponse(description="Emotion service unavailable"),
        },
        summary="Detect emotion from an image",
        tags=["Emotion"],
    )
    def post(self, request: Request) -> Response:
        
        image_file = request.FILES.get("image")
        if not image_file:
            return error_response(
                message="No image file provided. Send the image under the 'image' key.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        allowed_content_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        content_type: str = getattr(image_file, "content_type", "image/jpeg")
        if content_type.lower() not in allowed_content_types:
            return error_response(
                message=(
                    f"Unsupported image type '{content_type}'. "
                    "Accepted types: JPEG, PNG, WEBP."
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_data: bytes = image_file.read()
            result = detect_emotion(image_data=image_data, content_type=content_type)
            logger.info(
                "[DetectEmotionView] Success – user=%s emotion=%s",
                request.user.id,
                result.get("emotion", "unknown"),
            )
            return success_response(
                message="Emotion detected successfully.",
                data=result,
                status_code=status.HTTP_200_OK,
            )
        except ApplicationError as exc:
            logger.warning("[DetectEmotionView] ApplicationError: %s", exc)
            return error_response(
                message=str(exc),
                status_code=exc.status_code,
            )
        except Exception as exc:
            logger.exception("[DetectEmotionView] Unexpected error: %s", exc)
            return error_response(
                message="An unexpected error occurred during emotion detection.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
