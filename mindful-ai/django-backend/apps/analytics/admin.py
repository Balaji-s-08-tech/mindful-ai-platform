
from django.contrib import admin
from apps.analytics.models import UserAnalytics

@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    
    list_display = [
        'user', 'total_sessions', 'total_messages',
        'most_common_emotion', 'last_session_at', 'updated_at',
    ]
    search_fields = ['user__email', 'user__name']
    ordering = ['-updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user']
