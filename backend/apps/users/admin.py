"""
Django Admin configuration for User Management (S1).

Provides comprehensive admin interface for managing users,
roles, and security settings with audit trail support.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import User, Role, UserRole, MFADevice


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with EDMS-specific fields."""
    
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'department', 'is_validated', 'mfa_enabled',
        'is_active', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_validated',
        'mfa_enabled', 'department', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    readonly_fields = ('uuid', 'date_joined', 'last_login', 'password_changed_at')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('EDMS Information'), {
            'fields': (
                'uuid', 'employee_id', 'department', 'position',
                'manager', 'phone_number'
            ),
        }),
        (_('Validation & Security'), {
            'fields': (
                'is_validated', 'validation_date', 'validation_expiry',
                'mfa_enabled', 'failed_login_attempts', 'account_locked_until',
                'password_changed_at'
            ),
        }),
        (_('Audit Information'), {
            'fields': ('created_by', 'metadata'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('manager', 'created_by')


class UserRoleInline(admin.TabularInline):
    """Inline for managing user roles."""
    model = UserRole
    extra = 0
    readonly_fields = ('uuid', 'assigned_at', 'assigned_by')
    fields = (
        'role', 'assigned_at', 'assigned_by', 'expires_at',
        'is_active', 'assignment_reason'
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin for managing EDMS roles."""
    
    list_display = (
        'name', 'module', 'permission_level', 'is_active',
        'is_system_role', 'user_count', 'created_at'
    )
    list_filter = ('module', 'permission_level', 'is_active', 'is_system_role')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'user_count')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'module', 'permission_level')
        }),
        (_('Inheritance'), {
            'fields': ('inherits_from',),
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_system_role'),
        }),
        (_('Audit Information'), {
            'fields': ('uuid', 'created_at', 'updated_at', 'created_by', 'metadata'),
        }),
    )
    
    inlines = [UserRoleInline]
    
    def user_count(self, obj):
        """Return the number of users assigned to this role."""
        count = obj.role_users.filter(is_active=True).count()
        url = reverse('admin:users_userrole_changelist') + f'?role__id__exact={obj.id}'
        return format_html('<a href="{}">{} users</a>', url, count)
    user_count.short_description = _('Active Users')
    user_count.admin_order_field = 'role_users__count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('role_users')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin for managing user role assignments."""
    
    list_display = (
        'user', 'role', 'assigned_at', 'assigned_by',
        'expires_at', 'is_active'
    )
    list_filter = (
        'is_active', 'role__module', 'role__permission_level',
        'assigned_at', 'expires_at'
    )
    search_fields = (
        'user__username', 'user__email', 'role__name',
        'assignment_reason', 'revocation_reason'
    )
    readonly_fields = ('uuid', 'assigned_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role')
        }),
        (_('Assignment Details'), {
            'fields': (
                'assigned_at', 'assigned_by', 'assignment_reason',
                'expires_at', 'is_active'
            ),
        }),
        (_('Revocation Details'), {
            'fields': ('revoked_at', 'revoked_by', 'revocation_reason'),
        }),
        (_('Additional Information'), {
            'fields': ('uuid', 'metadata'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'role', 'assigned_by', 'revoked_by'
        )


@admin.register(MFADevice)
class MFADeviceAdmin(admin.ModelAdmin):
    """Admin for managing MFA devices."""
    
    list_display = (
        'user', 'name', 'device_type', 'is_active',
        'is_verified', 'last_used_at', 'created_at'
    )
    list_filter = ('device_type', 'is_active', 'is_verified', 'created_at')
    search_fields = ('user__username', 'name', 'phone_number', 'email_address')
    readonly_fields = ('uuid', 'created_at', 'verified_at', 'last_used_at', 'usage_count')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'device_type', 'name')
        }),
        (_('Configuration'), {
            'fields': ('phone_number', 'email_address'),
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_verified', 'verified_at'),
        }),
        (_('Usage Statistics'), {
            'fields': ('last_used_at', 'usage_count'),
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_at', 'metadata'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# UserSessionAdmin moved to audit app