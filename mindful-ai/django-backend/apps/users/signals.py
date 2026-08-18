
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

def get_user_model_lazy():
    
    from apps.users.models import User

    return User

@receiver(post_save, sender='users.User')
def log_user_creation(
    sender,
    instance,
    created: bool,
    **kwargs,
) -> None:
    
    if created:
        logger.info(
            'New user account created | id=%s | email=%s | name=%s',
            instance.id,
            instance.email,
            instance.name,
        )
