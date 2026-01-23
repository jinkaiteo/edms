"""
Periodic Review Service

Handles the business logic for document periodic reviews:
- Monitoring review due dates
- Creating review notifications
- Processing review completions
"""

from datetime import date, timedelta
from typing import Dict, List, Any
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.documents.models import Document
from apps.workflows.models import DocumentWorkflow, DocumentState
from apps.workflows.models_review import DocumentReview

User = get_user_model()


class PeriodicReviewService:
    """Service for managing periodic document reviews."""
    
    def process_periodic_reviews(self) -> Dict[str, Any]:
        """
        Check for documents that need periodic review.
        
        This runs daily via Celery Beat scheduler.
        
        Returns:
            dict: Processing results with counts and errors
        """
        today = date.today()
        
        # Find documents needing periodic review
        documents_due = Document.objects.filter(
            status='EFFECTIVE',
            next_review_date__lte=today,
            is_active=True
        ).select_related('author', 'reviewer', 'approver')
        
        results = {
            'total_checked': documents_due.count(),
            'notifications_created': 0,
            'workflows_created': 0,
            'errors': [],
            'processed_documents': []
        }
        
        for document in documents_due:
            try:
                # Check if already has active periodic review workflow
                active_review = DocumentWorkflow.objects.filter(
                    document=document,
                    workflow_type='PERIODIC_REVIEW',
                    is_terminated=False
                ).exists()
                
                if active_review:
                    # Skip if already under review
                    continue
                
                # Create periodic review workflow
                workflow = self._create_periodic_review_workflow(document)
                
                # Create notifications for stakeholders
                notification_count = self._create_review_notifications(workflow, document)
                
                results['workflows_created'] += 1
                results['notifications_created'] += notification_count
                results['processed_documents'].append({
                    'document_number': document.document_number,
                    'title': document.title,
                    'due_date': document.next_review_date.isoformat()
                })
                
            except Exception as e:
                results['errors'].append({
                    'document_number': document.document_number,
                    'error': str(e)
                })
        
        return results
    
    def _create_periodic_review_workflow(self, document: Document) -> DocumentWorkflow:
        """
        Create a periodic review workflow for a document.
        
        Args:
            document: Document to review
            
        Returns:
            DocumentWorkflow: Created workflow instance
        """
        # Get PERIODIC_REVIEW state (will be created by migration/setup)
        review_state, _ = DocumentState.objects.get_or_create(
            code='UNDER_PERIODIC_REVIEW',
            defaults={
                'name': 'Under Periodic Review',
                'description': 'Document is undergoing periodic review',
                'is_initial': False,
                'is_final': False
            }
        )
        
        # Create workflow
        workflow = DocumentWorkflow.objects.create(
            document=document,
            workflow_type='PERIODIC_REVIEW',
            current_state=review_state,
            initiated_by=document.author,  # System initiated, but attribute to author
            current_assignee=document.author,  # Assign to document owner first
            due_date=date.today() + timedelta(days=30),  # 30 days to complete review
            workflow_data={
                'review_type': 'periodic',
                'original_next_review_date': document.next_review_date.isoformat() if document.next_review_date else None,
                'review_period_months': document.review_period_months
            }
        )
        
        return workflow
    
    def _create_review_notifications(self, workflow: DocumentWorkflow, document: Document) -> int:
        """
        Create notifications for document stakeholders about periodic review.
        
        Args:
            workflow: Created workflow instance
            document: Document being reviewed
            
        Returns:
            int: Number of notifications created
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Collect stakeholders
        stakeholders = set()
        if document.author:
            stakeholders.add(document.author)
        if document.reviewer:
            stakeholders.add(document.reviewer)
        if document.approver:
            stakeholders.add(document.approver)
        
        # Log notification creation (actual email notifications can be added later)
        notification_count = 0
        for user in stakeholders:
            try:
                logger.info(
                    f"Periodic review notification: {document.document_number} - "
                    f"Assigned to {user.username} (workflow ID: {workflow.id})"
                )
                notification_count += 1
                
                # TODO: Send email notification when SMTP is configured
                # notification_service.send_periodic_review_email(user, document, workflow)
                
            except Exception as e:
                logger.error(f"Failed to log notification for {user.username}: {str(e)}")
        
        return notification_count
    
    def complete_periodic_review(
        self, 
        document: Document, 
        user: User, 
        outcome: str,
        comments: str = '',
        next_review_months: int = None
    ) -> Dict[str, Any]:
        """
        Process periodic review completion.
        
        Args:
            document: Document being reviewed
            user: User completing the review
            outcome: Review outcome (CONFIRMED, MINOR_UPVERSION, or MAJOR_UPVERSION)
            comments: Review comments
            next_review_months: Override default review period
            
        Returns:
            dict: Processing results including new version info if up-versioned
        """
        with transaction.atomic():
            # Validate outcome
            valid_outcomes = ['CONFIRMED', 'UPVERSION_REQUIRED']
            if outcome not in valid_outcomes:
                raise ValueError(f"Invalid outcome. Must be one of: {', '.join(valid_outcomes)}")
            
            # Calculate next review date
            if next_review_months is None:
                next_review_months = document.review_period_months
            
            next_review_date = date.today() + timedelta(days=30 * next_review_months)
            
            # For up-versioning outcomes, we don't auto-create versions anymore
            # Frontend will handle version creation through the version modal
            # We just record the review outcome
            new_version = None
            new_workflow = None
            
            # Create review record
            review = DocumentReview.objects.create(
                document=document,
                reviewed_by=user,
                outcome=outcome,
                comments=comments,
                next_review_date=next_review_date,
                new_version=new_version,  # Will be null for now, linked later from version modal
                metadata={
                    'review_period_months': next_review_months,
                    'previous_review_date': document.last_review_date.isoformat() if document.last_review_date else None,
                    'requires_upversion': outcome == 'UPVERSION_REQUIRED',
                    'note': 'Up-version to be created through version modal' if outcome == 'UPVERSION_REQUIRED' else None
                }
            )
            
            # Get and terminate periodic review workflow
            workflow = DocumentWorkflow.objects.filter(
                document=document,
                workflow_type='PERIODIC_REVIEW',
                is_terminated=False
            ).first()
            
            if workflow:
                # Link review to workflow
                review.workflow = workflow
                review.save(update_fields=['workflow'])
                
                # Terminate the periodic review workflow
                workflow.is_terminated = True
                workflow.save(update_fields=['is_terminated'])
            
            # Document fields are updated automatically by DocumentReview.save()
            
            result = {
                'success': True,
                'review_id': review.id,
                'review_uuid': str(review.uuid),
                'outcome': outcome,
                'next_review_date': next_review_date.isoformat(),
                'document_updated': True,
                'requires_upversion': outcome == 'UPVERSION_REQUIRED',
                'message': 'Periodic review recorded. Please create new version through version modal.' if outcome == 'UPVERSION_REQUIRED' else 'Periodic review completed successfully.'
            }
            
            return result


# Global service instance
_periodic_review_service = None


def get_periodic_review_service() -> PeriodicReviewService:
    """Get the global periodic review service instance."""
    global _periodic_review_service
    if _periodic_review_service is None:
        _periodic_review_service = PeriodicReviewService()
    return _periodic_review_service
