"""
API endpoints for enhanced rejection workflow functionality.
Provides REST endpoints for React frontend to consume rejection history and recommendations.

FIXED VERSION: Added proper error handling and logging
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from apps.documents.models import Document
from .document_lifecycle import get_document_lifecycle_service
from apps.scheduler.notification_service import notification_service
import traceback
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rejection_history(request, document_id):
    """
    API endpoint to get rejection history for a document.
    Used by React frontend to show rejection details to authors.
    
    GET /api/v1/documents/{document_id}/rejection-history/
    """
    try:
        document = get_object_or_404(Document, uuid=document_id)
        lifecycle_service = get_document_lifecycle_service()
        
        rejection_history = lifecycle_service.get_rejection_history(document)
        
        return Response({
            'rejection_history': rejection_history,
            'has_rejections': len(rejection_history) > 0
        })
        
    except Exception as e:
        logger.error(f"Error getting rejection history for document {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_recommendations(request, document_id):
    """
    API endpoint to get assignment recommendations based on rejection history.
    Used by React frontend when showing reviewer/approver selection modals.
    
    GET /api/v1/documents/{document_id}/assignment-recommendations/
    """
    try:
        document = get_object_or_404(Document, uuid=document_id)
        lifecycle_service = get_document_lifecycle_service()
        
        recommendations = lifecycle_service.get_assignment_recommendations(document)
        
        # Add user-friendly summary
        summary = {
            'show_warning': recommendations['has_rejections'],
            'warning_message': None,
            'guidance': None
        }
        
        if recommendations['has_rejections']:
            latest = recommendations['latest_rejection']
            if latest:
                if latest['rejection_type'] == 'review':
                    summary['warning_message'] = f"This document was previously rejected during review by {latest['rejected_by']}"
                    summary['guidance'] = "Consider addressing the reviewer's concerns before resubmitting, or choose a different reviewer if needed."
                else:
                    summary['warning_message'] = f"This document was previously rejected during approval by {latest['rejected_by']}"
                    summary['guidance'] = "Consider addressing the approver's concerns and having it re-reviewed before resubmitting."
        
        return Response({
            'recommendations': recommendations,
            'summary': summary,
            'highlight_different_assignees': not (recommendations['recommendations']['prefer_same_reviewer'] or 
                                                 recommendations['recommendations']['prefer_same_approver'])
        })
        
    except Exception as e:
        logger.error(f"Error getting assignment recommendations for document {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_for_review_enhanced(request, document_id):
    """
    Enhanced submit for review with rejection awareness and warnings.
    Provides guidance when reassigning to previous rejectors.
    
    POST /api/v1/workflows/documents/{document_id}/submit-for-review-enhanced/
    Body: {
        "reviewer_id": "user_id",
        "comment": "optional comment",
        "acknowledge_warnings": false
    }
    
    FIXED: Added comprehensive error handling and logging
    """
    try:
        logger.info(f"submit_for_review_enhanced called for document {document_id}")
        logger.info(f"User: {request.user.username}, Data: {request.data}")
        
        document = get_object_or_404(Document, uuid=document_id)
        logger.info(f"Document found: {document.document_number}, Status: {document.status}")
        
        lifecycle_service = get_document_lifecycle_service()
        
        # Check permission
        if document.author != request.user:
            logger.warning(f"Permission denied: {request.user.username} is not author of {document.document_number}")
            return Response(
                {'error': 'Only document author can submit for review'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        reviewer_id = request.data.get('reviewer_id')
        comment = request.data.get('comment', '')
        acknowledge_warnings = request.data.get('acknowledge_warnings', False)
        
        logger.info(f"Reviewer ID: {reviewer_id}, Comment: {comment}, Acknowledge: {acknowledge_warnings}")
        
        if not reviewer_id:
            logger.warning("No reviewer_id provided")
            return Response(
                {'error': 'reviewer_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviewer = get_object_or_404(User, id=reviewer_id)
        logger.info(f"Reviewer found: {reviewer.username} ({reviewer.get_full_name()})")
        
        # Get recommendations and warnings - with error handling
        warnings = []
        try:
            logger.info("Getting assignment recommendations...")
            recommendations = lifecycle_service.get_assignment_recommendations(document)
            logger.info(f"Recommendations: {recommendations}")
            
            # Check if choosing DIFFERENT reviewer than who previously rejected - this needs guidance
            if (recommendations['previously_rejected_reviewers'] and 
                reviewer.username not in recommendations['previously_rejected_reviewers']):
                latest_rejection = recommendations['latest_rejection']
                if latest_rejection and latest_rejection['rejection_type'] == 'review':
                    previous_reviewer_name = latest_rejection.get('rejected_by', 'Previous reviewer')
                    warnings.append({
                        'type': 'different_reviewer_guidance',
                        'severity': 'medium',
                        'title': 'Guidance: Different Reviewer Selected',
                        'message': f"You're assigning to {reviewer.get_full_name()} instead of {previous_reviewer_name} who previously reviewed this document",
                        'rejection_comment': latest_rejection['comment'],
                        'rejection_date': latest_rejection['rejection_date'],
                        'suggestion': f"Make sure {reviewer.get_full_name()} understands the previous feedback and requirements"
                    })
        except Exception as rec_error:
            logger.warning(f"Error getting recommendations (non-critical): {str(rec_error)}")
            logger.warning(traceback.format_exc())
            # Continue without recommendations - this is not a critical error
        
        # If warnings exist and not acknowledged, return warnings for frontend confirmation
        if warnings and not acknowledge_warnings:
            logger.info("Returning warnings for user acknowledgment")
            return Response({
                'requires_confirmation': True,
                'warnings': warnings,
                'message': 'Please review the warnings and confirm assignment',
                'success': False
            }, status=status.HTTP_200_OK)
        
        # Proceed with assignment
        logger.info(f"Assigning reviewer {reviewer.username} to document")
        document.reviewer = reviewer
        document.save()
        logger.info("Document saved with reviewer assignment")
        
        # Submit for review
        logger.info("Calling lifecycle_service.submit_for_review...")
        success = lifecycle_service.submit_for_review(document, request.user, comment)
        logger.info(f"submit_for_review returned: {success}")
        
        if success:
            # Refresh document to get updated status
            document.refresh_from_db()
            logger.info(f"Document status after submit: {document.status}")
            
            # Send email notification to reviewer
            try:
                logger.info(f"Sending email notification to reviewer: {reviewer.email}")
                notification_service.send_task_email(reviewer, 'Review', document)
                logger.info(f"✅ Email notification sent successfully to {reviewer.email}")
            except Exception as email_error:
                logger.error(f"Failed to send email notification: {str(email_error)}")
                # Don't fail the workflow if email fails
            
            return Response({
                'success': True,
                'message': 'Document submitted for review successfully',
                'warnings_acknowledged': warnings,
                'reviewer': {
                    'id': reviewer.id,
                    'name': reviewer.get_full_name(),
                    'username': reviewer.username
                },
                'document_status': document.status
            })
        else:
            logger.error("submit_for_review returned False")
            return Response(
                {'error': 'Failed to submit document for review', 'success': False}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Unhandled exception in submit_for_review_enhanced: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e), 'success': False, 'traceback': traceback.format_exc()}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
