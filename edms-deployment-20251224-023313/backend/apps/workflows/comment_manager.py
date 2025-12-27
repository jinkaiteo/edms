"""
Workflow Comment Manager for EDMS.

Implements comment system for reviewers and approvers as required by 
EDMS_details_workflow.txt lines 7, 12.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class WorkflowComment(models.Model):
    """Comments from reviewers and approvers during workflow."""
    
    COMMENT_TYPES = [
        ('REVIEW', 'Review Comment'),
        ('APPROVAL', 'Approval Comment'),
        ('REVISION', 'Revision Request'),
        ('GENERAL', 'General Comment'),
    ]
    
    DECISION_TYPES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_REVISION', 'Needs Revision'),
        ('INFO_ONLY', 'Information Only'),
    ]
    
    workflow = models.ForeignKey(
        'workflows.DocumentWorkflow',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='workflow_comments'
    )
    
    # Comment details
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPES)
    comment = models.TextField(help_text="Comment from reviewer/approver")
    decision = models.CharField(
        max_length=20, 
        choices=DECISION_TYPES, 
        null=True, 
        blank=True
    )
    
    # Document section reference (optional)
    document_section = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specific section of document being commented on"
    )
    page_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Page number for comment reference"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = "workflows"
        db_table = 'workflow_comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', 'comment_type']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.comment_type} by {self.user.username} on {self.workflow.document.title}"


class WorkflowCommentManager:
    """Manager for workflow comments."""
    
    @staticmethod
    def add_comment(workflow, user, comment_type, comment, decision=None, **kwargs):
        """
        Add comment to workflow.
        
        Args:
            workflow: DocumentWorkflow instance
            user: User making the comment
            comment_type: Type of comment (REVIEW, APPROVAL, etc.)
            comment: Comment text
            decision: Decision made (APPROVED, REJECTED, etc.)
            **kwargs: Additional fields (document_section, page_number)
        
        Returns:
            WorkflowComment instance
        """
        workflow_comment = WorkflowComment.objects.create(
            workflow=workflow,
            user=user,
            comment_type=comment_type,
            comment=comment,
            decision=decision,
            document_section=kwargs.get('document_section', ''),
            page_number=kwargs.get('page_number')
        )
        
        return workflow_comment
    
    @staticmethod
    def get_review_comments(workflow):
        """Get all review comments for a workflow."""
        return WorkflowComment.objects.filter(
            workflow=workflow,
            comment_type='REVIEW'
        ).order_by('created_at')
    
    @staticmethod
    def get_approval_comments(workflow):
        """Get all approval comments for a workflow."""
        return WorkflowComment.objects.filter(
            workflow=workflow,
            comment_type='APPROVAL'
        ).order_by('created_at')
    
    @staticmethod
    def get_all_comments(workflow):
        """Get all comments for a workflow ordered by creation date."""
        return WorkflowComment.objects.filter(
            workflow=workflow
        ).order_by('created_at')
    
    @staticmethod
    def get_user_comments(workflow, user):
        """Get all comments from a specific user for a workflow."""
        return WorkflowComment.objects.filter(
            workflow=workflow,
            user=user
        ).order_by('created_at')
    
    @staticmethod
    def has_reviewer_comments(workflow):
        """Check if workflow has any review comments."""
        return WorkflowComment.objects.filter(
            workflow=workflow,
            comment_type='REVIEW'
        ).exists()
    
    @staticmethod
    def has_approver_comments(workflow):
        """Check if workflow has any approval comments."""
        return WorkflowComment.objects.filter(
            workflow=workflow,
            comment_type='APPROVAL'
        ).exists()
    
    @staticmethod
    def get_comments_summary(workflow):
        """
        Get summary of comments for workflow.
        
        Returns:
            dict: Summary of comments by type and decision
        """
        comments = WorkflowComment.objects.filter(workflow=workflow)
        
        summary = {
            'total_comments': comments.count(),
            'review_comments': comments.filter(comment_type='REVIEW').count(),
            'approval_comments': comments.filter(comment_type='APPROVAL').count(),
            'approved_decisions': comments.filter(decision='APPROVED').count(),
            'rejected_decisions': comments.filter(decision='REJECTED').count(),
            'revision_requests': comments.filter(decision='NEEDS_REVISION').count(),
            'latest_comment': comments.order_by('-created_at').first()
        }
        
        return summary