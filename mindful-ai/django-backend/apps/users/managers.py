
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager
from django.db import models

if TYPE_CHECKING:
    from apps.users.models import User

class UserManager(BaseUserManager):
    
    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        **extra_fields: Any,
    ) -> 'User':
        
        if not email:
            raise ValueError('An email address is required to create a user.')
        if not name:
            raise ValueError('A name is required to create a user.')

        email = self.normalize_email(email).lower()
        user: 'User' = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        name: str,
        **extra_fields: Any,
    ) -> 'User':
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, name, **extra_fields)

    def get_active(self) -> models.QuerySet:
        
        return self.filter(is_active=True, is_deleted=False)
