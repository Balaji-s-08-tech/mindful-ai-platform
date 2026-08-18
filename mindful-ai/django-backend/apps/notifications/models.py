
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

class NotificationType(models.TextChoices):
    
    PUSH = "push", "Push Notification"
    EMAIL = "email", "Email"
    IN_APP = "in_app", "In-App Notification"
    SMS = "sms", "SMS"

class Notification(models.Model):
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the notification.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
        help_text="The user who receives this notification.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Short notification title or subject line.",
    )
    body = models.TextField(
        help_text="Full body text of the notification.",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.IN_APP,
        db_index=True,
        help_text="Channel through which the notification is delivered.",
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True once the user has acknowledged the notification.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="UTC timestamp when this notification was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="UTC timestamp when this notification was last updated.",
    )

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read"], name="notif_user_read_idx"),
            models.Index(fields=["user", "notification_type"], name="notif_user_type_idx"),
        ]

    def __str__(self) -> str:
        
        return f"[{self.notification_type}] {self.title} → {self.user}"

    def mark_as_read(self) -> None:
        
        self.is_read = True
        self.save(update_fields=["is_read", "updated_at"])
