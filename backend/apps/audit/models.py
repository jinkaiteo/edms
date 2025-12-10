"""
Audit Trail Models (S2)

Provides comprehensive audit trail functionality for 21 CFR Part 11 compliance.
Tracks all system changes, user activities, and security events with tamper-proof logging.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


User = get_user_model()


class AuditConfiguration(models.Model):
    """
    Configuration settings for audit trail functionality.
    
    Defines what should be audited and how audit records
    should be managed for compliance requirements.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Audit scope settings
    enable_field_tracking = models.BooleanField(default=True)
    enable_relationship_tracking = models.BooleanField(default=True)
    track_create = models.BooleanField(default=True)
    track_update = models.BooleanField(default=True)
    track_delete = models.BooleanField(default=True)
    
    # Retention settings
    retention_days = models.IntegerField(default=2555)  # 7 years for compliance
    compress_old_records = models.BooleanField(default=True)
    
    # Performance settings
    async_logging = models.BooleanField(default=True)
    batch_size = models.IntegerField(default=100)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Additional settings
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'audit_configurations'
        verbose_name = _('Audit Configuration')
        verbose_name_plural = _('Audit Configurations')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AuditTrail(models.Model):
    """
    Main audit log table for tracking all system changes.
    
    Provides immutable audit trail with comprehensive tracking
    of user actions and system events for compliance.
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ACCESS_GRANTED', 'Access Granted'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('WORKFLOW_TRANSITION', 'Workflow Transition'),
        ('SIGNATURE_APPLIED', 'Digital Signature Applied'),
        ('SIGNATURE_VERIFIED', 'Digital Signature Verified'),
        ('ENCRYPTION', 'Encryption'),
        ('DECRYPTION', 'Decryption'),
        ('BACKUP_CREATED', 'Backup Created'),
        ('RESTORE_PERFORMED', 'Restore Performed'),
        ('CONFIGURATION_CHANGED', 'Configuration Changed'),
        ('ROLE_ASSIGNED', 'Role Assigned'),
        ('ROLE_REMOVED', 'Role Removed'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('ACCOUNT_UNLOCKED', 'Account Unlocked'),
        ('SYSTEM_EVENT', 'System Event'),
        ('SECURITY_EVENT', 'Security Event'),
    ]
    
    SEVERITY_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Primary audit fields
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='INFO')
    
    # User and session information
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    user_display_name = models.CharField(max_length=200, blank=True)
    session_id = models.CharField(max_length=40, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Object being audited (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_representation = models.CharField(max_length=200, blank=True)
    
    # Change information
    field_changes = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    old_values = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    new_values = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    
    # Additional context
    description = models.TextField(blank=True)
    module = models.CharField(max_length=10, blank=True)  # O1, S1, S2, etc.
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Compliance and integrity
    checksum = models.CharField(max_length=64, blank=True)  # SHA-256 checksum
    is_tampered = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, default='VERIFIED')
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'audit_trail'
        verbose_name = _('Audit Log Entry')
        verbose_name_plural = _('Audit Log Entries')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['module', 'action']),
            models.Index(fields=['checksum']),
        ]
    
    def natural_key(self):
        """Return the natural key for this audit trail entry"""
        return (
            str(self.uuid),  # Unique UUID for this audit entry
            self.timestamp.isoformat()  # Timestamp for additional uniqueness
        )

    @classmethod
    def get_by_natural_key(cls, audit_uuid, timestamp_iso):
        """Get audit trail entry by natural key"""
        return cls.objects.get(uuid=audit_uuid)

    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.user_display_name or 'System'}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate checksum for integrity."""
        if not self.checksum:
            self.checksum = self.calculate_checksum()
        super().save(*args, **kwargs)
    
    def calculate_checksum(self):
        """Calculate SHA-256 checksum for tamper detection."""
        import hashlib
        
        # Create a consistent string representation
        data_string = f"{self.timestamp}{self.action}{self.user_id or ''}{self.object_id or ''}{json.dumps(self.field_changes, sort_keys=True)}"
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def verify_integrity(self):
        """Verify the integrity of this audit record."""
        expected_checksum = self.calculate_checksum()
        return self.checksum == expected_checksum


class AuditQueryLog(models.Model):
    """
    Logs audit trail queries and access for compliance.
    
    Tracks who accessed audit records and when for
    regulatory compliance and security monitoring.
    """
    
    QUERY_TYPES = [
        ('VIEW', 'View Records'),
        ('SEARCH', 'Search Records'),
        ('EXPORT', 'Export Records'),
        ('REPORT', 'Generate Report'),
        ('FILTER', 'Filter Records'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    query_type = models.CharField(max_length=20, choices=QUERY_TYPES)
    
    # User performing the query
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    
    # Query details
    query_description = models.TextField()
    filters_applied = models.JSONField(default=dict, blank=True)
    records_accessed = models.IntegerField(default=0)
    
    # Date range queried
    date_from = models.DateTimeField(null=True, blank=True)
    date_to = models.DateTimeField(null=True, blank=True)
    
    # Additional context
    purpose = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'audit_query_logs'
        verbose_name = _('Audit Query Log')
        verbose_name_plural = _('Audit Query Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['query_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.query_type} by {self.user.username} at {self.timestamp}"


class ComplianceReport(models.Model):
    """
    Stores compliance reports generated from audit data.
    
    Maintains generated compliance reports for regulatory
    submissions and audit purposes.
    """
    
    REPORT_TYPES = [
        ('CFR_PART_11', '21 CFR Part 11 Compliance'),
        ('USER_ACTIVITY', 'User Activity Report'),
        ('DOCUMENT_LIFECYCLE', 'Document Lifecycle Report'),
        ('ACCESS_CONTROL', 'Access Control Report'),
        ('SECURITY_EVENTS', 'Security Events Report'),
        ('SYSTEM_CHANGES', 'System Changes Report'),
        ('SIGNATURE_VERIFICATION', 'Digital Signature Report'),
        ('DATA_INTEGRITY', 'Data Integrity Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Report parameters
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    filters = models.JSONField(default=dict, blank=True)
    
    # Generation info
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATING')
    
    # Report content
    report_data = models.JSONField(default=dict, blank=True)
    summary_stats = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    
    # Integrity and compliance
    report_checksum = models.CharField(max_length=64, blank=True)
    digital_signature = models.TextField(blank=True)
    
    # Lifecycle management
    expires_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'compliance_reports'
        verbose_name = _('Compliance Report')
        verbose_name_plural = _('Compliance Reports')
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'generated_at']),
            models.Index(fields=['generated_by', 'generated_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"


class DataIntegrityCheck(models.Model):
    """
    Records data integrity verification checks.
    
    Tracks automated and manual data integrity checks
    performed on the system for compliance monitoring.
    """
    
    CHECK_TYPES = [
        ('CHECKSUM', 'Checksum Verification'),
        ('SIGNATURE', 'Digital Signature Verification'),
        ('AUDIT_TRAIL', 'Audit Trail Integrity'),
        ('DATABASE', 'Database Integrity'),
        ('FILE_SYSTEM', 'File System Integrity'),
        ('BACKUP', 'Backup Integrity'),
        ('ENCRYPTION', 'Encryption Integrity'),
    ]
    
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Check parameters
    scope = models.CharField(max_length=200)  # What was checked
    parameters = models.JSONField(default=dict, blank=True)
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')
    items_checked = models.IntegerField(default=0)
    items_passed = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    
    # Findings
    findings = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True)
    
    # Execution context
    triggered_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    is_automated = models.BooleanField(default=False)
    execution_time = models.DurationField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'data_integrity_checks'
        verbose_name = _('Data Integrity Check')
        verbose_name_plural = _('Data Integrity Checks')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['check_type', 'started_at']),
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['is_automated', 'started_at']),
        ]
    
    def __str__(self):
        return f"{self.get_check_type_display()} - {self.status} ({self.started_at})"


class SystemEvent(models.Model):
    """
    System-level events and automated actions.
    """
    
    EVENT_TYPES = [
        ('STARTUP', 'System Startup'),
        ('SHUTDOWN', 'System Shutdown'),
        ('ERROR', 'System Error'),
        ('WARNING', 'System Warning'),
        ('MAINTENANCE', 'Maintenance Event'),
        ('BACKUP', 'Backup Event'),
        ('UPDATE', 'System Update'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=10, default='INFO')
    
    class Meta:
        app_label = "audit"
        db_table = 'system_events'
        ordering = ['-timestamp']

    def natural_key(self):
        """Return the natural key for this system event"""
        return (
            str(self.uuid),  # Unique UUID
            self.timestamp.isoformat()  # Timestamp for additional context
        )

    @classmethod
    def get_by_natural_key(cls, event_uuid, timestamp_iso):
        """Get system event by natural key"""
        return cls.objects.get(uuid=event_uuid)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"


class LoginAudit(models.Model):
    """
    Login and authentication audit records.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    username = models.CharField(max_length=150)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    failure_reason = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'login_audit'
        ordering = ['-timestamp']

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username} - {status} at {self.timestamp}"


class UserSession(models.Model):
    """
    User session tracking for audit purposes.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_timestamp = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_timestamp = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'user_sessions_audit'
        ordering = ['-login_timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.session_key}"


class DatabaseChangeLog(models.Model):
    """
    Database change log for detailed tracking.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    table_name = models.CharField(max_length=100)
    operation = models.CharField(max_length=20)
    record_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Additional fields that audit signals try to pass
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=30, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=40, null=True, blank=True)
    integrity_hash = models.CharField(max_length=64, null=True, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'database_change_log'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.operation} on {self.table_name} at {self.timestamp}"


class ComplianceEvent(models.Model):
    """
    Compliance-related events and violations.
    """
    
    EVENT_TYPES = [
        ('VALIDATION', 'Validation Event'),
        ('VIOLATION', 'Compliance Violation'),
        ('REVIEW', 'Compliance Review'),
        ('AUDIT', 'Audit Event'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    severity = models.CharField(max_length=10, default='INFO')
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    resolution_status = models.CharField(max_length=20, default='OPEN')
    
    class Meta:
        app_label = "audit"
        db_table = 'compliance_events'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} - {self.description[:50]}"


class AuditEvent(models.Model):
    """
    High-level audit events for business process tracking.
    
    Tracks significant business events that span multiple
    system actions for process-level audit trails.
    """
    
    EVENT_TYPES = [
        ('DOCUMENT_CREATED', 'Document Created'),
        ('DOCUMENT_PUBLISHED', 'Document Published'),
        ('DOCUMENT_OBSOLETED', 'Document Obsoleted'),
        ('WORKFLOW_COMPLETED', 'Workflow Completed'),
        ('USER_REGISTERED', 'User Registered'),
        ('ROLE_CHANGED', 'Role Changed'),
        ('SYSTEM_BACKUP', 'System Backup'),
        ('SECURITY_INCIDENT', 'Security Incident'),
        ('COMPLIANCE_VIOLATION', 'Compliance Violation'),
        ('DATA_EXPORT', 'Data Export'),
        ('CONFIGURATION_UPDATE', 'Configuration Update'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Participants
    primary_user = models.ForeignKey(
        User, on_delete=models.PROTECT, 
        related_name='primary_audit_events'
    )
    involved_users = models.ManyToManyField(
        User, blank=True,
        related_name='involved_audit_events'
    )
    
    # Related objects
    related_audit_logs = models.ManyToManyField(AuditTrail, blank=True)
    
    # Event outcome
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Business context
    business_process = models.CharField(max_length=100, blank=True)
    compliance_impact = models.TextField(blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "audit"
        db_table = 'audit_events'
        verbose_name = _('Audit Event')
        verbose_name_plural = _('Audit Events')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['event_type', 'started_at']),
            models.Index(fields=['primary_user', 'started_at']),
            models.Index(fields=['is_successful', 'started_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.event_type})"