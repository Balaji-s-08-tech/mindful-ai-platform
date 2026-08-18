
import uuid
from django.db import models

class TimeStampedModel(models.Model):
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text='Unique identifier for this record (UUID v4).',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when this record was created (UTC).',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when this record was last updated (UTC).',
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Soft-delete flag. When True the record is treated as deleted.',
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self) -> None:
        
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def restore(self) -> None:
        
        self.is_deleted = False
        self.save(update_fields=['is_deleted', 'updated_at'])
