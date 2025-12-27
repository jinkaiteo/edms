"""
API endpoints for enhanced rejection workflow functionality.
Provides REST endpoints for React frontend to consume rejection history and recommendations.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from apps.documents.models import Document
from .document_lifecycle import get_document_lifecycle_service

User = get_user_model()


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
        
        # Check permission - author or admin can view rejection history
        if not (document.author == request.user or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        rejection_history = lifecycle_service.get_rejection_history(document)
        
        return Response({
            'document_id': str(document.uuid),
            'document_number': document.document_number,
            'document_title': document.title,
            'rejection_history': rejection_history,
            'total_rejections': len(rejection_history),
            'success': True
        })
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_recommendations(request, document_id):
    """
    API endpoint to get smart assignment recommendations based on rejection history.
    Used by React frontend when showing reviewer/approver selection modals.
    
    GET /api/v1/documents/{document_id}/assignment-recommendations/
    """
    try:
        document = get_object_or_404(Document, uuid=document_id)
        lifecycle_service = get_document_lifecycle_service()
        
        # Check permission - author or admin can view recommendations
        if not (document.author == request.user or request.user.is_superuser):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        recommendations = lifecycle_service.get_assignment_recommendations(document)
        
        # Add user-friendly warnings for frontend display
        warnings = []
        if recommendations['has_rejections']:
            latest = recommendations['latest_rejection']
            if latest:
                warnings.append({
                    'type': 'rejection_history',
                    'title': 'Document Previously Rejected',
                    'message': f"This document was last rejected during {latest['rejection_type']} by {latest['rejected_by']}",
                    'suggestion': 'Consider reviewing the rejection comments before reassigning.',
                    'rejection_comment': latest['comment'],
                    'rejection_date': latest['rejection_date']
                })
        
        return Response({
            'document_id': str(document.uuid),
            'recommendations': recommendations,
            'warnings': warnings,
            'ui_guidance': {
                'show_rejection_history_link': recommendations['has_rejections'],
                'highlight_different_assignees': not (recommendations['recommendations']['prefer_same_reviewer'] or 
                                                     recommendations['recommendations']['prefer_same_approver']),
                'show_address_concerns_reminder': recommendations['recommendations']['address_concerns_first']
            },
            'success': True
        })
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_for_review_enhanced(request, document_id):
    """
    Enhanced submit for review with rejection awareness and warnings.
    Provides guidance when reassigning to previous rejectors.
    
    POST /api/v1/documents/{document_id}/submit-for-review-enhanced/
    Body: {
        "reviewer_id": "user_id",
        "comment": "optional comment",
        "acknowledge_warnings": false
    }
    """
    try:
        document = get_object_or_404(Document, uuid=document_id)
        lifecycle_service = get_document_lifecycle_service()
        
        # Check permission
        if document.author != request.user:
            return Response(
                {'error': 'Only document author can submit for review'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        reviewer_id = request.data.get('reviewer_id')
        comment = request.data.get('comment', '')
        acknowledge_warnings = request.data.get('acknowledge_warnings', False)
        
        if not reviewer_id:
            return Response(
                {'error': 'reviewer_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviewer = get_object_or_404(User, id=reviewer_id)
        
        # Get recommendations and warnings
        recommendations = lifecycle_service.get_assignment_recommendations(document)
        warnings = []
        
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
        
        # If warnings exist and not acknowledged, return warnings for frontend confirmation
        if warnings and not acknowledge_warnings:
            return Response({
                'requires_confirmation': True,
                'warnings': warnings,
                'message': 'Please review the warnings and confirm assignment',
                'success': False
            }, status=status.HTTP_200_OK)
        
        # Proceed with assignment
        document.reviewer = reviewer
        document.save()
        
        # Submit for review
        success = lifecycle_service.submit_for_review(document, request.user, comment)
        
        if success:
            return Response({
                'success': True,
                'message': 'Document submitted for review successfully',
                'warnings_acknowledged': warnings,
                'reviewer': {
                    'id': reviewer.id,
                    'name': reviewer.get_full_name(),
                    'username': reviewer.username
                }
            })
        else:
            return Response(
                {'error': 'Failed to submit document for review', 'success': False}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )