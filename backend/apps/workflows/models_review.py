"""
DocumentReview Model for Periodic Review System

Tracks the history of periodic reviews for compliance and audit purposes.
This is separate from the DocumentWorkflow model which tracks approval workflows.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


__all__ = ['DocumentReview']


class DocumentReview(models.Model):
    """
    Track periodic review history for compliance.
    
    Each time a document undergoes periodic review, a DocumentReview
    record is created to maintain a complete audit trail.
    """
    
    REVIEW_OUTCOMES = [
        ('CONFIRMED', 'Confirmed - No changes needed'),
        ('UPVERSION_REQUIRED', 'Up-Version Required'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    # Document being reviewed
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='periodic_reviews',
        help_text='Document that was reviewed'
    )
    
    # Review details
    review_date = models.DateField(
        auto_now_add=True,
        db_index=True,
        help_text='Date when review was completed'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='completed_reviews',
        help_text='User who completed the review'
    )
    
    # Review outcome
    outcome = models.CharField(
        max_length=20,
        choices=REVIEW_OUTCOMES,
        help_text='Result of the periodic review'
    )
    comments = models.TextField(
        blank=True,
        help_text='Reviewer comments and observations'
    )
    
    # Next review scheduling
    next_review_date = models.DateField(
        help_text='Scheduled date for next periodic review'
    )
    
    # Link to new version if up-versioned
    new_version = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_from_review',
        help_text='New document version created from this review (if outcome was UPVERSIONED)'
    )
    
    # Workflow integration
    workflow = models.ForeignKey(
        'workflows.DocumentWorkflow',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='periodic_review',
        help_text='Associated workflow if periodic review triggered a workflow'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional review metadata (checklist results, etc.)'
    )
    
    class Meta:
        app_label = 'workflows'
        db_table = 'document_reviews'
        verbose_name = _('Document Review')
        verbose_name_plural = _('Document Reviews')
        ordering = ['-review_date', '-created_at']
        indexes = [
            models.Index(fields=['document', 'review_date']),
            models.Index(fields=['reviewed_by', 'review_date']),
            models.Index(fields=['outcome']),
            models.Index(fields=['next_review_date']),
        ]
    
    def __str__(self):
        return f"{self.document.document_number} - Review on {self.review_date} by {self.reviewed_by.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Override save to update parent document's review fields."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update document's review tracking fields
            self.document.last_review_date = self.review_date
            self.document.last_reviewed_by = self.reviewed_by
            self.document.next_review_date = self.next_review_date
            self.document.save(update_fields=['last_review_date', 'last_reviewed_by', 'next_review_date'])
