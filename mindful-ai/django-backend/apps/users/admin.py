
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import PasswordResetToken, User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    
    list_display = [
        'email',
        'name',
        'is_active',
        'is_staff',
        'is_deleted',
        'last_active_at',
        'created_at',
    ]
    list_display_links = ['email', 'name']
    list_filter = ['is_active', 'is_staff', 'is_deleted', 'is_superuser']
    search_fields = ['name', 'email']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_active_at']

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal info', {'fields': ('name', 'preferences', 'last_active_at')}),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'is_deleted',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'name',
                    'password1',
                    'password2',
                    'is_staff',
                    'is_superuser',
                    'is_active',
                ),
            },
        ),
    )

    USERNAME_FIELD_OVERRIDE = 'email'

    def get_form(self, request, obj=None, **kwargs):
        
        form = super().get_form(request, obj, **kwargs)
        if 'username' in form.base_fields:
            form.base_fields['username'].label = 'Email'
        return form

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    
    list_display = [
        'user',
        'token_preview',
        'is_used',
        'created_at',
        'expires_at',
    ]
    list_filter = ['is_used']
    search_fields = ['user__email', 'user__name', 'token']
    readonly_fields = ['id', 'user', 'token', 'created_at', 'expires_at', 'is_used']
    ordering = ['-created_at']

    def token_preview(self, obj: PasswordResetToken) -> str:
        
        return f'{obj.token[:8]}…'

    token_preview.short_description = 'Token (preview)'

    def has_add_permission(self, request) -> bool:
        
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        
        return False
