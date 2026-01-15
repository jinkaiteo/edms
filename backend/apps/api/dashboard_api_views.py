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
from apps.audit.models import LoginAudit, AuditTrail
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
        
        # Get recent audit trail activity for admin dashboard
        recent_audits = AuditTrail.objects.select_related('user').order_by('-timestamp')[:10]
        
        activity_list = []
        for audit in recent_audits:
            # Generate user-friendly title
            title = _generate_activity_title(audit)
            
            activity_list.append({
                'id': audit.id,
                'title': title,
                'user': audit.user.get_full_name() if audit.user else 'System',
                'timestamp': audit.timestamp.isoformat() if audit.timestamp else timezone.now().isoformat(),
                'icon': _get_activity_icon(audit.action),
                'iconColor': _get_activity_color(audit.action)
            })
        
        return Response({
            'user_stats': user_stats,
            'system_stats': system_stats,
            'document_breakdown': status_counts,
            'recent_activity': activity_list,
            'total_documents': total_documents,
            'active_users': total_users,
            'active_workflows': active_workflows,
            'placeholders': 0,  # TODO: Get actual placeholder count
            'audit_entries_24h': AuditTrail.objects.filter(timestamp__gte=timezone.now() - timedelta(hours=24)).count(),
            'timestamp': timezone.now().isoformat(),
            'cache_duration': 300,
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

def _generate_activity_title(audit):
    """Generate human-readable activity title."""
    action_titles = {
        'CREATE': f"Document Created: {audit.object_representation}",
        'UPDATE': f"Document Updated: {audit.object_representation}",
        'DELETE': f"Document Deleted: {audit.object_representation}",
        'SIGN': f"Document Signed: {audit.object_representation}",
        'LOGIN': f"User Login: {audit.user.username if audit.user else 'Unknown'}",
        'LOGIN_SUCCESS': f"User Login: {audit.user.username if audit.user else 'Unknown'}",
        'LOGIN_FAILED': f"Failed Login Attempt",
        'LOGOUT': f"User Logout: {audit.user.username if audit.user else 'Unknown'}",
        'WORKFLOW_COMPLETE': f"Workflow Completed: {audit.object_representation}",
        'WORKFLOW_TRANSITION': f"Workflow Updated: {audit.object_representation}",
        'SYSTEM_HEALTH_CHECK': "System Health Check Performed",
        'BACKUP_CREATED': "System Backup Created",
        'BACKUP_RESTORED': "System Restored from Backup",
        'USER_CREATED': f"User Created: {audit.object_representation}",
        'USER_UPDATED': f"User Updated: {audit.object_representation}",
        'USER_DELETED': f"User Deleted: {audit.object_representation}",
        'PASSWORD_CHANGED': f"Password Changed",
        'PERMISSION_CHANGED': f"Permissions Changed: {audit.object_representation}",
        'CONFIGURATION_UPDATED': "System Configuration Updated"
    }
    
    # Return title with description fallback if object_representation is Unknown
    title = action_titles.get(audit.action)
    if title:
        return title
    # Fallback: format action name nicely
    if audit.object_representation and audit.object_representation != 'Unknown':
        return f"{audit.action.replace('_', ' ').title()}: {audit.object_representation}"
    else:
        return audit.action.replace('_', ' ').title()


def _get_activity_icon(action):
    """Get icon for activity type."""
    icon_mapping = {
        'CREATE': '📄',
        'UPDATE': '✏️',
        'DELETE': '🗑️',
        'SIGN': '✍️',
        'LOGIN': '🔐',
        'LOGIN_SUCCESS': '🔐',
        'LOGIN_FAILED': '🚫',
        'LOGOUT': '👋',
        'WORKFLOW_COMPLETE': '✅',
        'WORKFLOW_TRANSITION': '🔄',
        'SYSTEM_HEALTH_CHECK': '❤️',
        'BACKUP_CREATED': '💾',
        'BACKUP_RESTORED': '♻️',
        'USER_CREATED': '👤',
        'USER_UPDATED': '👤',
        'USER_DELETED': '👤',
        'PASSWORD_CHANGED': '🔑',
        'PERMISSION_CHANGED': '🛡️',
        'CONFIGURATION_UPDATED': '⚙️'
    }
    return icon_mapping.get(action, '📊')


def _get_activity_color(action):
    """Get color for activity type."""
    color_mapping = {
        'CREATE': 'bg-green-500',
        'UPDATE': 'bg-blue-500',
        'DELETE': 'bg-red-500',
        'SIGN': 'bg-purple-500',
        'LOGIN': 'bg-indigo-500',
        'LOGIN_SUCCESS': 'bg-green-500',
        'LOGIN_FAILED': 'bg-red-500',
        'LOGOUT': 'bg-gray-500',
        'WORKFLOW_COMPLETE': 'bg-emerald-500',
        'WORKFLOW_TRANSITION': 'bg-orange-500',
        'SYSTEM_HEALTH_CHECK': 'bg-green-500',
        'BACKUP_CREATED': 'bg-blue-500',
        'BACKUP_RESTORED': 'bg-orange-500',
        'USER_CREATED': 'bg-green-500',
        'USER_UPDATED': 'bg-blue-500',
        'USER_DELETED': 'bg-red-500',
        'PASSWORD_CHANGED': 'bg-yellow-500',
        'PERMISSION_CHANGED': 'bg-purple-500',
        'CONFIGURATION_UPDATED': 'bg-indigo-500'
    }
    return color_mapping.get(action, 'bg-gray-500')
