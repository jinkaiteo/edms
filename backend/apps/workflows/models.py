"""
Workflow Management Models for EDMS.

Implements Django-River workflow integration for document lifecycle
management with 21 CFR Part 11 compliance.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from river.models.fields.state import StateField
from river.models import State


User = get_user_model()


class WorkflowType(models.Model):
    """
    Workflow Type model for defining different workflow configurations.
    
    Manages different types of workflows like Review, Up-versioning,
    Obsolescence, and Termination workflows.
    """
    
    WORKFLOW_TYPES = [
        ('REVIEW', 'Review Workflow'),
        ('UP_VERSION', 'Up-versioning Workflow'),
        ('OBSOLETE', 'Obsolescence Workflow'),
        ('TERMINATE', 'Termination Workflow'),
        ('APPROVAL', 'Approval Workflow'),
        ('CHANGE', 'Change Control Workflow'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES)
    description = models.TextField(blank=True)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    allows_parallel = models.BooleanField(default=False)
    auto_transition = models.BooleanField(default=False)
    
    # Timing
    timeout_days = models.PositiveIntegerField(null=True, blank=True)
    reminder_days = models.PositiveIntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_types'
        verbose_name = _('Workflow Type')
        verbose_name_plural = _('Workflow Types')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"


class WorkflowInstance(models.Model):
    """
    Workflow Instance model for tracking active workflow processes.
    
    Tracks individual workflow executions with state management
    and audit trail for compliance.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow_type = models.ForeignKey(
        WorkflowType,
        on_delete=models.PROTECT,
        related_name='instances'
    )
    
    # River state field for workflow state management
    state = StateField()
    
    # Content object (typically Document)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE
    )
    object_id = models.CharField(max_length=100)
    content_object = models.GenericForeignKey('content_type', 'object_id')
    
    # Workflow context
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='initiated_workflows'
    )
    current_assignee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assigned_workflows'
    )
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completion_reason = models.CharField(max_length=200, blank=True)
    
    # Workflow data
    workflow_data = models.JSONField(default=dict, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_instances'
        verbose_name = _('Workflow Instance')
        verbose_name_plural = _('Workflow Instances')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['state', 'is_active']),
            models.Index(fields=['current_assignee', 'is_active']),
            models.Index(fields=['started_at']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.workflow_type.name} - {self.state}"
    
    @property
    def is_overdue(self):
        """Check if workflow is overdue."""
        return (
            self.due_date and 
            self.due_date < timezone.now() and 
            not self.is_completed
        )
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date."""
        if not self.due_date or self.is_completed:
            return None
        
        delta = self.due_date.date() - timezone.now().date()
        return delta.days
    
    def complete_workflow(self, reason='Completed'):
        """Mark workflow as completed."""
        self.is_completed = True
        self.is_active = False
        self.completed_at = timezone.now()
        self.completion_reason = reason
        self.save()


class WorkflowTransition(models.Model):
    """
    Workflow Transition model for tracking state changes.
    
    Maintains audit trail of all workflow transitions
    for compliance and tracking purposes.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='transitions'
    )
    
    # Transition details
    from_state = models.CharField(max_length=100)
    to_state = models.CharField(max_length=100)
    transition_name = models.CharField(max_length=100)
    
    # Actor information
    transitioned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='workflow_transitions'
    )
    transitioned_at = models.DateTimeField(auto_now_add=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    
    # Transition data
    comment = models.TextField(blank=True)
    transition_data = models.JSONField(default=dict, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_transitions'
        verbose_name = _('Workflow Transition')
        verbose_name_plural = _('Workflow Transitions')
        ordering = ['-transitioned_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'transitioned_at']),
            models.Index(fields=['transitioned_by', 'transitioned_at']),
            models.Index(fields=['from_state', 'to_state']),
        ]
    
    def __str__(self):
        return f"{self.from_state} → {self.to_state} by {self.transitioned_by.username}"


class WorkflowTask(models.Model):
    """
    Workflow Task model for individual tasks within workflows.
    
    Represents specific actions that users need to take
    as part of the workflow process.
    """
    
    TASK_TYPES = [
        ('REVIEW', 'Review Task'),
        ('APPROVE', 'Approval Task'),
        ('VALIDATE', 'Validation Task'),
        ('SIGN', 'Signature Task'),
        ('NOTIFY', 'Notification Task'),
        ('CUSTOM', 'Custom Task'),
    ]
    
    TASK_PRIORITIES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    TASK_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    
    # Task definition
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    priority = models.CharField(max_length=10, choices=TASK_PRIORITIES, default='NORMAL')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='workflow_tasks'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_workflow_tasks'
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='PENDING')
    completion_note = models.TextField(blank=True)
    
    # Task data
    task_data = models.JSONField(default=dict, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_tasks'
        verbose_name = _('Workflow Task')
        verbose_name_plural = _('Workflow Tasks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.assigned_to.username} ({self.status})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        return (
            self.due_date and 
            self.due_date < timezone.now() and 
            self.status in ['PENDING', 'IN_PROGRESS']
        )
    
    def complete_task(self, completion_note='', result_data=None):
        """Mark task as completed."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.completion_note = completion_note
        if result_data:
            self.result_data = result_data
        self.save()


class WorkflowRule(models.Model):
    """
    Workflow Rule model for defining conditional workflow behavior.
    
    Allows for dynamic workflow behavior based on conditions
    and business rules.
    """
    
    RULE_TYPES = [
        ('CONDITION', 'Conditional Rule'),
        ('VALIDATION', 'Validation Rule'),
        ('ASSIGNMENT', 'Assignment Rule'),
        ('NOTIFICATION', 'Notification Rule'),
        ('ESCALATION', 'Escalation Rule'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow_type = models.ForeignKey(
        WorkflowType,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    
    # Rule definition
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    
    # Rule conditions (stored as JSON)
    conditions = models.JSONField(default=dict)
    actions = models.JSONField(default=dict)
    
    # Rule execution
    is_active = models.BooleanField(default=True)
    execution_order = models.PositiveIntegerField(default=100)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_rules'
        verbose_name = _('Workflow Rule')
        verbose_name_plural = _('Workflow Rules')
        ordering = ['execution_order', 'name']
        indexes = [
            models.Index(fields=['workflow_type', 'is_active']),
            models.Index(fields=['rule_type', 'is_active']),
            models.Index(fields=['execution_order']),
        ]
    
    def __str__(self):
        return f"{self.workflow_type.name} - {self.name}"


class WorkflowNotification(models.Model):
    """
    Workflow Notification model for tracking notifications sent.
    
    Tracks all notifications sent during workflow execution
    for audit and follow-up purposes.
    """
    
    NOTIFICATION_TYPES = [
        ('ASSIGNMENT', 'Task Assignment'),
        ('REMINDER', 'Task Reminder'),
        ('ESCALATION', 'Task Escalation'),
        ('COMPLETION', 'Workflow Completion'),
        ('REJECTION', 'Workflow Rejection'),
        ('CANCELLATION', 'Workflow Cancellation'),
    ]
    
    NOTIFICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='workflow_notifications'
    )
    
    # Content
    subject = models.CharField(max_length=255)
    message = models.TextField()
    notification_data = models.JSONField(default=dict, blank=True)
    
    # Delivery
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='PENDING')
    error_message = models.TextField(blank=True)
    
    # Channels (email, in-app, etc.)
    channels = models.JSONField(default=list, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_notifications'
        verbose_name = _('Workflow Notification')
        verbose_name_plural = _('Workflow Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_instance', 'status']),
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username} - {self.status}"


class WorkflowTemplate(models.Model):
    """
    Workflow Template model for defining reusable workflow patterns.
    
    Provides templates for common workflow configurations
    that can be applied to different document types.
    """
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    workflow_type = models.CharField(max_length=20, choices=WorkflowType.WORKFLOW_TYPES)
    
    # Template definition
    states_config = models.JSONField(default=dict)
    transitions_config = models.JSONField(default=dict)
    tasks_config = models.JSONField(default=dict)
    rules_config = models.JSONField(default=dict)
    
    # Applicability
    document_types = models.ManyToManyField(
        'documents.DocumentType',
        blank=True,
        related_name='workflow_templates'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'workflow_templates'
        verbose_name = _('Workflow Template')
        verbose_name_plural = _('Workflow Templates')
        ordering = ['name']
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


# River workflow states for document management
DOCUMENT_STATES = [
    ('draft', 'Draft'),
    ('pending_review', 'Pending Review'),
    ('under_review', 'Under Review'),
    ('review_completed', 'Review Completed'),
    ('pending_approval', 'Pending Approval'),
    ('under_approval', 'Under Approval'),
    ('approved', 'Approved'),
    ('effective', 'Effective'),
    ('superseded', 'Superseded'),
    ('obsolete', 'Obsolete'),
    ('terminated', 'Terminated'),
]