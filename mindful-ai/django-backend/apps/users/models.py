
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.users.managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier (UUID v4).',
    )
    name = models.CharField(
        max_length=100,
        help_text='Display name of the user.',
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text='Email address used as the login identifier.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user account should be considered active.',
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the Django admin.',
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Soft-delete flag. When True the account is treated as deleted.',
    )

    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'User preference overrides stored as JSON. '
            'Keys: voiceEnabled, cameraEnabled, ttsProvider.'
        ),
    )
    last_active_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of the user\'s last activity (UTC).',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the account was created (UTC).',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp of the last account update (UTC).',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        
        return f'{self.name} <{self.email}>'

    def get_full_name(self) -> str:
        
        return self.name

    def get_short_name(self) -> str:
        
        return self.name.split()[0] if self.name else self.email

    def soft_delete(self) -> None:
        
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=['is_deleted', 'is_active', 'updated_at'])

    @property
    def default_preferences(self) -> dict:
        
        defaults: dict = {
            'voiceEnabled': True,
            'cameraEnabled': False,
            'ttsProvider': 'browser',
        }
        return {**defaults, **self.preferences}

class PasswordResetToken(models.Model):
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier (UUID v4).',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        help_text='The user who requested this password reset.',
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text='Cryptographically random token string.',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the token was generated (UTC).',
    )
    expires_at = models.DateTimeField(
        help_text='Datetime after which the token is no longer valid (UTC).',
    )
    is_used = models.BooleanField(
        default=False,
        help_text='True once the token has been consumed to reset a password.',
    )

    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'

    def __str__(self) -> str:
        
        return f'Reset token for {self.user.email} (used={self.is_used})'

    @property
    def is_valid(self) -> bool:
        
        return not self.is_used and self.expires_at > timezone.now()
