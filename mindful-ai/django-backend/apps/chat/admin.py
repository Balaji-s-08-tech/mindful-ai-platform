
from django.contrib import admin
from apps.chat.models import ChatSession, Message

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    
    list_display = [
        'id', 'user', 'title', 'message_count',
        'is_active', 'is_deleted', 'created_at', 'updated_at',
    ]
    list_filter = ['is_active', 'is_deleted', 'created_at']
    search_fields = ['user__email', 'user__name', 'title', 'id']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'message_count']
    raw_id_fields = ['user']

    fieldsets = (
        ('Session Info', {
            'fields': ('id', 'user', 'title', 'is_active', 'is_deleted'),
        }),
        ('Emotion', {
            'fields': ('emotion_summary',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('message_count', 'created_at', 'updated_at'),
        }),
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    
    list_display = ['id', 'session', 'role', 'short_content', 'tokens', 'model', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['session__id', 'content', 'model']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['session']

    def short_content(self, obj: Message) -> str:
        
        return obj.content[:80] + '…' if len(obj.content) > 80 else obj.content

    short_content.short_description = 'Content'
