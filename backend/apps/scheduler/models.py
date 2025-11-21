"""
Scheduler Models for EDMS (S3).

Implements scheduled task management for document lifecycle
automation and system maintenance with Celery integration.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


User = get_user_model()


class ScheduledTask(models.Model):
    """
    Scheduled Task model for managing automated system tasks.
    
    Defines tasks that run on schedule for document lifecycle
    management and system automation.
    """
    
    TASK_TYPES = [
        ('DOCUMENT_EFFECTIVE', 'Make Documents Effective'),
        ('DOCUMENT_OBSOLETE', 'Process Document Obsolescence'),
        ('REVIEW_REMINDER', 'Send Review Reminders'),
        ('APPROVAL_REMINDER', 'Send Approval Reminders'),
        ('OVERDUE_NOTIFICATION', 'Send Overdue Notifications'),
        ('HEALTH_CHECK', 'System Health Check'),
        ('DATABASE_BACKUP', 'Database Backup'),
        ('FILE_CLEANUP', 'Cleanup Temporary Files'),
        ('AUDIT_CLEANUP', 'Cleanup Old Audit Logs'),
        ('WORKFLOW_TIMEOUT', 'Handle Workflow Timeouts'),
        ('DEPENDENCY_CHECK', 'Check Document Dependencies'),
        ('CUSTOM', 'Custom Task'),
    ]
    
    TASK_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('ERROR', 'Error'),
    ]
    
    FREQUENCY_TYPES = [
        ('ONCE', 'Run Once'),
        ('MINUTELY', 'Every Minute'),
        ('HOURLY', 'Every Hour'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('CRON', 'Custom Cron Expression'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=30, choices=TASK_TYPES)
    
    # Task configuration
    task_module = models.CharField(max_length=200)  # Python module path
    task_function = models.CharField(max_length=100)  # Function name
    task_args = models.JSONField(default=list, blank=True)  # Positional arguments
    task_kwargs = models.JSONField(default=dict, blank=True)  # Keyword arguments
    
    # Scheduling configuration
    frequency_type = models.CharField(max_length=20, choices=FREQUENCY_TYPES, default='DAILY')
    cron_expression = models.CharField(max_length=100, blank=True, help_text="Cron expression for custom scheduling")
    interval_value = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Timing settings
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Execution settings
    timeout_seconds = models.PositiveIntegerField(default=3600)  # 1 hour
    max_retries = models.PositiveIntegerField(default=3)
    retry_delay_seconds = models.PositiveIntegerField(default=300)  # 5 minutes
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='ACTIVE')
    is_running = models.BooleanField(default=False)
    total_runs = models.PositiveIntegerField(default=0)
    successful_runs = models.PositiveIntegerField(default=0)
    failed_runs = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    # Management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'scheduled_tasks'
        verbose_name = _('Scheduled Task')
        verbose_name_plural = _('Scheduled Tasks')
        ordering = ['name']
        indexes = [
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['next_run', 'status']),
            models.Index(fields=['is_running']),
            models.Index(fields=['frequency_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_task_type_display()})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue for execution."""
        return (
            self.next_run and 
            self.next_run < timezone.now() and 
            self.status == 'ACTIVE' and 
            not self.is_running
        )
    
    def calculate_next_run(self):
        """Calculate next run time based on frequency settings."""
        if self.frequency_type == 'ONCE':
            return None
        
        from datetime import timedelta
        import croniter
        
        base_time = self.last_run or self.start_date
        
        if self.frequency_type == 'MINUTELY':
            return base_time + timedelta(minutes=self.interval_value)
        elif self.frequency_type == 'HOURLY':
            return base_time + timedelta(hours=self.interval_value)
        elif self.frequency_type == 'DAILY':
            return base_time + timedelta(days=self.interval_value)
        elif self.frequency_type == 'WEEKLY':
            return base_time + timedelta(weeks=self.interval_value)
        elif self.frequency_type == 'MONTHLY':
            # Approximate monthly scheduling
            return base_time + timedelta(days=30 * self.interval_value)
        elif self.frequency_type == 'CRON' and self.cron_expression:
            try:
                cron = croniter.croniter(self.cron_expression, base_time)
                return cron.get_next(datetime)
            except:
                return None
        
        return None
    
    def mark_execution_start(self):
        """Mark task as running."""
        self.is_running = True
        self.save(update_fields=['is_running'])
    
    def mark_execution_complete(self, success=True, error_message=''):
        """Mark task execution as complete."""
        self.is_running = False
        self.last_run = timezone.now()
        self.total_runs += 1
        
        if success:
            self.successful_runs += 1
            self.last_error = ''
        else:
            self.failed_runs += 1
            self.last_error = error_message
        
        self.next_run = self.calculate_next_run()
        
        self.save(update_fields=[
            'is_running', 'last_run', 'total_runs', 'successful_runs',
            'failed_runs', 'last_error', 'next_run'
        ])


class TaskExecution(models.Model):
    """
    Task Execution model for tracking individual task runs.
    
    Maintains detailed history of task executions for
    monitoring and troubleshooting.
    """
    
    EXECUTION_STATUS = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('TIMEOUT', 'Timeout'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    scheduled_task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution details
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='RUNNING')
    
    # Execution context
    celery_task_id = models.CharField(max_length=100, blank=True)
    worker_hostname = models.CharField(max_length=255, blank=True)
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='triggered_executions'
    )
    
    # Results
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    output_log = models.TextField(blank=True)
    
    # Performance metrics
    execution_time = models.DurationField(null=True, blank=True)
    memory_usage = models.PositiveIntegerField(null=True, blank=True)  # MB
    cpu_usage = models.FloatField(null=True, blank=True)  # Percentage
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'task_executions'
        verbose_name = _('Task Execution')
        verbose_name_plural = _('Task Executions')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['scheduled_task', 'started_at']),
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['celery_task_id']),
        ]
    
    def __str__(self):
        return f"{self.scheduled_task.name} - {self.started_at} ({self.status})"
    
    @property
    def duration_seconds(self):
        """Get execution duration in seconds."""
        if self.execution_time:
            return self.execution_time.total_seconds()
        elif self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        else:
            return (timezone.now() - self.started_at).total_seconds()
    
    def mark_completed(self, success=True, result_data=None, error_message=''):
        """Mark execution as completed."""
        self.completed_at = timezone.now()
        self.execution_time = self.completed_at - self.started_at
        self.status = 'COMPLETED' if success else 'FAILED'
        
        if result_data:
            self.result = result_data
        
        if error_message:
            self.error_message = error_message
        
        self.save()


class DocumentSchedule(models.Model):
    """
    Document Schedule model for document lifecycle automation.
    
    Manages automatic document state transitions based on
    scheduled dates and business rules.
    """
    
    SCHEDULE_TYPES = [
        ('EFFECTIVE_DATE', 'Make Effective on Date'),
        ('REVIEW_DUE', 'Review Due Reminder'),
        ('OBSOLETE_DATE', 'Make Obsolete on Date'),
        ('ARCHIVE_DATE', 'Archive on Date'),
        ('REMINDER', 'Send Reminder'),
        ('WORKFLOW_TIMEOUT', 'Workflow Timeout'),
    ]
    
    SCHEDULE_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    
    # Schedule definition
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)
    scheduled_date = models.DateTimeField()
    description = models.CharField(max_length=255, blank=True)
    
    # Action configuration
    action_data = models.JSONField(default=dict, blank=True)
    notification_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='document_schedule_notifications'
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=SCHEDULE_STATUS, default='PENDING')
    executed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='executed_document_schedules'
    )
    
    # Results
    execution_result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Management
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_document_schedules'
    )
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'document_schedules'
        verbose_name = _('Document Schedule')
        verbose_name_plural = _('Document Schedules')
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['document', 'schedule_type']),
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.document.document_number} - {self.get_schedule_type_display()}"
    
    @property
    def is_overdue(self):
        """Check if schedule is overdue."""
        return (
            self.scheduled_date < timezone.now() and 
            self.status == 'PENDING'
        )
    
    def execute(self, user=None):
        """Execute the scheduled action."""
        from .services import scheduler_service
        
        return scheduler_service.execute_document_schedule(self, user)


class SystemHealthCheck(models.Model):
    """
    System Health Check model for monitoring system status.
    
    Tracks automated health checks and system monitoring
    for operational visibility.
    """
    
    CHECK_TYPES = [
        ('DATABASE', 'Database Connectivity'),
        ('REDIS', 'Redis Connectivity'),
        ('CELERY', 'Celery Worker Status'),
        ('DISK_SPACE', 'Disk Space Usage'),
        ('MEMORY', 'Memory Usage'),
        ('CPU', 'CPU Usage'),
        ('DOCUMENT_INTEGRITY', 'Document File Integrity'),
        ('WORKFLOW_HEALTH', 'Workflow Engine Health'),
        ('BACKUP_STATUS', 'Backup System Status'),
        ('AUDIT_TRAIL', 'Audit Trail Integrity'),
    ]
    
    CHECK_STATUS = [
        ('HEALTHY', 'Healthy'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('ERROR', 'Error'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    check_type = models.CharField(max_length=30, choices=CHECK_TYPES)
    checked_at = models.DateTimeField(auto_now_add=True)
    
    # Check results
    status = models.CharField(max_length=20, choices=CHECK_STATUS)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Metrics
    response_time = models.FloatField(null=True, blank=True)  # Seconds
    value = models.FloatField(null=True, blank=True)  # Numeric value for metrics
    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'system_health_checks'
        verbose_name = _('System Health Check')
        verbose_name_plural = _('System Health Checks')
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['check_type', 'checked_at']),
            models.Index(fields=['status', 'checked_at']),
            models.Index(fields=['checked_at']),
        ]
    
    def __str__(self):
        return f"{self.get_check_type_display()} - {self.status} ({self.checked_at})"
    
    @property
    def is_critical(self):
        """Check if health check indicates critical status."""
        return self.status in ['CRITICAL', 'ERROR']
    
    @property
    def needs_attention(self):
        """Check if health check needs attention."""
        return self.status in ['WARNING', 'CRITICAL', 'ERROR']


class NotificationQueue(models.Model):
    """
    Notification Queue model for managing scheduled notifications.
    
    Queues notifications for sending based on schedules
    and system events.
    """
    
    NOTIFICATION_TYPES = [
        ('TASK_REMINDER', 'Task Reminder'),
        ('DOCUMENT_DUE', 'Document Due Notification'),
        ('WORKFLOW_OVERDUE', 'Workflow Overdue'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('HEALTH_CHECK', 'Health Check Alert'),
        ('BACKUP_STATUS', 'Backup Status'),
        ('MAINTENANCE', 'Maintenance Notification'),
    ]
    
    NOTIFICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='NORMAL')
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='queued_notifications')
    recipient_emails = models.JSONField(default=list, blank=True)  # Additional emails
    
    # Content
    subject = models.CharField(max_length=255)
    message = models.TextField()
    notification_data = models.JSONField(default=dict, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='PENDING')
    
    # Delivery details
    delivery_channels = models.JSONField(default=list, blank=True)  # email, in-app, etc.
    delivery_attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    error_message = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_notifications'
    )
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notification_queue'
        verbose_name = _('Notification Queue')
        verbose_name_plural = _('Notification Queue')
        ordering = ['scheduled_at', '-priority']
        indexes = [
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.status}"
    
    @property
    def is_overdue(self):
        """Check if notification is overdue for sending."""
        return (
            self.scheduled_at < timezone.now() and 
            self.status == 'PENDING'
        )
    
    @property
    def can_retry(self):
        """Check if notification can be retried."""
        return (
            self.status == 'FAILED' and 
            self.delivery_attempts < self.max_attempts
        )