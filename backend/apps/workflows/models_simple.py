"""
Simple Workflow Models for EDMS.

Contains only the essential models for the Simple Workflow approach:
- DocumentState
- DocumentWorkflow  
- DocumentTransition

These models provide the complete workflow functionality needed for EDMS
without the complexity of the River-based approach.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class DocumentState(models.Model):
    """Document workflow states aligned with EDMS specification."""
    
    # Document states from EDMS_details_workflow.txt specification
    DRAFT = 'DRAFT'
    PENDING_REVIEW = 'PENDING_REVIEW'
    UNDER_REVIEW = 'UNDER_REVIEW'
    REVIEWED = 'REVIEWED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    UNDER_APPROVAL = 'UNDER_APPROVAL'
    APPROVED_PENDING_EFFECTIVE = 'APPROVED_PENDING_EFFECTIVE'
    APPROVED_AND_EFFECTIVE = 'APPROVED_AND_EFFECTIVE'
    SUPERSEDED = 'SUPERSEDED'
    PENDING_OBSOLETE = 'PENDING_OBSOLETE'
    OBSOLETE = 'OBSOLETE'
    TERMINATED = 'TERMINATED'
    
    STATE_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_REVIEW, 'Pending Review'),
        (UNDER_REVIEW, 'Under Review'),
        (REVIEWED, 'Reviewed'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (UNDER_APPROVAL, 'Under Approval'),
        (APPROVED_PENDING_EFFECTIVE, 'Approved - Pending Effective'),
        (APPROVED_AND_EFFECTIVE, 'Approved and Effective'),
        (SUPERSEDED, 'Superseded'),
        (PENDING_OBSOLETE, 'Pending Obsolete'),
        (OBSOLETE, 'Obsolete'),
        (TERMINATED, 'Terminated'),
    ]
    
    code = models.CharField(max_length=50, choices=STATE_CHOICES, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    
    class Meta:
        app_label = "workflows"
        db_table = 'workflow_document_states'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DocumentWorkflow(models.Model):
    """Document Workflow model aligned with EDMS specification."""
    
    WORKFLOW_TYPES = [
        ('REVIEW', 'Review Workflow'),
        ('UP_VERSION', 'Up-versioning Workflow'),
        ('OBSOLETE', 'Obsolete Workflow'),
        ('TERMINATION', 'Termination Workflow'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document = models.OneToOneField(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='workflow'
    )
    
    # Workflow type and state
    workflow_type = models.CharField(max_length=50, choices=WORKFLOW_TYPES, default='REVIEW')
    current_state = models.ForeignKey(
        DocumentState,
        on_delete=models.PROTECT,
        related_name='workflows'
    )
    
    # Workflow participants
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='initiated_document_workflows'
    )
    current_assignee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assigned_document_workflows'
    )
    selected_reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='selected_reviewer_workflows'
    )
    selected_approver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='selected_approver_workflows'
    )
    
    # Timing and dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    effective_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when approved document becomes effective"
    )
    obsoleting_date = models.DateField(
        null=True,
        blank=True, 
        help_text="Date when document becomes obsolete"
    )
    
    # Workflow context and reasons
    workflow_data = models.JSONField(default=dict, blank=True)
    up_version_reason = models.TextField(
        blank=True,
        help_text="Reason for up-versioning (required for up-version workflow)"
    )
    obsoleting_reason = models.TextField(
        blank=True,
        help_text="Reason for obsoleting document"
    )
    termination_reason = models.TextField(
        blank=True,
        help_text="Reason for terminating workflow"
    )
    
    # Workflow status
    is_terminated = models.BooleanField(
        default=False,
        help_text="Whether workflow has been terminated by author"
    )
    last_approved_state = models.CharField(
        max_length=50,
        blank=True,
        help_text="Last approved state before termination"
    )
    
    class Meta:
        app_label = "workflows"
        db_table = 'document_workflows'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.document} - {self.current_state}"
    
    def transition_to(self, new_state_code, user, comment='', **kwargs):
        """Transition document to new state with EDMS validation."""
        current_state_code = self.current_state.code
        
        # EDMS-compliant state transition validation
        valid_transitions = {
            'DRAFT': ['PENDING_REVIEW'],
            'PENDING_REVIEW': ['UNDER_REVIEW', 'DRAFT'],
            'UNDER_REVIEW': ['REVIEWED', 'DRAFT'],
            'REVIEWED': ['PENDING_APPROVAL'], 
            'PENDING_APPROVAL': ['UNDER_APPROVAL', 'APPROVED_PENDING_EFFECTIVE', 'APPROVED_AND_EFFECTIVE', 'DRAFT'],
            'UNDER_APPROVAL': ['APPROVED_PENDING_EFFECTIVE', 'APPROVED_AND_EFFECTIVE', 'DRAFT'],
            'APPROVED_PENDING_EFFECTIVE': ['APPROVED_AND_EFFECTIVE'],
            'APPROVED_AND_EFFECTIVE': ['SUPERSEDED', 'PENDING_OBSOLETE'],
            'SUPERSEDED': [],
            'PENDING_OBSOLETE': ['OBSOLETE', 'APPROVED_AND_EFFECTIVE'],
            'OBSOLETE': [],
            'TERMINATED': []
        }
        
        # Validate transition
        allowed_transitions = valid_transitions.get(current_state_code, [])
        if new_state_code not in allowed_transitions:
            raise ValueError(
                f'Invalid workflow transition: {current_state_code} → {new_state_code}. '
                f'Valid transitions from {current_state_code}: {allowed_transitions}'
            )
        
        old_state = self.current_state
        new_state = DocumentState.objects.get(code=new_state_code)
        
        # Create transition record
        transition = DocumentTransition.objects.create(
            workflow=self,
            from_state=old_state,
            to_state=new_state,
            transitioned_by=user,
            comment=comment,
            transition_data=kwargs.get('transition_data', {})
        )
        
        # Update workflow state
        self.current_state = new_state
        self.current_assignee = kwargs.get('assignee', self.current_assignee)
        self.due_date = kwargs.get('due_date', self.due_date)
        self.save()
        
        return transition
    
    def get_valid_next_states(self):
        """Get list of valid next states for current workflow state."""
        valid_transitions = {
            'DRAFT': ['PENDING_REVIEW'],
            'PENDING_REVIEW': ['UNDER_REVIEW', 'DRAFT'],
            'UNDER_REVIEW': ['REVIEWED', 'DRAFT'],
            'REVIEWED': ['PENDING_APPROVAL'], 
            'PENDING_APPROVAL': ['UNDER_APPROVAL', 'APPROVED_PENDING_EFFECTIVE', 'APPROVED_AND_EFFECTIVE', 'DRAFT'],
            'UNDER_APPROVAL': ['APPROVED_PENDING_EFFECTIVE', 'APPROVED_AND_EFFECTIVE', 'DRAFT'],
            'APPROVED_PENDING_EFFECTIVE': ['APPROVED_AND_EFFECTIVE'],
            'APPROVED_AND_EFFECTIVE': ['SUPERSEDED', 'PENDING_OBSOLETE'],
            'SUPERSEDED': [],
            'PENDING_OBSOLETE': ['OBSOLETE', 'APPROVED_AND_EFFECTIVE'],
            'OBSOLETE': [],
            'TERMINATED': []
        }
        
        current_state_code = self.current_state.code
        return valid_transitions.get(current_state_code, [])


class DocumentTransition(models.Model):
    """Document state transitions for audit trail."""
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    workflow = models.ForeignKey(
        DocumentWorkflow,
        on_delete=models.CASCADE,
        related_name='transitions'
    )
    
    # Transition details
    from_state = models.ForeignKey(
        DocumentState,
        on_delete=models.PROTECT,
        related_name='transitions_from'
    )
    to_state = models.ForeignKey(
        DocumentState,
        on_delete=models.PROTECT,
        related_name='transitions_to'
    )
    
    # Actor information
    transitioned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='document_transitions'
    )
    transitioned_at = models.DateTimeField(auto_now_add=True)
    
    # Context
    comment = models.TextField(blank=True)
    transition_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = "workflows"
        db_table = 'document_transitions'
        ordering = ['-transitioned_at']
    
    def __str__(self):
        return f"{self.from_state} → {self.to_state} by {self.transitioned_by.username}"