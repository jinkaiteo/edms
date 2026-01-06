"""
Workflow History API Views
Provides API endpoints to access document workflow transition history for frontend display
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.documents.models import Document
from .models import DocumentWorkflow, DocumentTransition


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_workflow_history(request, document_id):
    """
    Get complete workflow transition history for a document.
    
    GET /api/v1/workflows/documents/{document_id}/history/
    
    Returns:
    {
        "document": {
            "uuid": "...",
            "document_number": "SOP-2025-0007-v01.00",
            "title": "SOP201",
            "current_status": "APPROVED_AND_EFFECTIVE"
        },
        "workflow": {
            "id": 106,
            "current_state": "APPROVED_AND_EFFECTIVE",
            "is_terminated": false,
            "created_at": "2025-12-02T07:00:00Z"
        },
        "transitions": [
            {
                "id": 333,
                "transitioned_at": "2025-12-02T07:00:35Z",
                "transitioned_by": {
                    "id": 14,
                    "username": "author01",
                    "first_name": "David",
                    "last_name": "Brown",
                    "full_name": "David Brown"
                },
                "from_state": {
                    "code": "DRAFT",
                    "name": "Draft"
                },
                "to_state": {
                    "code": "PENDING_REVIEW", 
                    "name": "Pending Review"
                },
                "comment": "For your rejection"
            },
            ...
        ],
        "statistics": {
            "total_transitions": 14,
            "total_rejections": 2,
            "total_approvals": 2,
            "workflow_duration_days": 0,
            "current_state_duration_hours": 5
        }
    }
    """
    try:
        # Get the document
        document = get_object_or_404(Document, uuid=document_id)
        
        # Check permissions - user should be able to view workflow history for documents they have access to
        # For now, allow document author, reviewer, approver, or admin
        user_can_view = (
            document.author == request.user or
            document.reviewer == request.user or
            document.approver == request.user or
            request.user.is_superuser or
            request.user.groups.filter(name__in=['Document Reviewer', 'Document Approver', 'Senior Document Approver']).exists()
        )
        
        if not user_can_view:
            return Response(
                {'error': 'You do not have permission to view workflow history for this document'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the workflow
        workflow = DocumentWorkflow.objects.filter(document=document).first()
        
        if not workflow:
            return Response({
                'document': {
                    'uuid': str(document.uuid),
                    'document_number': document.document_number,
                    'title': document.title,
                    'current_status': document.status
                },
                'workflow': None,
                'transitions': [],
                'statistics': {
                    'total_transitions': 0,
                    'total_rejections': 0,
                    'total_approvals': 0,
                    'workflow_duration_days': 0,
                    'current_state_duration_hours': 0
                },
                'message': 'No workflow found for this document'
            })
        
        # Get all transitions for this workflow
        transitions = DocumentTransition.objects.filter(
            workflow=workflow
        ).order_by('transitioned_at').select_related(
            'transitioned_by', 'from_state', 'to_state'
        )
        
        # Build transitions data
        transitions_data = []
        rejection_count = 0
        approval_count = 0
        
        for transition in transitions:
            # Count rejections and approvals
            if 'reject' in transition.comment.lower():
                rejection_count += 1
            if transition.to_state.code in ['REVIEWED', 'APPROVED_AND_EFFECTIVE']:
                approval_count += 1
            
            transitions_data.append({
                'id': transition.id,
                'transitioned_at': transition.transitioned_at.isoformat(),
                'transitioned_by': {
                    'id': transition.transitioned_by.id,
                    'username': transition.transitioned_by.username,
                    'first_name': transition.transitioned_by.first_name or '',
                    'last_name': transition.transitioned_by.last_name or '',
                    'full_name': transition.transitioned_by.get_full_name()
                },
                'from_state': {
                    'code': transition.from_state.code,
                    'name': transition.from_state.name
                },
                'to_state': {
                    'code': transition.to_state.code,
                    'name': transition.to_state.name
                },
                'comment': transition.comment
            })
        
        # Calculate workflow statistics
        from django.utils import timezone
        workflow_start = transitions.first().transitioned_at if transitions.exists() else workflow.created_at
        workflow_duration = timezone.now() - workflow_start
        
        current_state_start = transitions.last().transitioned_at if transitions.exists() else workflow.created_at
        current_state_duration = timezone.now() - current_state_start
        
        # Build response
        response_data = {
            'document': {
                'uuid': str(document.uuid),
                'document_number': document.document_number,
                'title': document.title,
                'current_status': document.status,
                'status_display': getattr(document, 'get_status_display', lambda: document.status)(),
                'author': document.author.get_full_name(),
                'created_at': document.created_at.isoformat(),
                'updated_at': document.updated_at.isoformat() if document.updated_at else document.created_at.isoformat()
            },
            'workflow': {
                'id': workflow.id,
                'current_state': workflow.current_state.code if workflow.current_state else None,
                'current_state_name': workflow.current_state.name if workflow.current_state else None,
                'is_terminated': workflow.is_terminated,
                'created_at': workflow.created_at.isoformat(),
                'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else workflow.created_at.isoformat()
            },
            'transitions': transitions_data,
            'statistics': {
                'total_transitions': len(transitions_data),
                'total_rejections': rejection_count,
                'total_approvals': approval_count,
                'workflow_duration_days': workflow_duration.days,
                'current_state_duration_hours': round(current_state_duration.total_seconds() / 3600, 1)
            },
            'success': True
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )