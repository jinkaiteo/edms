"""
Placeholder Management Models for EDMS S6 Module.

Models for template management, placeholder definitions,
and document generation capabilities.
"""

import uuid
import json
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class PlaceholderDefinition(models.Model):
    """
    Placeholder Definition model for template processing.
    
    Defines placeholders that can be used in document templates
    with their data sources and formatting rules.
    """
    
    PLACEHOLDER_TYPES = [
        ('DOCUMENT', 'Document Metadata'),
        ('USER', 'User Information'),
        ('WORKFLOW', 'Workflow Data'),
        ('SYSTEM', 'System Information'),
        ('DATE', 'Date/Time'),
        ('CUSTOM', 'Custom Field'),
        ('CONDITIONAL', 'Conditional Logic'),
    ]
    
    DATA_SOURCES = [
        ('DOCUMENT_MODEL', 'Document Model Field'),
        ('USER_MODEL', 'User Model Field'),
        ('WORKFLOW_MODEL', 'Workflow Model Field'),
        ('SYSTEM_CONFIG', 'System Configuration'),
        ('COMPUTED', 'Computed Value'),
        ('JSONB_FIELD', 'JSONB Metadata Field'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z][A-Z0-9_]*$',
                message='Placeholder name must be uppercase with underscores only'
            )
        ],
        help_text="Placeholder name (e.g., DOC_NUMBER, AUTHOR_NAME)"
    )
    display_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Type and source configuration
    placeholder_type = models.CharField(max_length=20, choices=PLACEHOLDER_TYPES)
    data_source = models.CharField(max_length=30, choices=DATA_SOURCES)
    source_field = models.CharField(
        max_length=100,
        help_text="Model field name or configuration key"
    )
    
    # Formatting configuration
    format_string = models.CharField(
        max_length=100,
        blank=True,
        help_text="Python format string (e.g., '{:.2f}' for decimals)"
    )
    date_format = models.CharField(
        max_length=50,
        blank=True,
        default='%Y-%m-%d',
        help_text="Date format string (e.g., %Y-%m-%d)"
    )
    
    # Default and validation
    default_value = models.TextField(
        blank=True,
        help_text="Default value if source data is not available"
    )
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Validation rules for placeholder values"
    )
    
    # Processing configuration
    is_active = models.BooleanField(default=True)
    requires_permission = models.CharField(
        max_length=50,
        blank=True,
        help_text="Permission level required to access this placeholder"
    )
    cache_duration = models.PositiveIntegerField(
        default=0,
        help_text="Cache duration in seconds (0 = no cache)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_placeholders'
    )
    
    class Meta:
        db_table = 'placeholder_definitions'
        verbose_name = _('Placeholder Definition')
        verbose_name_plural = _('Placeholder Definitions')
        ordering = ['name']
        indexes = [
            models.Index(fields=['placeholder_type']),
            models.Index(fields=['data_source']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{{{{ {self.name} }}}}"
    
    def clean(self):
        """Validate placeholder definition."""
        super().clean()
        
        # Validate format string
        if self.format_string:
            try:
                self.format_string.format('test')
            except (ValueError, KeyError):
                raise ValidationError({
                    'format_string': 'Invalid format string syntax'
                })
        
        # Validate date format
        if self.date_format and self.placeholder_type == 'DATE':
            try:
                timezone.now().strftime(self.date_format)
            except ValueError:
                raise ValidationError({
                    'date_format': 'Invalid date format string'
                })
    
    def get_template_syntax(self):
        """Get the template syntax for this placeholder."""
        return f"{{{{{ self.name} }}}}"
    
    def get_conditional_syntax(self, condition):
        """Get conditional syntax for this placeholder."""
        return f"{{% if {condition} %}}{{{{{ self.name} }}}}{{% endif %}}"


class DocumentTemplate(models.Model):
    """
    Document Template model for template management.
    
    Stores document templates with placeholder definitions
    and generation rules.
    """
    
    TEMPLATE_TYPES = [
        ('DOCX', 'Word Document (.docx)'),
        ('PDF', 'PDF Document (.pdf)'),
        ('HTML', 'HTML Document (.html)'),
        ('TEXT', 'Text Document (.txt)'),
        ('CUSTOM', 'Custom Format'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ARCHIVED', 'Archived'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template configuration
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    file_path = models.CharField(
        max_length=500,
        help_text="Path to template file"
    )
    output_filename_pattern = models.CharField(
        max_length=200,
        default='{DOC_NUMBER}_{DOC_TITLE}',
        help_text="Pattern for output filename using placeholders"
    )
    
    # Template content and processing
    placeholders = models.ManyToManyField(
        PlaceholderDefinition,
        through='TemplatePlaceholder',
        related_name='templates'
    )
    processing_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Processing rules and configurations"
    )
    
    # Version and status
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_default = models.BooleanField(
        default=False,
        help_text="Default template for this type"
    )
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_templates'
    )
    
    class Meta:
        db_table = 'document_templates'
        verbose_name = _('Document Template')
        verbose_name_plural = _('Document Templates')
        ordering = ['name', 'version']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'version'],
                name='unique_template_version'
            ),
        ]
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['status']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def increment_usage(self):
        """Increment usage counter and update last used timestamp."""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def get_output_filename(self, context_data):
        """Generate output filename using pattern and context data."""
        try:
            # Simple placeholder replacement for filename
            filename = self.output_filename_pattern
            for placeholder, value in context_data.items():
                filename = filename.replace(f'{{{placeholder}}}', str(value))
            return filename
        except Exception:
            return f"{self.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"


class TemplatePlaceholder(models.Model):
    """
    Template-Placeholder relationship model.
    
    Defines how placeholders are used within specific templates
    with template-specific configurations.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name='template_placeholders'
    )
    placeholder = models.ForeignKey(
        PlaceholderDefinition,
        on_delete=models.CASCADE,
        related_name='template_usages'
    )
    
    # Template-specific configuration
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this placeholder is required for this template"
    )
    default_value = models.TextField(
        blank=True,
        help_text="Template-specific default value"
    )
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Template-specific validation rules"
    )
    
    # Position and formatting
    order = models.PositiveIntegerField(default=0)
    format_override = models.CharField(
        max_length=100,
        blank=True,
        help_text="Override format string for this template"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'template_placeholders'
        verbose_name = _('Template Placeholder')
        verbose_name_plural = _('Template Placeholders')
        ordering = ['order', 'placeholder__name']
        constraints = [
            models.UniqueConstraint(
                fields=['template', 'placeholder'],
                name='unique_template_placeholder'
            ),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.placeholder.name}"


class DocumentGeneration(models.Model):
    """
    Document Generation model for tracking generated documents.
    
    Tracks document generation requests, status, and results
    for audit and monitoring purposes.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.PROTECT,
        related_name='generations'
    )
    
    # Source document (if generating from existing)
    source_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generations'
    )
    
    # Generation configuration
    output_format = models.CharField(max_length=20)
    context_data = models.JSONField(
        default=dict,
        help_text="Data used for placeholder replacement"
    )
    generation_options = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional options for document generation"
    )
    
    # Generation results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    output_file_path = models.CharField(max_length=500, blank=True)
    output_filename = models.CharField(max_length=200, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_checksum = models.CharField(max_length=64, blank=True)
    
    # Processing details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='document_generations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_generations'
        verbose_name = _('Document Generation')
        verbose_name_plural = _('Document Generations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['template']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.status} - {self.created_at}"
    
    def mark_processing(self):
        """Mark generation as processing."""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, output_file_path, file_size=None, checksum=None):
        """Mark generation as completed."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.output_file_path = output_file_path
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
        
        if file_size:
            self.file_size = file_size
        if checksum:
            self.file_checksum = checksum
            
        self.save(update_fields=[
            'status', 'completed_at', 'output_file_path',
            'processing_time', 'file_size', 'file_checksum'
        ])
    
    def mark_failed(self, error_message):
        """Mark generation as failed."""
        self.status = 'FAILED'
        self.completed_at = timezone.now()
        self.error_message = error_message
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
            
        self.save(update_fields=[
            'status', 'completed_at', 'error_message', 'processing_time'
        ])


class PlaceholderCache(models.Model):
    """
    Placeholder Cache model for caching computed placeholder values.
    
    Caches expensive-to-compute placeholder values to improve
    document generation performance.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    placeholder = models.ForeignKey(
        PlaceholderDefinition,
        on_delete=models.CASCADE,
        related_name='cache_entries'
    )
    
    # Cache key and value
    cache_key = models.CharField(max_length=255)
    cached_value = models.TextField()
    context_hash = models.CharField(
        max_length=64,
        help_text="Hash of the context data used to generate this value"
    )
    
    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    hit_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'placeholder_cache'
        verbose_name = _('Placeholder Cache')
        verbose_name_plural = _('Placeholder Cache')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['placeholder', 'cache_key'],
                name='unique_placeholder_cache_key'
            ),
        ]
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['placeholder', 'cache_key']),
        ]
    
    def __str__(self):
        return f"{self.placeholder.name} - {self.cache_key}"
    
    def is_expired(self):
        """Check if cache entry is expired."""
        return timezone.now() > self.expires_at
    
    def increment_hit_count(self):
        """Increment hit count for cache statistics."""
        self.hit_count += 1
        self.save(update_fields=['hit_count'])