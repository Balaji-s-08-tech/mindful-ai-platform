
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

def send_password_reset_email(
    user_email: str,
    reset_token: str,
    reset_url: str,
) -> None:
    
    logger.info(
        '[TASK] Password reset email queued | recipient=%s | url=%s',
        user_email,
        reset_url,
    )

def send_welcome_email(user_email: str, user_name: str) -> None:
    
    logger.info(
        '[TASK] Welcome email queued | recipient=%s | name=%s',
        user_email,
        user_name,
    )
