
from __future__ import annotations

from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from apps.users.models import PasswordResetToken, User

def get_user_by_email(email: str) -> Optional[User]:
    
    try:
        return User.objects.get(email=email.lower(), is_deleted=False)
    except User.DoesNotExist:
        return None

def get_user_by_id(user_id: str) -> Optional[User]:
    
    try:
        return User.objects.get(id=user_id, is_deleted=False)
    except (User.DoesNotExist, ValueError):
        return None

def get_active_users() -> QuerySet:
    
    return User.objects.filter(is_active=True, is_deleted=False)

def get_valid_reset_token(token: str) -> Optional[PasswordResetToken]:
    
    try:
        return PasswordResetToken.objects.select_related('user').get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
    except PasswordResetToken.DoesNotExist:
        return None

def get_user_reset_tokens(user: User) -> QuerySet:
    
    return PasswordResetToken.objects.filter(user=user).order_by('-created_at')
