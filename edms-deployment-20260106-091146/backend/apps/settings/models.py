"""
Settings Models for EDMS S7 Module.

Models for system configuration, application settings,
and customization options.
"""

import uuid
import json
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class SystemConfiguration(models.Model):
    """
    System Configuration model for global system settings.
    
    Stores system-wide configuration parameters
    that affect application behavior and appearance.
    """
    
    SETTING_TYPES = [
        ('STRING', 'String Value'),
        ('INTEGER', 'Integer Value'),
        ('FLOAT', 'Float Value'),
        ('BOOLEAN', 'Boolean Value'),
        ('JSON', 'JSON Object'),
        ('FILE_PATH', 'File Path'),
        ('URL', 'URL'),
        ('EMAIL', 'Email Address'),
        ('COLOR', 'Color Code'),
    ]
    
    CATEGORIES = [
        ('SYSTEM', 'System Settings'),
        ('SECURITY', 'Security Settings'),
        ('APPEARANCE', 'Appearance Settings'),
        ('NOTIFICATION', 'Notification Settings'),
        ('INTEGRATION', 'Integration Settings'),
        ('WORKFLOW', 'Workflow Settings'),
        ('BACKUP', 'Backup Settings'),
        ('AUDIT', 'Audit Settings'),
        ('DOCUMENT', 'Document Settings'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique configuration key"
    )
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Setting details
    category = models.CharField(max_length=20, choices=CATEGORIES)
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES)
    
    # Value storage
    value = models.TextField(
        blank=True,
        help_text="Current setting value"
    )
    default_value = models.TextField(
        blank=True,
        help_text="Default setting value"
    )
    
    # Validation and constraints
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Validation rules for the setting value"
    )
    allowed_values = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed values (for choice fields)"
    )
    
    # Metadata
    is_sensitive = models.BooleanField(
        default=False,
        help_text="Whether this setting contains sensitive information"
    )
    requires_restart = models.BooleanField(
        default=False,
        help_text="Whether changing this setting requires application restart"
    )
    is_user_configurable = models.BooleanField(
        default=True,
        help_text="Whether users can modify this setting"
    )
    
    # Change tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='updated_settings'
    )
    
    class Meta:
        app_label = "settings"
        db_table = 'system_configurations'
        verbose_name = _('System Configuration')
        verbose_name_plural = _('System Configurations')
        ordering = ['category', 'display_name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['key']),
            models.Index(fields=['setting_type']),
        ]
    
    def __str__(self):
        return f"{self.key}: {self.display_name}"
    
    def clean(self):
        """Validate setting value against type and rules."""
        super().clean()
        
        if self.value:
            try:
                self._validate_value(self.value)
            except ValueError as e:
                raise ValidationError({'value': str(e)})
    
    def get_typed_value(self):
        """Get the setting value converted to appropriate Python type."""
        if not self.value:
            return self._convert_value(self.default_value) if self.default_value else None
        
        return self._convert_value(self.value)
    
    def set_value(self, value, user: User = None):
        """Set setting value with type conversion and validation."""
        # Convert to string for storage
        if self.setting_type == 'JSON':
            self.value = json.dumps(value) if not isinstance(value, str) else value
        elif self.setting_type == 'BOOLEAN':
            self.value = 'true' if value in [True, 'true', 'True', '1', 1] else 'false'
        else:
            self.value = str(value)
        
        # Validate
        self._validate_value(self.value)
        
        # Update metadata
        self.updated_by = user
        self.save()
    
    def _convert_value(self, value_str: str):
        """Convert string value to appropriate Python type."""
        if not value_str:
            return None
        
        if self.setting_type == 'INTEGER':
            return int(value_str)
        elif self.setting_type == 'FLOAT':
            return float(value_str)
        elif self.setting_type == 'BOOLEAN':
            return value_str.lower() in ['true', '1', 'yes', 'on']
        elif self.setting_type == 'JSON':
            return json.loads(value_str)
        else:
            return value_str
    
    def _validate_value(self, value_str: str):
        """Validate value against type and rules."""
        if not value_str and self.validation_rules.get('required', False):
            raise ValueError("Value is required")
        
        if not value_str:
            return  # Empty values are valid for non-required fields
        
        # Type validation
        try:
            typed_value = self._convert_value(value_str)
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid {self.setting_type} value: {str(e)}")
        
        # Choice validation
        if self.allowed_values and typed_value not in self.allowed_values:
            raise ValueError(f"Value must be one of: {self.allowed_values}")
        
        # Additional validation rules
        rules = self.validation_rules
        
        if self.setting_type in ['INTEGER', 'FLOAT']:
            if 'min_value' in rules and typed_value < rules['min_value']:
                raise ValueError(f"Value must be at least {rules['min_value']}")
            if 'max_value' in rules and typed_value > rules['max_value']:
                raise ValueError(f"Value must be at most {rules['max_value']}")
        
        if self.setting_type == 'STRING':
            if 'min_length' in rules and len(typed_value) < rules['min_length']:
                raise ValueError(f"Value must be at least {rules['min_length']} characters")
            if 'max_length' in rules and len(typed_value) > rules['max_length']:
                raise ValueError(f"Value must be at most {rules['max_length']} characters")


class UICustomization(models.Model):
    """
    UI Customization model for application appearance settings.
    
    Stores customization settings for themes, logos, banners,
    and other UI elements.
    """
    
    CUSTOMIZATION_TYPES = [
        ('LOGO', 'Company Logo'),
        ('BANNER', 'Page Banner'),
        ('THEME', 'Color Theme'),
        ('FONT', 'Font Settings'),
        ('LAYOUT', 'Layout Configuration'),
        ('DASHBOARD', 'Dashboard Settings'),
        ('MENU', 'Menu Configuration'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    customization_type = models.CharField(max_length=20, choices=CUSTOMIZATION_TYPES)
    
    # Customization data
    settings_data = models.JSONField(
        default=dict,
        help_text="Customization settings and values"
    )
    
    # File uploads (for logos, banners, etc.)
    uploaded_file = models.FileField(
        upload_to='customizations/',
        null=True, blank=True,
        help_text="Uploaded file for this customization"
    )
    
    # Status and application
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default customization"
    )
    
    # User and department targeting
    target_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='ui_customizations',
        help_text="Specific users this customization applies to"
    )
    target_departments = models.JSONField(
        default=list,
        blank=True,
        help_text="Departments this customization applies to"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_customizations'
    )
    
    class Meta:
        app_label = "settings"
        db_table = 'ui_customizations'
        verbose_name = _('UI Customization')
        verbose_name_plural = _('UI Customizations')
        ordering = ['customization_type', 'name']
        indexes = [
            models.Index(fields=['customization_type', 'status']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.customization_type})"


class FeatureToggle(models.Model):
    """
    Feature Toggle model for feature flag management.
    
    Enables/disables features dynamically without code deployment.
    """
    
    TOGGLE_TYPES = [
        ('RELEASE', 'Release Toggle'),
        ('EXPERIMENT', 'Experiment Toggle'),
        ('OPERATIONAL', 'Operational Toggle'),
        ('PERMISSION', 'Permission Toggle'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique feature toggle key"
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Toggle configuration
    toggle_type = models.CharField(max_length=20, choices=TOGGLE_TYPES)
    is_enabled = models.BooleanField(
        default=False,
        help_text="Whether the feature is currently enabled"
    )
    
    # Conditional enabling
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conditions for enabling this feature"
    )
    
    # User and role targeting
    target_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='feature_toggles',
        help_text="Users who have access to this feature"
    )
    target_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="Roles that have access to this feature"
    )
    
    # Percentage rollout
    rollout_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text="Percentage of users to enable feature for (0-100)"
    )
    
    # Lifecycle
    start_date = models.DateTimeField(
        null=True, blank=True,
        help_text="When to start enabling this feature"
    )
    end_date = models.DateTimeField(
        null=True, blank=True,
        help_text="When to stop enabling this feature"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_feature_toggles'
    )
    
    class Meta:
        app_label = "settings"
        db_table = 'feature_toggles'
        verbose_name = _('Feature Toggle')
        verbose_name_plural = _('Feature Toggles')
        ordering = ['name']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['toggle_type', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.key} ({'ON' if self.is_enabled else 'OFF'})"
    
    def is_enabled_for_user(self, user: User) -> bool:
        """Check if feature is enabled for a specific user."""
        # Check if feature is globally disabled
        if not self.is_enabled:
            return False
        
        # Check date range
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        # Check user targeting
        if self.target_users.filter(id=user.id).exists():
            return True
        
        # Check role targeting
        if self.target_roles:
            user_roles = user.user_roles.filter(
                role__name__in=self.target_roles,
                is_active=True
            )
            if user_roles.exists():
                return True
        
        # Check percentage rollout
        if self.rollout_percentage > 0:
            # Use user ID hash for consistent rollout
            user_hash = hash(str(user.id) + self.key) % 100
            return user_hash < self.rollout_percentage
        
        return False


class ConfigurationHistory(models.Model):
    """
    Configuration History model for tracking setting changes.
    
    Maintains audit trail of all configuration changes
    for compliance and rollback purposes.
    """
    
    CHANGE_TYPES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('RESET', 'Reset to Default'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    configuration = models.ForeignKey(
        SystemConfiguration,
        on_delete=models.CASCADE,
        related_name='change_history'
    )
    
    # Change details
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    change_reason = models.TextField(blank=True)
    
    # Context
    changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='configuration_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        app_label = "settings"
        db_table = 'configuration_history'
        verbose_name = _('Configuration History')
        verbose_name_plural = _('Configuration History')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['configuration', 'changed_at']),
            models.Index(fields=['changed_by', 'changed_at']),
        ]
    
    def __str__(self):
        return f"{self.configuration.key} - {self.change_type} - {self.changed_at}"


class NotificationTemplate(models.Model):
    """
    Notification Template model for system notifications.
    
    Defines templates for various types of system notifications
    including email, SMS, and dashboard notifications.
    """
    
    TEMPLATE_TYPES = [
        ('EMAIL', 'Email Template'),
        ('SMS', 'SMS Template'),
        ('DASHBOARD', 'Dashboard Notification'),
        ('PUSH', 'Push Notification'),
    ]
    
    EVENT_TYPES = [
        ('DOCUMENT_APPROVED', 'Document Approved'),
        ('DOCUMENT_REJECTED', 'Document Rejected'),
        ('WORKFLOW_ASSIGNED', 'Workflow Task Assigned'),
        ('WORKFLOW_OVERDUE', 'Workflow Task Overdue'),
        ('DOCUMENT_EFFECTIVE', 'Document Became Effective'),
        ('DOCUMENT_OBSOLETE', 'Document Became Obsolete'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('BACKUP_COMPLETED', 'Backup Completed'),
        ('BACKUP_FAILED', 'Backup Failed'),
        ('USER_ACCOUNT_CREATED', 'User Account Created'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template configuration
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    
    # Template content
    subject_template = models.CharField(
        max_length=200,
        blank=True,
        help_text="Subject line template (for email/SMS)"
    )
    body_template = models.TextField(
        help_text="Message body template"
    )
    html_template = models.TextField(
        blank=True,
        help_text="HTML template (for email)"
    )
    
    # Template variables
    available_variables = models.JSONField(
        default=list,
        help_text="List of available template variables"
    )
    
    # Status and versioning
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default='1.0')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_notification_templates'
    )
    
    class Meta:
        app_label = "settings"
        db_table = 'notification_templates'
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        ordering = ['template_type', 'event_type']
        constraints = [
            models.UniqueConstraint(
                fields=['template_type', 'event_type', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_template'
            ),
        ]
        indexes = [
            models.Index(fields=['template_type', 'event_type']),
            models.Index(fields=['is_active', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_type} - {self.event_type})"
    
    def render_template(self, context: dict) -> dict:
        """Render template with provided context variables."""
        from django.template import Template, Context
        
        try:
            # Render subject
            subject = ''
            if self.subject_template:
                subject_tmpl = Template(self.subject_template)
                subject = subject_tmpl.render(Context(context))
            
            # Render body
            body_tmpl = Template(self.body_template)
            body = body_tmpl.render(Context(context))
            
            # Render HTML if available
            html = ''
            if self.html_template:
                html_tmpl = Template(self.html_template)
                html = html_tmpl.render(Context(context))
            
            return {
                'subject': subject,
                'body': body,
                'html': html
            }
            
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")