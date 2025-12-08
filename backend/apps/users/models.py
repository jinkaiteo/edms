"""
User Management Models (S1)

This module contains user management models for the EDMS system,
including custom user model, roles, permissions, and MFA devices.
"""

import uuid
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Supports 21 CFR Part 11 compliance with additional fields
    for audit trail and security requirements.
    """
    
    # Additional identification fields
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        """Override save to handle empty employee_id consistently."""
        # Convert empty string to None to avoid unique constraint violations
        if self.employee_id == '':
            self.employee_id = None
        super().save(*args, **kwargs)
    
    # Contact information
    phone_number = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    department = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    manager = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subordinates'
    )
    
    # Security and compliance fields
    is_validated = models.BooleanField(default=False)
    validation_date = models.DateTimeField(null=True, blank=True)
    validation_expiry = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)
    
    # MFA and security
    mfa_enabled = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_users'
    )
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'users'
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"
    
    @property
    def display_name(self):
        """Return display name for the user."""
        return self.get_full_name() or self.username
    
    def has_edms_permission(self, permission_name, module=None):
        """Check if user has specific EDMS permission."""
        # Implementation for EDMS-specific permission checking
        return self.has_perm(f'edms.{permission_name}')


class Role(models.Model):
    """
    EDMS Role model for role-based access control.
    
    Defines roles that can be assigned to users for different
    modules and permission levels.
    """
    
    PERMISSION_LEVELS = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('review', 'Review'),
        ('approve', 'Approve'),
        ('admin', 'Admin'),
    ]
    
    MODULE_CHOICES = [
        ('O1', 'Electronic Document Management (O1)'),
        ('S1', 'User Management (S1)'),
        ('S2', 'Audit Trail (S2)'),
        ('S3', 'Scheduler (S3)'),
        ('S4', 'Backup and Health Check (S4)'),
        ('S5', 'Workflow Settings (S5)'),
        ('S6', 'Placeholder Management (S6)'),
        ('S7', 'App Settings (S7)'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=2, choices=MODULE_CHOICES)
    permission_level = models.CharField(max_length=10, choices=PERMISSION_LEVELS)
    
    # Role hierarchy and inheritance
    inherits_from = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='inherited_by'
    )
    
    # Status and lifecycle
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(default=False)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_roles'
    )
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'users'
        db_table = 'roles'
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        unique_together = ['module', 'permission_level']
        ordering = ['module', 'permission_level']
    
    def __str__(self):
        return f"{self.get_module_display()} - {self.get_permission_level_display()}"


class UserRole(models.Model):
    """
    Many-to-many relationship between Users and Roles.
    
    Tracks role assignments with audit information
    and expiration dates for compliance.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    
    # Assignment details
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_roles'
    )
    
    # Expiration and status
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='revoked_roles'
    )
    
    # Reason and metadata
    assignment_reason = models.TextField(blank=True)
    revocation_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'users'
        db_table = 'user_roles'
        verbose_name = _('User Role Assignment')
        verbose_name_plural = _('User Role Assignments')
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class MFADevice(models.Model):
    """
    Multi-Factor Authentication device model.
    
    Supports TOTP and backup codes for enhanced security
    as required for regulated environments.
    """
    
    DEVICE_TYPES = [
        ('totp', 'TOTP Authenticator'),
        ('backup', 'Backup Codes'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    name = models.CharField(max_length=100)
    
    # Device configuration
    secret_key = models.CharField(max_length=200, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email_address = models.EmailField(blank=True)
    
    # Status and usage tracking
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Security metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'users'
        db_table = 'mfa_devices'
        verbose_name = _('MFA Device')
        verbose_name_plural = _('MFA Devices')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.get_device_type_display()})"


# UserSession moved to audit app to avoid conflicts