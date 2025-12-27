"""
Viewflow-specific models for EDMS document workflows.
Integrates with Viewflow process management system.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from viewflow.workflow.models import Process
from django.utils import timezone

User = get_user_model()


class DocumentProcess(Process):
    """
    Viewflow Process model for document workflows.
    Extends the base Viewflow Process with EDMS-specific fields.
    """
    
    # Process identification
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Document being processed
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='processes',
        help_text="Document being processed in this workflow"
    )
    
    # For obsolescence workflows - target document to be obsoleted
    target_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='obsolescence_processes',
        null=True,
        blank=True,
        help_text="Document to be made obsolete (for obsolescence workflows)"
    )
    
    # Workflow assignments
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_document_reviews',
        null=True,
        blank=True,
        help_text="User assigned to review this document"
    )
    
    assigned_approver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_document_approvals',
        null=True,
        blank=True,
        help_text="User assigned to approve this document"
    )
    
    # Decision tracking
    DECISION_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('NEEDS_REVISION', 'Needs Revision'),
        ('REJECTED', 'Rejected'),
    ]
    
    review_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default='PENDING',
        help_text="Review decision"
    )
    
    approval_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default='PENDING',
        help_text="Approval decision"
    )
    
    final_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES + [('OBSOLETED', 'Obsoleted')],
        default='PENDING',
        help_text="Final workflow decision"
    )
    
    # Comments and notes
    review_comments = models.TextField(
        blank=True,
        help_text="Comments from reviewer"
    )
    
    approval_comments = models.TextField(
        blank=True,
        help_text="Comments from approver"
    )
    
    revision_notes = models.TextField(
        blank=True,
        help_text="Notes for revision requirements"
    )
    
    obsolescence_notes = models.TextField(
        blank=True,
        help_text="Notes for obsolescence workflow"
    )
    
    # Timing and deadlines
    review_due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Due date for review completion"
    )
    
    approval_due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Due date for approval completion"
    )
    
    # Workflow metadata
    workflow_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional workflow-specific data"
    )
    
    # Compliance tracking
    compliance_checked = models.BooleanField(
        default=False,
        help_text="Whether compliance requirements have been verified"
    )
    
    signature_required = models.BooleanField(
        default=True,
        help_text="Whether electronic signature is required"
    )
    
    class Meta:
        db_table = 'viewflow_document_processes'
        ordering = ['-created']
        
    def __str__(self):
        return f"Process {self.pk} - {self.document.title} ({self.flow_class})"
    
    @property
    def current_state_display(self):
        """Human-readable current workflow state."""
        if hasattr(self, 'task_set'):
            current_tasks = self.task_set.filter(finished__isnull=True)
            if current_tasks.exists():
                return current_tasks.first().flow_task.name.replace('_', ' ').title()
        return "Completed" if self.finished else "In Progress"
    
    def get_next_assignee(self):
        """Get the user who should handle the next task."""
        if hasattr(self, 'task_set'):
            current_tasks = self.task_set.filter(finished__isnull=True)
            if current_tasks.exists():
                task = current_tasks.first()
                if hasattr(task, 'owner') and task.owner:
                    return task.owner
                
        # Fallback logic
        if self.review_decision == 'PENDING' and self.assigned_reviewer:
            return self.assigned_reviewer
        elif self.review_decision == 'APPROVED' and self.approval_decision == 'PENDING':
            return self.assigned_approver
        
        return None
    
    def is_overdue(self):
        """Check if any current tasks are overdue."""
        from django.utils import timezone
        now = timezone.now()
        
        if self.review_decision == 'PENDING' and self.review_due_date:
            return now > self.review_due_date
        elif self.approval_decision == 'PENDING' and self.approval_due_date:
            return now > self.approval_due_date
            
        return False


class WorkflowTemplate(models.Model):
    """
    Template for common workflow configurations.
    Allows pre-configuration of workflow settings for different document types.
    """
    
    FLOW_CHOICES = [
        ('DocumentReviewFlow', 'Document Review Flow'),
        ('DocumentUpVersionFlow', 'Document Up-Version Flow'),
        ('DocumentObsoleteFlow', 'Document Obsolete Flow'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    flow_class_name = models.CharField(max_length=50, choices=FLOW_CHOICES)
    
    # Default assignments
    default_reviewer_group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        related_name='workflow_templates_reviewer',
        null=True,
        blank=True
    )
    
    default_approver_group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        related_name='workflow_templates_approver',
        null=True,
        blank=True
    )
    
    # Default timing
    default_review_days = models.PositiveIntegerField(default=5)
    default_approval_days = models.PositiveIntegerField(default=3)
    
    # Configuration
    requires_signature = models.BooleanField(default=True)
    compliance_required = models.BooleanField(default=True)
    
    # Applicable document types
    document_types = models.ManyToManyField(
        'documents.DocumentType',
        blank=True,
        help_text="Document types that use this workflow template"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'workflow_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_flow_class_name_display()})"