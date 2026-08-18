
from __future__ import annotations

from typing import Any, Dict

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.users.models import User
from apps.users.validators import validate_password_strength

class UserSerializer(serializers.ModelSerializer):
    
    preferences = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'preferences',
            'last_active_at',
            'created_at',
        ]
        read_only_fields = fields

    def get_preferences(self, obj: User) -> Dict[str, Any]:
        
        return obj.default_preferences

class RegisterSerializer(serializers.Serializer):
    
    name = serializers.CharField(
        max_length=100,
        help_text='Display name of the new user.',
    )
    email = serializers.EmailField(
        help_text='Email address used as the login identifier.',
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Plain-text password (will be hashed).',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Must match the password field.',
    )

    def validate_email(self, value: str) -> str:
        
        value = value.lower().strip()
        if User.objects.filter(email=value, is_deleted=False).exists():
            raise serializers.ValidationError(
                'A user with this email address already exists.'
            )
        return value

    def validate_password(self, value: str) -> str:
        
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message) from exc
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'Password fields did not match.'}
            )
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        
        from apps.users.services import create_user

        validated_data.pop('password_confirm')
        return create_user(
            name=validated_data['name'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

class LoginSerializer(serializers.Serializer):
    
    email = serializers.EmailField(
        help_text='Registered email address.',
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Account password.',
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        
        from apps.users.services import authenticate_user
        from apps.common.exceptions import ApplicationError

        email: str = attrs.get('email', '').lower()
        password: str = attrs.get('password', '')

        try:
            user = authenticate_user(email=email, password=password)
        except ApplicationError as exc:
            raise serializers.ValidationError({'non_field_errors': exc.message}) from exc

        attrs['user'] = user
        return attrs

class UpdateProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['name', 'preferences']

    def validate_name(self, value: str) -> str:
        
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name may not be blank.')
        return value

    def validate_preferences(self, value: Dict[str, Any]) -> Dict[str, Any]:
        
        allowed_keys = {'voiceEnabled', 'cameraEnabled', 'ttsProvider'}
        unknown = set(value.keys()) - allowed_keys
        if unknown:
            raise serializers.ValidationError(
                f'Unknown preference key(s): {", ".join(sorted(unknown))}.'
            )

        bool_keys = {'voiceEnabled', 'cameraEnabled'}
        for key in bool_keys & set(value.keys()):
            if not isinstance(value[key], bool):
                raise serializers.ValidationError(
                    f'Preference "{key}" must be a boolean.'
                )

        if 'ttsProvider' in value and not isinstance(value['ttsProvider'], str):
            raise serializers.ValidationError(
                'Preference "ttsProvider" must be a string.'
            )

        return value

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        
        from apps.users.services import update_profile

        return update_profile(user=instance, data=validated_data)

class ChangePasswordSerializer(serializers.Serializer):
    
    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='The user\'s existing password.',
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Desired new password.',
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Must match new_password.',
    )

    def validate_current_password(self, value: str) -> str:
        
        user: User = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value: str) -> str:
        
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message) from exc
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError(
                {'new_password_confirm': 'New passwords did not match.'}
            )
        return attrs

class ForgotPasswordSerializer(serializers.Serializer):
    
    email = serializers.EmailField(
        help_text='Email address associated with the account to reset.',
    )

    def validate_email(self, value: str) -> str:
        
        return value.lower().strip()

class ResetPasswordSerializer(serializers.Serializer):
    
    token = serializers.CharField(
        help_text='The one-time reset token from the reset email.',
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='The desired new password.',
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Must match new_password.',
    )

    def validate_new_password(self, value: str) -> str:
        
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message) from exc
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError(
                {'new_password_confirm': 'Passwords did not match.'}
            )
        return attrs
