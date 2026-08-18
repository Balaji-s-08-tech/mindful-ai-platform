
from __future__ import annotations

import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.exceptions import ApplicationError
from apps.common.responses import (
    created_response,
    error_response,
    no_content_response,
    success_response,
)
from apps.users.models import User
from apps.users.permissions import IsNotAuthenticated
from apps.users.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)
from apps.users.services import (
    authenticate_user,
    change_password,
    confirm_password_reset,
    create_user,
    deactivate_account,
    initiate_password_reset,
    update_profile,
)

logger = logging.getLogger(__name__)

def _build_token_pair(user: User) -> dict:
    
    refresh: RefreshToken = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

@extend_schema(tags=['Auth'])
class RegisterView(APIView):
    
    permission_classes = [IsNotAuthenticated]

    @extend_schema(
        summary='Register a new user',
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description='User registered successfully.'),
            400: OpenApiResponse(description='Validation error.'),
            409: OpenApiResponse(description='Email already registered.'),
        },
    )
    def post(self, request: Request) -> Response:
        
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user: User = serializer.save()
        except ApplicationError as exc:
            return error_response(
                message=exc.message,
                status_code=exc.status_code,
            )

        tokens = _build_token_pair(user)
        user_data = UserSerializer(user).data

        return created_response(
            data={'user': user_data, 'tokens': tokens},
            message='Account created successfully.',
        )

@extend_schema(tags=['Auth'])
class LoginView(APIView):
    
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Login with email and password',
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='Login successful.'),
            400: OpenApiResponse(description='Validation error.'),
            401: OpenApiResponse(description='Invalid credentials.'),
        },
    )
    def post(self, request: Request) -> Response:
        
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Invalid credentials.',
                errors=serializer.errors,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        user: User = serializer.validated_data['user']
        tokens = _build_token_pair(user)
        user_data = UserSerializer(user).data

        return success_response(
            data={'user': user_data, 'tokens': tokens},
            message='Login successful.',
        )

@extend_schema(tags=['Auth'])
class RefreshTokenView(TokenRefreshView):
    
@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Logout and blacklist the refresh token',
        responses={
            200: OpenApiResponse(description='Logout successful.'),
            400: OpenApiResponse(description='Invalid or missing refresh token.'),
        },
    )
    def post(self, request: Request) -> Response:
        
        refresh_token: str = request.data.get('refresh', '')
        if not refresh_token:
            return error_response(
                message='Refresh token is required.',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return error_response(
                message='Invalid or expired refresh token.',
                errors={'detail': str(exc)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(message='Logout successful.')

@extend_schema(tags=['Auth'])
class MeView(RetrieveAPIView):
    
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        summary='Get current authenticated user',
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description='Authentication required.'),
        },
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        
        serializer = UserSerializer(request.user)
        return success_response(
            data={'user': serializer.data},
            message='User profile retrieved.',
        )

@extend_schema(tags=['Auth'])
class ForgotPasswordView(APIView):
    
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Request a password reset email',
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description='Reset email dispatched (if address exists).'),
            400: OpenApiResponse(description='Validation error.'),
        },
    )
    def post(self, request: Request) -> Response:
        
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
            )

        try:
            initiate_password_reset(email=serializer.validated_data['email'])
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)
        except Exception:
            logger.exception('Unexpected error during password reset initiation.')

            pass

        return success_response(
            message=(
                'If an account with that email exists, '
                'a password reset link has been sent.'
            )
        )

@extend_schema(tags=['Auth'])
class ResetPasswordView(APIView):
    
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Reset password using a one-time token',
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password reset successfully.'),
            400: OpenApiResponse(description='Invalid token or validation error.'),
        },
    )
    def post(self, request: Request) -> Response:
        
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
            )

        try:
            confirm_password_reset(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password'],
            )
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)

        return success_response(
            message='Password has been reset successfully. You may now log in.'
        )

@extend_schema(tags=['Users'])
class UserProfileView(RetrieveUpdateAPIView):
    
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateProfileSerializer

    @extend_schema(
        summary='Get the authenticated user\'s profile',
        responses={200: UserSerializer},
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        
        serializer = UserSerializer(request.user)
        return success_response(
            data={'user': serializer.data},
            message='Profile retrieved.',
        )

    @extend_schema(
        summary='Update the authenticated user\'s profile',
        request=UpdateProfileSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request: Request, *args, **kwargs) -> Response:
        
        serializer = UpdateProfileSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
            )

        try:
            updated_user: User = serializer.save()
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)

        return success_response(
            data={'user': UserSerializer(updated_user).data},
            message='Profile updated successfully.',
        )

    def put(self, request: Request, *args, **kwargs) -> Response:
        
        return error_response(
            message='PUT is not supported. Use PATCH for partial updates.',
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

@extend_schema(tags=['Users'])
class ChangePasswordView(APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Change the authenticated user\'s password',
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password changed successfully.'),
            400: OpenApiResponse(description='Validation error or wrong current password.'),
        },
    )
    def post(self, request: Request) -> Response:
        
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return error_response(
                message='Validation error.',
                errors=serializer.errors,
            )

        try:
            change_password(
                user=request.user,
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password'],
            )
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)

        return success_response(message='Password changed successfully.')

@extend_schema(tags=['Users'])
class DeleteAccountView(APIView):
    
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Delete (deactivate) the authenticated user\'s account',
        responses={
            200: OpenApiResponse(description='Account deleted successfully.'),
        },
    )
    def delete(self, request: Request) -> Response:
        
        try:
            deactivate_account(user=request.user)
        except ApplicationError as exc:
            return error_response(message=exc.message, status_code=exc.status_code)

        return no_content_response(message='Account deleted successfully.')
