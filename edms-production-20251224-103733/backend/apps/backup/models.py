"""
Backup Models for EDMS S4 Module.

Models for backup management, health monitoring,
and disaster recovery procedures.
"""

import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class BackupConfiguration(models.Model):
    """
    Backup Configuration model for system backup settings.
    
    Defines backup policies, schedules, and retention rules
    for different types of data.
    """
    
    BACKUP_TYPES = [
        ('FULL', 'Full Backup'),
        ('INCREMENTAL', 'Incremental Backup'),
        ('DIFFERENTIAL', 'Differential Backup'),
        ('DATABASE', 'Database Only'),
        ('FILES', 'Files Only'),
        ('EXPORT', 'Export Package'),
    ]
    
    BACKUP_FREQUENCIES = [
        ('HOURLY', 'Hourly'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('ON_DEMAND', 'On Demand'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Backup configuration
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    frequency = models.CharField(max_length=20, choices=BACKUP_FREQUENCIES)
    
    # Schedule settings
    schedule_time = models.TimeField(
        help_text="Time of day to run backup (for daily/weekly/monthly)"
    )
    schedule_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Days of week for weekly backups (0=Monday, 6=Sunday)"
    )
    
    # Retention policy
    retention_days = models.PositiveIntegerField(
        default=30,
        help_text="Number of days to keep backups"
    )
    max_backups = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of backups to keep"
    )
    
    # Storage configuration
    storage_path = models.CharField(
        max_length=500,
        help_text="Path where backups will be stored"
    )
    compression_enabled = models.BooleanField(
        default=True,
        help_text="Enable backup compression"
    )
    encryption_enabled = models.BooleanField(
        default=True,
        help_text="Enable backup encryption"
    )
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_enabled = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_backup_configs'
    )
    
    class Meta:
        app_label = "backup"
        db_table = 'backup_configurations'
        verbose_name = _('Backup Configuration')
        verbose_name_plural = _('Backup Configurations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['backup_type']),
            models.Index(fields=['frequency']),
            models.Index(fields=['status', 'is_enabled']),
        ]
    
    def natural_key(self):
        """Return the natural key for this backup configuration (name)"""
        return (self.name,)

    @classmethod
    def get_by_natural_key(cls, name):
        """Get backup configuration by natural key (name)"""
        return cls.objects.get(name=name)

    def __str__(self):
        return f"{self.name} ({self.backup_type} - {self.frequency})"


class BackupJob(models.Model):
    """
    Backup Job model for individual backup executions.
    
    Tracks backup job execution, status, and results
    for monitoring and audit purposes.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('TIMEOUT', 'Timeout'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    configuration = models.ForeignKey(
        BackupConfiguration,
        on_delete=models.CASCADE,
        related_name='backup_jobs'
    )
    
    # Job details
    job_name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=20)
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    backup_file_path = models.CharField(max_length=500, blank=True)
    backup_size = models.BigIntegerField(
        null=True, blank=True,
        help_text="Backup file size in bytes"
    )
    compression_ratio = models.FloatField(
        null=True, blank=True,
        help_text="Compression ratio (original/compressed)"
    )
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Validation
    checksum = models.CharField(
        max_length=64, blank=True,
        help_text="SHA-256 checksum of backup file"
    )
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='triggered_backups'
    )
    
    class Meta:
        app_label = "backup"
        db_table = 'backup_jobs'
        verbose_name = _('Backup Job')
        verbose_name_plural = _('Backup Jobs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['configuration', 'created_at']),
            models.Index(fields=['backup_type']),
        ]
    
    def natural_key(self):
        """Return the natural key for this backup job"""
        return (
            self.configuration.natural_key()[0],  # Configuration name
            str(self.uuid)                        # Job UUID for uniqueness
        )

    @classmethod
    def get_by_natural_key(cls, config_name, job_uuid):
        """Get backup job by natural key"""
        config = BackupConfiguration.objects.get(name=config_name)
        return cls.objects.get(configuration=config, uuid=job_uuid)

    def __str__(self):
        return f"{self.job_name} - {self.status} - {self.created_at}"
    
    def mark_started(self):
        """Mark backup job as started."""
        self.status = 'RUNNING'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, file_path: str, file_size: int = None, checksum: str = None):
        """Mark backup job as completed."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.backup_file_path = file_path
        
        if self.started_at:
            self.duration = self.completed_at - self.started_at
        
        if file_size:
            self.backup_size = file_size
        
        if checksum:
            self.checksum = checksum
            self.is_valid = True
        
        self.save(update_fields=[
            'status', 'completed_at', 'backup_file_path',
            'duration', 'backup_size', 'checksum', 'is_valid'
        ])
    
    def mark_failed(self, error_message: str):
        """Mark backup job as failed."""
        self.status = 'FAILED'
        self.completed_at = timezone.now()
        self.error_message = error_message
        
        if self.started_at:
            self.duration = self.completed_at - self.started_at
        
        self.save(update_fields=[
            'status', 'completed_at', 'error_message', 'duration'
        ])


class RestoreJob(models.Model):
    """
    Restore Job model for data restoration operations.
    
    Tracks restore operations from backups for
    disaster recovery and data restoration.
    """
    
    RESTORE_TYPES = [
        ('FULL_RESTORE', 'Full System Restore'),
        ('DATABASE_RESTORE', 'Database Restore'),
        ('FILES_RESTORE', 'Files Restore'),
        ('SELECTIVE_RESTORE', 'Selective Restore'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    backup_job = models.ForeignKey(
        BackupJob,
        on_delete=models.PROTECT,
        related_name='restore_jobs'
    )
    
    # Restore details
    restore_type = models.CharField(max_length=20, choices=RESTORE_TYPES)
    target_location = models.CharField(
        max_length=500,
        help_text="Target location for restore"
    )
    restore_options = models.JSONField(
        default=dict,
        blank=True,
        help_text="Restore-specific options"
    )
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    restored_items_count = models.PositiveIntegerField(default=0)
    failed_items_count = models.PositiveIntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    restore_log = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='requested_restores'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='approved_restores'
    )
    
    class Meta:
        app_label = "backup"
        db_table = 'restore_jobs'
        verbose_name = _('Restore Job')
        verbose_name_plural = _('Restore Jobs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['restore_type']),
            models.Index(fields=['requested_by']),
        ]
    
    def natural_key(self):
        """Return the natural key for this restore job"""
        return (
            self.backup_job.natural_key()[0],  # Configuration name
            self.backup_job.natural_key()[1],  # Job UUID
            str(self.uuid)                     # Restore job UUID
        )

    @classmethod
    def get_by_natural_key(cls, config_name, job_uuid, restore_uuid):
        """Get restore job by natural key"""
        backup_job = BackupJob.get_by_natural_key(config_name, job_uuid)
        return cls.objects.get(backup_job=backup_job, uuid=restore_uuid)

    def __str__(self):
        return f"Restore {self.restore_type} - {self.status} - {self.created_at}"


class HealthCheck(models.Model):
    """
    Health Check model for system monitoring.
    
    Stores health check results for various system components
    including database, storage, and application health.
    """
    
    CHECK_TYPES = [
        ('DATABASE', 'Database Health'),
        ('STORAGE', 'Storage Health'),
        ('APPLICATION', 'Application Health'),
        ('NETWORK', 'Network Connectivity'),
        ('SERVICES', 'External Services'),
        ('BACKUP_SYSTEM', 'Backup System'),
        ('SECURITY', 'Security Status'),
    ]
    
    STATUS_CHOICES = [
        ('HEALTHY', 'Healthy'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    check_name = models.CharField(max_length=200)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPES)
    
    # Check results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time = models.FloatField(
        null=True, blank=True,
        help_text="Response time in seconds"
    )
    
    # Details
    message = models.TextField(blank=True)
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed check results"
    )
    
    # Metrics
    metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Performance and health metrics"
    )
    
    # Metadata
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "backup"
        db_table = 'health_checks'
        verbose_name = _('Health Check')
        verbose_name_plural = _('Health Checks')
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['check_type', 'status']),
            models.Index(fields=['status', 'checked_at']),
            models.Index(fields=['check_name']),
        ]
    
    def __str__(self):
        return f"{self.check_name} - {self.status} - {self.checked_at}"


class SystemMetric(models.Model):
    """
    System Metric model for performance monitoring.
    
    Stores system performance metrics for monitoring
    and trend analysis.
    """
    
    METRIC_TYPES = [
        ('CPU_USAGE', 'CPU Usage'),
        ('MEMORY_USAGE', 'Memory Usage'),
        ('DISK_USAGE', 'Disk Usage'),
        ('NETWORK_IO', 'Network I/O'),
        ('DATABASE_PERFORMANCE', 'Database Performance'),
        ('APPLICATION_PERFORMANCE', 'Application Performance'),
        ('USER_ACTIVITY', 'User Activity'),
        ('DOCUMENT_ACTIVITY', 'Document Activity'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    metric_name = models.CharField(max_length=200)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    
    # Metric values
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    
    # Thresholds
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('NORMAL', 'Normal'),
            ('WARNING', 'Warning'),
            ('CRITICAL', 'Critical'),
        ],
        default='NORMAL'
    )
    
    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metric metadata"
    )
    
    # Timing
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "backup"
        db_table = 'system_metrics'
        verbose_name = _('System Metric')
        verbose_name_plural = _('System Metrics')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', 'recorded_at']),
            models.Index(fields=['metric_name', 'recorded_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit} - {self.recorded_at}"
    
    def check_thresholds(self):
        """Check if metric exceeds thresholds and update status."""
        if self.critical_threshold and self.value >= self.critical_threshold:
            self.status = 'CRITICAL'
        elif self.warning_threshold and self.value >= self.warning_threshold:
            self.status = 'WARNING'
        else:
            self.status = 'NORMAL'
        
        self.save(update_fields=['status'])


class DisasterRecoveryPlan(models.Model):
    """
    Disaster Recovery Plan model for DR procedures.
    
    Stores disaster recovery plans and procedures
    for different types of disasters.
    """
    
    DISASTER_TYPES = [
        ('HARDWARE_FAILURE', 'Hardware Failure'),
        ('SOFTWARE_FAILURE', 'Software Failure'),
        ('DATA_CORRUPTION', 'Data Corruption'),
        ('SECURITY_BREACH', 'Security Breach'),
        ('NATURAL_DISASTER', 'Natural Disaster'),
        ('POWER_OUTAGE', 'Power Outage'),
        ('NETWORK_FAILURE', 'Network Failure'),
    ]
    
    PLAN_STATUS = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('UNDER_REVIEW', 'Under Review'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    disaster_type = models.CharField(max_length=30, choices=DISASTER_TYPES)
    
    # Plan details
    recovery_procedures = models.TextField(
        help_text="Step-by-step recovery procedures"
    )
    estimated_recovery_time = models.DurationField(
        help_text="Estimated time to complete recovery"
    )
    required_resources = models.JSONField(
        default=list,
        help_text="Resources required for recovery"
    )
    
    # Contacts and responsibilities
    responsible_team = models.JSONField(
        default=list,
        help_text="Team members responsible for executing plan"
    )
    emergency_contacts = models.JSONField(
        default=list,
        help_text="Emergency contact information"
    )
    
    # Status and versioning
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='DRAFT')
    version = models.CharField(max_length=20, default='1.0')
    
    # Testing and validation
    last_tested = models.DateTimeField(null=True, blank=True)
    test_results = models.TextField(blank=True)
    next_test_due = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_dr_plans'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='approved_dr_plans'
    )
    
    class Meta:
        app_label = "backup"
        db_table = 'disaster_recovery_plans'
        verbose_name = _('Disaster Recovery Plan')
        verbose_name_plural = _('Disaster Recovery Plans')
        ordering = ['name']
        indexes = [
            models.Index(fields=['disaster_type']),
            models.Index(fields=['status']),
            models.Index(fields=['next_test_due']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.disaster_type})"