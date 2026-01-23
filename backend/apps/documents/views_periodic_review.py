"""
Periodic Review API Views

Provides API endpoints for initiating and completing periodic document reviews.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta

from apps.documents.models import Document
from apps.workflows.models import DocumentWorkflow
from apps.scheduler.services.periodic_review_service import get_periodic_review_service


class PeriodicReviewMixin:
    """
    Mixin for DocumentViewSet to add periodic review endpoints.
    
    Add this to DocumentViewSet in views.py:
    class DocumentViewSet(PeriodicReviewMixin, viewsets.ModelViewSet):
    """
    
    @action(detail=True, methods=['post'], url_path='initiate-periodic-review')
    def initiate_periodic_review(self, request, uuid=None):
        """
        Manually initiate periodic review for a document.
        
        POST /api/v1/documents/{uuid}/initiate-periodic-review/
        
        Body: {}  # No body required
        
        Returns:
            201: Review workflow created successfully
            400: Document not eligible for periodic review
            403: User not authorized
        """
        document = self.get_object()
        user = request.user
        
        # Validate document is EFFECTIVE
        if document.status != 'EFFECTIVE':
            return Response(
                {'error': 'Only EFFECTIVE documents can undergo periodic review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a stakeholder (author, reviewer, or approver)
        is_stakeholder = (
            document.author == user or
            document.reviewer == user or
            document.approver == user or
            user.is_superuser
        )
        
        if not is_stakeholder:
            return Response(
                {'error': 'Only stakeholders can initiate periodic review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already has active periodic review
        active_review = DocumentWorkflow.objects.filter(
            document=document,
            workflow_type='PERIODIC_REVIEW',
            is_terminated=False
        ).exists()
        
        if active_review:
            return Response(
                {'error': 'Document already has an active periodic review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create periodic review workflow
        periodic_review_service = get_periodic_review_service()
        workflow = periodic_review_service._create_periodic_review_workflow(document)
        
        # Create notifications
        notification_count = periodic_review_service._create_review_notifications(workflow, document)
        
        return Response({
            'message': 'Periodic review initiated successfully',
            'workflow_id': workflow.id,
            'workflow_uuid': str(workflow.uuid),
            'notifications_sent': notification_count,
            'due_date': workflow.due_date.isoformat()
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='complete-periodic-review')
    def complete_periodic_review(self, request, uuid=None):
        """
        Complete periodic review for a document.
        
        POST /api/v1/documents/{uuid}/complete-periodic-review/
        
        Body:
        {
            "outcome": "CONFIRMED" | "MINOR_UPVERSION" | "MAJOR_UPVERSION",
            "comments": "Review comments",
            "next_review_months": 12  // Optional, defaults to document's review_period_months
        }
        
        Returns:
            200: Review completed successfully
            400: Invalid data or document not under review
            403: User not authorized
        """
        document = self.get_object()
        user = request.user
        
        # Validate user is a stakeholder
        is_stakeholder = (
            document.author == user or
            document.reviewer == user or
            document.approver == user or
            user.is_superuser
        )
        
        if not is_stakeholder:
            return Response(
                {'error': 'Only stakeholders can complete periodic review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get review data
        outcome = request.data.get('outcome')
        comments = request.data.get('comments', '')
        next_review_months = request.data.get('next_review_months')
        
        # Validate outcome
        if not outcome:
            return Response(
                {'error': 'Outcome is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if outcome not in ['CONFIRMED', 'UPVERSION_REQUIRED']:
            return Response(
                {'error': 'Invalid outcome. Must be CONFIRMED or UPVERSION_REQUIRED'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Complete the review
        try:
            periodic_review_service = get_periodic_review_service()
            result = periodic_review_service.complete_periodic_review(
                document=document,
                user=user,
                outcome=outcome,
                comments=comments,
                next_review_months=next_review_months
            )
            
            return Response({
                'message': 'Periodic review completed successfully',
                **result
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to complete review: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='review-history')
    def get_review_history(self, request, uuid=None):
        """
        Get periodic review history for a document.
        
        GET /api/v1/documents/{uuid}/review-history/
        
        Returns:
            200: List of review records
        """
        document = self.get_object()
        
        from apps.workflows.models_review import DocumentReview
        
        reviews = DocumentReview.objects.filter(
            document=document
        ).select_related('reviewed_by', 'new_version').order_by('-review_date')
        
        review_data = []
        for review in reviews:
            review_data.append({
                'uuid': str(review.uuid),
                'review_date': review.review_date.isoformat(),
                'reviewed_by': {
                    'id': review.reviewed_by.id,
                    'username': review.reviewed_by.username,
                    'full_name': review.reviewed_by.get_full_name(),
                },
                'outcome': review.outcome,
                'outcome_display': review.get_outcome_display(),
                'comments': review.comments,
                'next_review_date': review.next_review_date.isoformat(),
                'new_version': {
                    'uuid': str(review.new_version.uuid),
                    'document_number': review.new_version.document_number,
                } if review.new_version else None,
            })
        
        return Response({
            'document_uuid': str(document.uuid),
            'document_number': document.document_number,
            'review_count': len(review_data),
            'reviews': review_data
        })
