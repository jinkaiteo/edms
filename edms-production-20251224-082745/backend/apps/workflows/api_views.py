"""
Workflow API Views
Provides missing endpoints for workflow types and other workflow operations.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import DocumentState


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workflow_types(request):
    """Get available workflow types."""
    try:
        # Return available workflow types based on system configuration
        workflow_types = [
            {
                'id': 'REVIEW_WORKFLOW',
                'name': 'Review Workflow',
                'description': 'Standard document review and approval process',
                'states': ['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'PENDING_APPROVAL', 'APPROVED', 'EFFECTIVE']
            },
            {
                'id': 'VERSION_WORKFLOW', 
                'name': 'Version Workflow',
                'description': 'Document versioning and update process',
                'states': ['DRAFT', 'PENDING_REVIEW', 'APPROVED', 'EFFECTIVE']
            },
            {
                'id': 'OBSOLESCENCE_WORKFLOW',
                'name': 'Obsolescence Workflow', 
                'description': 'Document retirement and obsolescence process',
                'states': ['EFFECTIVE', 'PENDING_OBSOLESCENCE', 'OBSOLETE']
            }
        ]
        
        return Response(workflow_types)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)