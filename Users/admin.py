from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'is_verified', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'national_id']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Health System Fields', {
            'fields': ('role', 'phone_number', 'national_id', 'is_verified')
        }),
    )