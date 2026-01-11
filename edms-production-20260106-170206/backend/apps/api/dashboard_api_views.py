"""
Dashboard API Views
Provides live data endpoints for dashboard statistics and recent activity
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.documents.models import Document
from apps.workflows.models import DocumentWorkflow, DocumentTransition
from apps.audit.models import LoginAudit
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    """
    Get comprehensive dashboard statistics for the current user.
    
    GET /api/v1/dashboard/stats/
    
    Returns:
    {
        "user_stats": {
            "total_documents": 15,
            "pending_tasks": 3,
            "my_documents": 5,
            "action_required": 2
        },
        "system_stats": {
            "total_documents": 50,
            "active_workflows": 8,
            "total_users": 21,
            "system_status": "Operational"
        },
        "document_breakdown": {
            "draft": 2,
            "pending_review": 3,
            "reviewed": 1,
            "pending_approval": 2,
            "approved_and_effective": 15
        }
    }
    """
    try:
        user = request.user
        
        # User-specific statistics
        user_documents = Document.objects.filter(author=user)
        
        # Documents requiring user action (DRAFT or REVIEWED)
        action_required_docs = user_documents.filter(
            status__in=['DRAFT', 'REVIEWED']
        )
        
        # Documents where user is waiting on others
        pending_docs = user_documents.filter(
            status__in=['PENDING_REVIEW', 'UNDER_REVIEW', 'PENDING_APPROVAL']
        )
        
        # New relevant dashboard metrics
        active_workflows = Document.objects.filter(
            status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED']
        ).count()
        
        awaiting_approval = Document.objects.filter(
            status__in=['REVIEWED', 'PENDING_APPROVAL']
        ).count()
        
        # Recent activity (documents updated in last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_activity = Document.objects.filter(updated_at__gte=week_ago).count()
        
        effective_documents = Document.objects.filter(
            status='APPROVED_AND_EFFECTIVE'
        ).count()
        
        # User statistics (maintaining backward compatibility)
        user_stats = {
            'total_documents': user_documents.count(),
            'pending_tasks': pending_docs.count(),
            'my_documents': user_documents.count(),
            'action_required': action_required_docs.count(),
            # New metrics for dashboard cards
            'active_workflows': active_workflows,
            'awaiting_approval': awaiting_approval,
            'recent_activity': recent_activity,
            'effective_documents': effective_documents
        }
        
        # System-wide statistics (for admin dashboard)
        total_documents = Document.objects.count()
        active_workflows = DocumentWorkflow.objects.filter(is_terminated=False).count()
        total_users = User.objects.filter(is_active=True).count()
        
        # System health check (simplified)
        try:
            # Check if we can query the database successfully
            recent_activity = DocumentTransition.objects.filter(
                transitioned_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            system_status = "Operational"
        except Exception:
            system_status = "Issues Detected"
        
        system_stats = {
            'total_documents': total_documents,
            'active_workflows': active_workflows,
            'total_users': total_users,
            'system_status': system_status,
            'recent_activity_24h': recent_activity
        }
        
        # Document status breakdown (system-wide)
        document_breakdown = Document.objects.values('status').annotate(
            count=Count('status')
        ).order_by('status')
        
        # Convert to dictionary
        status_counts = {item['status'].lower().replace('_', ' '): item['count'] 
                        for item in document_breakdown}
        
        return Response({
            'user_stats': user_stats,
            'system_stats': system_stats,
            'document_breakdown': status_counts,
            'last_updated': timezone.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_activity(request):
    """
    Get recent workflow activity for dashboard display.
    
    GET /api/v1/dashboard/activity/?limit=10&days=7
    
    Returns:
    {
        "activities": [
            {
                "id": 1,
                "timestamp": "2025-01-01T10:00:00Z",
                "type": "document_transition",
                "description": "Document SOP-2025-0001 submitted for review",
                "user": "John Doe",
                "document": "SOP-2025-0001-v01.00",
                "from_state": "DRAFT",
                "to_state": "PENDING_REVIEW"
            }
        ]
    }
    """
    try:
        # Get query parameters
        limit = int(request.GET.get('limit', 10))
        days = int(request.GET.get('days', 7))
        user_only = request.GET.get('user_only', 'false').lower() == 'true'
        
        # Calculate date range
        since = timezone.now() - timedelta(days=days)
        
        # Get recent workflow transitions
        transitions_query = DocumentTransition.objects.filter(
            transitioned_at__gte=since
        ).select_related('transitioned_by', 'workflow__document', 'from_state', 'to_state')
        
        # Filter to user's documents only if requested
        if user_only:
            transitions_query = transitions_query.filter(
                Q(workflow__document__author=request.user) |
                Q(transitioned_by=request.user)
            )
        
        recent_transitions = transitions_query.order_by('-transitioned_at')[:limit]
        
        activities = []
        for transition in recent_transitions:
            # Create human-readable description
            doc = transition.workflow.document
            user_name = transition.transitioned_by.get_full_name()
            
            # Determine activity type and description
            from_state = transition.from_state.code
            to_state = transition.to_state.code
            
            if to_state == 'PENDING_REVIEW':
                description = f"Document {doc.document_number} submitted for review"
                activity_type = "submission"
            elif to_state == 'UNDER_REVIEW':
                description = f"Review started for document {doc.document_number}"
                activity_type = "review_start"
            elif to_state == 'REVIEWED':
                description = f"Review completed for document {doc.document_number}"
                activity_type = "review_complete"
            elif to_state == 'PENDING_APPROVAL':
                description = f"Document {doc.document_number} routed for approval"
                activity_type = "approval_routing"
            elif to_state == 'APPROVED_AND_EFFECTIVE':
                description = f"Document {doc.document_number} approved and made effective"
                activity_type = "approval"
            elif 'reject' in transition.comment.lower():
                description = f"Document {doc.document_number} rejected"
                activity_type = "rejection"
            else:
                description = f"Document {doc.document_number} transitioned from {from_state} to {to_state}"
                activity_type = "transition"
            
            activities.append({
                'id': transition.id,
                'timestamp': transition.transitioned_at.isoformat(),
                'type': activity_type,
                'description': description,
                'user': user_name,
                'user_username': transition.transitioned_by.username,
                'document': doc.document_number,
                'document_title': doc.title,
                'document_uuid': str(doc.uuid),
                'from_state': from_state,
                'to_state': to_state,
                'comment': transition.comment if transition.comment else None
            })
        
        return Response({
            'activities': activities,
            'total_found': len(activities),
            'date_range': {
                'since': since.isoformat(),
                'days': days
            },
            'user_only': user_only,
            'success': True
        })
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_overview(request):
    """
    Get combined dashboard overview data in a single call for efficiency.
    
    GET /api/v1/dashboard/overview/
    """
    try:
        # Get stats
        stats_response = get_dashboard_stats(request)
        stats_data = stats_response.data if stats_response.status_code == 200 else {}
        
        # Get recent activity (limited to 5 for overview)
        activity_request = request
        activity_request.GET = activity_request.GET.copy()
        activity_request.GET['limit'] = '5'
        activity_response = get_recent_activity(activity_request)
        activity_data = activity_response.data if activity_response.status_code == 200 else {'activities': []}
        
        return Response({
            'stats': stats_data,
            'recent_activity': activity_data['activities'],
            'overview_generated_at': timezone.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )