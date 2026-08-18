
from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional

from django.utils import timezone

from apps.common.exceptions import ApplicationError
from apps.users.models import PasswordResetToken, User
from apps.users.selectors import (
    get_user_by_email,
    get_user_by_id,
    get_user_reset_tokens,
    get_valid_reset_token,
)

logger = logging.getLogger(__name__)

RESET_TOKEN_EXPIRY_HOURS: int = 1

def create_user(name: str, email: str, password: str) -> User:
    
    email = email.lower().strip()

    if User.objects.filter(email=email).exists():
        raise ApplicationError(
            message='A user with this email address already exists.',
            status_code=409,
        )

    user: User = User.objects.create_user(
        email=email,
        password=password,
        name=name.strip(),
    )

    logger.info('User created: %s (id=%s)', user.email, user.id)

    from apps.users.tasks import send_welcome_email

    send_welcome_email(user_email=user.email, user_name=user.name)

    return user

def authenticate_user(email: str, password: str) -> User:
    
    email = email.lower().strip()
    user: Optional[User] = get_user_by_email(email)

    if user is None:
        raise ApplicationError(
            message='Invalid email or password.',
            status_code=401,
        )

    if not user.is_active:
        raise ApplicationError(
            message='This account has been deactivated. Please contact support.',
            status_code=403,
        )

    if not user.check_password(password):
        raise ApplicationError(
            message='Invalid email or password.',
            status_code=401,
        )

    user.last_active_at = timezone.now()
    user.save(update_fields=['last_active_at'])

    logger.info('User authenticated: %s (id=%s)', user.email, user.id)
    return user

def change_password(user: User, current_password: str, new_password: str) -> None:
    
    if not user.check_password(current_password):
        raise ApplicationError(
            message='Current password is incorrect.',
            status_code=400,
        )

    user.set_password(new_password)
    user.save(update_fields=['password', 'updated_at'])

    get_user_reset_tokens(user).update(is_used=True)

    logger.info('Password changed for user: %s (id=%s)', user.email, user.id)

def initiate_password_reset(email: str) -> PasswordResetToken:
    
    email = email.lower().strip()
    user: Optional[User] = get_user_by_email(email)

    if user is None:
        logger.info(
            'Password reset requested for unknown email: %s (no-op)', email
        )

        dummy = PasswordResetToken.__new__(PasswordResetToken)
        return dummy

    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

    raw_token: str = secrets.token_hex(32)
    reset_token: PasswordResetToken = PasswordResetToken.objects.create(
        user=user,
        token=raw_token,
        expires_at=timezone.now() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS),
    )

    from django.conf import settings
    from apps.users.tasks import send_password_reset_email

    frontend_url: str = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_url: str = f'{frontend_url}/reset-password?token={raw_token}'

    send_password_reset_email(
        user_email=user.email,
        reset_token=raw_token,
        reset_url=reset_url,
    )

    logger.info(
        'Password reset token created for user: %s (id=%s)', user.email, user.id
    )
    return reset_token

def confirm_password_reset(token: str, new_password: str) -> None:
    
    reset_token: Optional[PasswordResetToken] = get_valid_reset_token(token)

    if reset_token is None:
        raise ApplicationError(
            message='This password reset link is invalid or has expired.',
            status_code=400,
        )

    user: User = reset_token.user

    reset_token.is_used = True
    reset_token.save(update_fields=['is_used'])

    user.set_password(new_password)
    user.save(update_fields=['password', 'updated_at'])

    logger.info(
        'Password reset completed for user: %s (id=%s)', user.email, user.id
    )

def update_profile(user: User, data: Dict[str, Any]) -> User:
    
    update_fields = ['updated_at']

    if 'name' in data:
        user.name = data['name'].strip()
        update_fields.append('name')

    if 'preferences' in data:

        merged = {**user.preferences, **data['preferences']}
        user.preferences = merged
        update_fields.append('preferences')

    user.save(update_fields=update_fields)
    logger.info('Profile updated for user: %s (id=%s)', user.email, user.id)
    return user

def deactivate_account(user: User) -> None:
    
    user.soft_delete()

    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

    logger.info('Account deactivated for user: %s (id=%s)', user.email, user.id)
