"""
Document Termination API Views

Provides API endpoints for document termination functionality.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Document
from .serializers import DocumentListSerializer as DocumentSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminate_document(request, document_id):
    """
    Terminate a document (author only, pre-effective status only).
    
    POST /api/v1/documents/{id}/terminate/
    Body: { "reason": "Termination reason" }
    """
    try:
        # Get document
        document = get_object_or_404(Document, id=document_id)
        
        # Check if user can terminate
        if not document.can_terminate(request.user):
            if document.author != request.user:
                return Response(
                    {'error': 'Only the document author can terminate their document'},
                    status=status.HTTP_403_FORBIDDEN
                )
            else:
                return Response(
                    {'error': f'Document cannot be terminated in {document.status} status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get termination reason
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response(
                {'error': 'Termination reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store IP and user agent for audit trail
        request.user._current_ip = request.META.get('REMOTE_ADDR')
        request.user._current_user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Terminate document
        document.terminate_document(request.user, reason)
        
        # Return updated document
        serializer = DocumentSerializer(document)
        
        return Response({
            'message': f'Document {document.document_number} has been terminated',
            'document': serializer.data,
            'terminated_at': timezone.now().isoformat(),
            'terminated_by': request.user.get_full_name() or request.user.username,
            'reason': reason
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to terminate document: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def can_terminate_document(request, document_id):
    """
    Check if the current user can terminate a document.
    
    GET /api/v1/documents/{id}/can-terminate/
    """
    try:
        document = get_object_or_404(Document, id=document_id)
        
        can_terminate = document.can_terminate(request.user)
        
        response_data = {
            'can_terminate': can_terminate,
            'document_id': document.id,
            'document_number': document.document_number,
            'current_status': document.status,
            'is_author': document.author == request.user
        }
        
        if not can_terminate:
            if document.author != request.user:
                response_data['reason'] = 'Only the document author can terminate their document'
            else:
                response_data['reason'] = f'Document cannot be terminated in {document.status} status'
                response_data['terminable_statuses'] = ['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'PENDING_APPROVAL']
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to check termination permission: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )