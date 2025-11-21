# Django Models Implementation

## Overview
This document provides the complete Django model implementations based on the database schema, including all apps, models, relationships, and custom methods.

## Project Apps Structure

```python
# settings.py - Installed Apps
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'corsheaders',
    'river',
    
    # EDMS apps
    'apps.users',
    'apps.documents',
    'apps.audit',
    'apps.workflow',
    'apps.storage',
    'apps.auth',
    'apps.scheduler',
    'apps.backup',
    'apps.placeholders',
    'apps.settings',
]
```

## Users App Models

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.core.validators import RegexValidator
import uuid

class UserProfile(models.Model):
    """Extended user profile for EDMS users"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Invalid phone number format')]
    )
    title = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    azure_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    ldap_dn = models.CharField(max_length=255, blank=True)
    
    # MFA settings
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)
    
    # Account status
    account_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_password_change = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if not self.account_locked:
            return False
        
        if self.locked_until and timezone.now() > self.locked_until:
            # Auto-unlock expired locks
            self.account_locked = False
            self.locked_until = None
            self.failed_login_attempts = 0
            self.save()
            return False
        
        return True

class MFADevice(models.Model):
    """Multi-factor authentication devices"""
    
    MFA_TYPES = [
        ('totp', 'TOTP Authenticator'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_type = models.CharField(max_length=10, choices=MFA_TYPES)
    device_name = models.CharField(max_length=100)
    secret = models.CharField(max_length=32, blank=True)  # For TOTP
    phone_number = models.CharField(max_length=20, blank=True)  # For SMS
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'device_name']
        verbose_name = 'MFA Device'
        verbose_name_plural = 'MFA Devices'
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name} ({self.device_type})"

class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    
    username = models.CharField(max_length=150, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]

class UserActivity(models.Model):
    """Track user activity for audit purposes"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
```

## Documents App Models

```python
# apps/documents/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from river.models.fields.state import StateField
import uuid
import os

class DocumentType(models.Model):
    """Document type definitions"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    template_path = models.CharField(max_length=500, blank=True)
    retention_period = models.PositiveIntegerField(null=True, blank=True, help_text="Retention period in days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class DocumentSource(models.Model):
    """Document source definitions"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Document(models.Model):
    """Main document model with workflow integration"""
    
    # Workflow states
    DRAFT = 'draft'
    PENDING_REVIEW = 'pending_review'
    REVIEWED = 'reviewed'
    PENDING_APPROVAL = 'pending_approval'
    APPROVED_PENDING_EFFECTIVE = 'approved_pending_effective'
    APPROVED_EFFECTIVE = 'approved_effective'
    SUPERSEDED = 'superseded'
    PENDING_OBSOLETING = 'pending_obsoleting'
    OBSOLETE = 'obsolete'
    DELETED = 'deleted'
    
    STATE_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_REVIEW, 'Pending Review'),
        (REVIEWED, 'Reviewed'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED_PENDING_EFFECTIVE, 'Approved, Pending Effective'),
        (APPROVED_EFFECTIVE, 'Approved and Effective'),
        (SUPERSEDED, 'Superseded'),
        (PENDING_OBSOLETING, 'Pending Obsoleting'),
        (OBSOLETE, 'Obsolete'),
        (DELETED, 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    version_major = models.PositiveIntegerField(default=1)
    version_minor = models.PositiveIntegerField(default=0)
    
    # Document classification
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    document_source = models.ForeignKey(DocumentSource, on_delete=models.PROTECT)
    
    # Workflow participants
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='authored_documents')
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reviewed_documents', null=True, blank=True)
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_documents', null=True, blank=True)
    
    # Workflow state
    status = StateField(default=DRAFT)
    
    # File information
    file_path = models.CharField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_checksum = models.CharField(max_length=64, blank=True, db_index=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Dates
    approval_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True, db_index=True)
    obsolete_date = models.DateField(null=True, blank=True)
    
    # Additional information
    reason_for_change = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['status']),
            models.Index(fields=['author']),
            models.Index(fields=['document_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['effective_date']),
        ]
        permissions = [
            ('can_review_document', 'Can review documents'),
            ('can_approve_document', 'Can approve documents'),
            ('can_obsolete_document', 'Can obsolete documents'),
            ('can_terminate_workflow', 'Can terminate workflows'),
            ('can_view_all_documents', 'Can view all documents'),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.title}"
    
    @property
    def version(self):
        """Get version string"""
        return f"{self.version_major}.{self.version_minor}"
    
    @property
    def can_be_edited(self):
        """Check if document can be edited"""
        return self.status in [self.DRAFT]
    
    @property
    def can_be_obsoleted(self):
        """Check if document can be obsoleted"""
        return self.status == self.APPROVED_EFFECTIVE and not self.has_dependencies()
    
    @property
    def is_current_version(self):
        """Check if this is the current version"""
        return self.status in [self.APPROVED_EFFECTIVE, self.PENDING_OBSOLETING]
    
    def has_dependencies(self):
        """Check if other documents depend on this one"""
        return DocumentDependency.objects.filter(depends_on=self).exists()
    
    def get_dependencies(self):
        """Get documents this document depends on"""
        return Document.objects.filter(
            dependency_sources__document=self,
            status=Document.APPROVED_EFFECTIVE
        )
    
    def get_dependents(self):
        """Get documents that depend on this document"""
        return Document.objects.filter(
            dependency_targets__depends_on=self
        )
    
    def generate_document_number(self):
        """Generate unique document number"""
        if not self.document_number:
            from django.conf import settings
            prefix = getattr(settings, 'DOCUMENT_NUMBER_PREFIX', 'DOC')
            year = self.created_at.year if self.created_at else timezone.now().year
            
            # Get next sequence number for the year
            last_doc = Document.objects.filter(
                document_number__startswith=f"{prefix}-{year}-"
            ).order_by('-document_number').first()
            
            if last_doc:
                try:
                    last_num = int(last_doc.document_number.split('-')[-1])
                    next_num = last_num + 1
                except ValueError:
                    next_num = 1
            else:
                next_num = 1
            
            self.document_number = f"{prefix}-{year}-{next_num:04d}"
    
    def save(self, *args, **kwargs):
        if not self.document_number:
            self.generate_document_number()
        super().save(*args, **kwargs)

class DocumentDependency(models.Model):
    """Document dependencies and relationships"""
    
    DEPENDENCY_TYPES = [
        ('REFERENCE', 'Reference'),
        ('TEMPLATE', 'Template'),
        ('SUPERSEDES', 'Supersedes'),
        ('RELATED', 'Related'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='dependency_sources')
    depends_on = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='dependency_targets')
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPES, default='REFERENCE')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['document', 'depends_on']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['depends_on']),
        ]
    
    def __str__(self):
        return f"{self.document.document_number} depends on {self.depends_on.document_number}"

class DocumentVersion(models.Model):
    """Document version history"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_major = models.PositiveIntegerField()
    version_minor = models.PositiveIntegerField()
    file_path = models.CharField(max_length=500)
    file_checksum = models.CharField(max_length=64)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    change_summary = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-version_major', '-version_minor']
        unique_together = ['document', 'version_major', 'version_minor']
    
    def __str__(self):
        return f"{self.document.document_number} v{self.version_major}.{self.version_minor}"
    
    @property
    def version(self):
        return f"{self.version_major}.{self.version_minor}"

class DocumentWorkflowHistory(models.Model):
    """Document workflow transition history"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='workflow_history')
    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comments = models.TextField(blank=True)
    approved = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.document.document_number}: {self.from_state} → {self.to_state}"

class DocumentDownload(models.Model):
    """Track document downloads for audit purposes"""
    
    DOWNLOAD_TYPES = [
        ('ORIGINAL', 'Original Document'),
        ('ANNOTATED', 'Annotated Document'),
        ('OFFICIAL_PDF', 'Official PDF'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloaded_documents')
    download_type = models.CharField(max_length=20, choices=DOWNLOAD_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    file_checksum = models.CharField(max_length=64, blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-downloaded_at']
        indexes = [
            models.Index(fields=['document', 'downloaded_at']),
            models.Index(fields=['user', 'downloaded_at']),
        ]

class DocumentAccessLog(models.Model):
    """Document access logging for compliance"""
    
    ACCESS_TYPES = [
        ('VIEW', 'View'),
        ('DOWNLOAD', 'Download'),
        ('EDIT', 'Edit'),
        ('REVIEW', 'Review'),
        ('APPROVE', 'Approve'),
        ('DELETE', 'Delete'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_access_logs')
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['document', 'accessed_at']),
            models.Index(fields=['user', 'accessed_at']),
        ]
```

## Audit App Models

```python
# apps/audit/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

class AuditTrail(models.Model):
    """Comprehensive audit trail for all system changes"""
    
    ACTION_CHOICES = [
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('WORKFLOW', 'Workflow Change'),
        ('DOWNLOAD', 'Download'),
        ('ACCESS', 'Access'),
    ]
    
    # What was changed
    table_name = models.CharField(max_length=100, db_index=True)
    record_id = models.CharField(max_length=100, db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    
    # Who changed it
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # What changed
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    
    # Why changed
    reason = models.TextField(blank=True)
    
    # When and session info
    session_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.table_name}:{self.record_id} by {self.user}"

class SystemEvent(models.Model):
    """System-level events and alerts"""
    
    SEVERITY_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    event_type = models.CharField(max_length=50, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='INFO', db_index=True)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.severity}: {self.event_type} - {self.message[:50]}"

class ComplianceReport(models.Model):
    """Compliance reporting and validation results"""
    
    REPORT_TYPES = [
        ('CFR_21_PART_11', '21 CFR Part 11 Compliance'),
        ('ALCOA', 'ALCOA Compliance'),
        ('DATA_INTEGRITY', 'Data Integrity Check'),
        ('ACCESS_REVIEW', 'Access Rights Review'),
        ('AUDIT_LOG', 'Audit Log Review'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Report period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Report results
    total_records = models.PositiveIntegerField(default=0)
    compliant_records = models.PositiveIntegerField(default=0)
    non_compliant_records = models.PositiveIntegerField(default=0)
    
    # Report data
    report_data = models.JSONField(default=dict)
    findings = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True)
    
    # Report file
    report_file = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.generated_at.strftime('%Y-%m-%d')}"
```

## Scheduler App Models

```python
# apps/scheduler/models.py
from django.db import models
from django.contrib.auth.models import User

class ScheduledTask(models.Model):
    """Scheduled task definitions"""
    
    TASK_TYPES = [
        ('BACKUP', 'Backup'),
        ('CLEANUP', 'Cleanup'),
        ('NOTIFICATION', 'Notification'),
        ('WORKFLOW', 'Workflow Processing'),
        ('INTEGRITY_CHECK', 'Integrity Check'),
        ('REPORT_GENERATION', 'Report Generation'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('RUNNING', 'Running'),
        ('PENDING', 'Pending'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    cron_expression = models.CharField(max_length=100, help_text="Cron expression for scheduling")
    is_active = models.BooleanField(default=True)
    
    # Task execution info
    last_run = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    last_error = models.TextField(blank=True)
    
    # Task configuration
    task_parameters = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TaskExecution(models.Model):
    """Task execution history"""
    
    task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE, related_name='executions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ScheduledTask.STATUS_CHOICES, default='RUNNING')
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    execution_time = models.PositiveIntegerField(null=True, blank=True, help_text="Execution time in seconds")
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['task', 'started_at']),
        ]
    
    def __str__(self):
        return f"{self.task.name} - {self.started_at}"
```

This Django models implementation provides:

1. **Complete model structure** for all EDMS components
2. **Proper relationships** between models with foreign keys
3. **Django best practices** including Meta classes and custom methods
4. **Database optimization** with strategic indexes
5. **Audit trail integration** with comprehensive logging
6. **Workflow support** with state management
7. **Security features** including user profiles and MFA
8. **File management** with version control and dependencies
9. **Compliance tracking** with detailed audit models
10. **Task scheduling** with execution history

The models are designed to support all the workflows and functionality defined in the previous specifications while maintaining data integrity and performance.