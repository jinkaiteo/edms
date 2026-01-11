"""
Simple Dashboard Statistics API View

Standalone view for dashboard statistics that avoids complex dependencies.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.throttling import UserRateThrottle
from django.utils import timezone
from datetime import timedelta
from django.db import connection


class DashboardStatsView(APIView):
    """Simple dashboard statistics API endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        """Get real-time dashboard statistics."""
        try:
            # Get statistics using direct database queries to avoid serializer dependencies
            with connection.cursor() as cursor:
                # Active users count
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
                active_users_count = cursor.fetchone()[0]
                
                # Active workflows count
                cursor.execute("SELECT COUNT(*) FROM workflow_instances WHERE is_active = true")
                active_workflows_count = cursor.fetchone()[0]
                
                # Placeholders count
                cursor.execute("SELECT COUNT(*) FROM placeholder_definitions")
                placeholders_count = cursor.fetchone()[0]
                
                # Audit entries in last 24 hours
                twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
                cursor.execute(
                    "SELECT COUNT(*) FROM audit_trail WHERE timestamp >= %s",
                    [twenty_four_hours_ago]
                )
                audit_entries_24h = cursor.fetchone()[0]
                
                # Total documents count
                cursor.execute("SELECT COUNT(*) FROM documents")
                total_documents_count = cursor.fetchone()[0]
                
                # Pending reviews count (documents in review state)
                cursor.execute(
                    "SELECT COUNT(*) FROM workflow_instances WHERE state ILIKE '%review%' AND is_active = true"
                )
                pending_reviews_count = cursor.fetchone()[0]
                
                # Recent activity (last 5 audit entries)
                cursor.execute("""
                    SELECT uuid, action, object_representation, description, timestamp, user_display_name 
                    FROM audit_trail 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                
                recent_activities = cursor.fetchall()
                
            activity_list = []
            for audit in recent_activities:
                activity_item = {
                    'id': str(audit[0]),
                    'type': self._map_audit_action_to_type(audit[1]),
                    'title': self._generate_activity_title(audit[1], audit[2]),
                    'description': audit[3],
                    'timestamp': audit[4].isoformat() if audit[4] else timezone.now().isoformat(),
                    'user': audit[5] if audit[5] else 'System',
                    'icon': self._get_activity_icon(audit[1]),
                    'iconColor': self._get_activity_color(audit[1])
                }
                activity_list.append(activity_item)
            
            return Response({
                'total_documents': total_documents_count,
                'pending_reviews': pending_reviews_count,
                'active_workflows': active_workflows_count,
                'active_users': active_users_count,
                'placeholders': placeholders_count,
                'audit_entries_24h': audit_entries_24h,
                'recent_activity': activity_list,
                'timestamp': timezone.now().isoformat(),
                'cache_duration': 300  # 5 minutes cache suggestion
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to fetch dashboard statistics',
                'detail': str(e),
                'fallback_data': {
                    'total_documents': 0,
                    'pending_reviews': 0,
                    'active_workflows': 0,
                    'active_users': 0,
                    'placeholders': 0,
                    'audit_entries_24h': 0,
                    'recent_activity': [],
                    'timestamp': timezone.now().isoformat(),
                    'cache_duration': 0
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _map_audit_action_to_type(self, action):
        """Map audit action to activity type."""
        if not action:
            return 'system_activity'
            
        action_mapping = {
            'CREATE': 'document_created',
            'UPDATE': 'document_updated', 
            'DELETE': 'document_deleted',
            'SIGN': 'document_signed',
            'LOGIN': 'user_login',
            'WORKFLOW_COMPLETE': 'workflow_completed',
            'WORKFLOW_TRANSITION': 'workflow_updated'
        }
        return action_mapping.get(action, 'system_activity')
    
    def _generate_activity_title(self, action, object_representation):
        """Generate human-readable activity title."""
        if not action:
            return 'System Activity'
            
        action_titles = {
            'CREATE': f"Document Created: {object_representation or 'Unknown'}",
            'UPDATE': f"Document Updated: {object_representation or 'Unknown'}",
            'DELETE': f"Document Deleted: {object_representation or 'Unknown'}",
            'SIGN': f"Document Signed: {object_representation or 'Unknown'}",
            'LOGIN': f"User Login: {object_representation or 'Unknown'}",
            'WORKFLOW_COMPLETE': f"Workflow Completed: {object_representation or 'Unknown'}",
            'WORKFLOW_TRANSITION': f"Workflow Updated: {object_representation or 'Unknown'}"
        }
        return action_titles.get(action, f"{action}: {object_representation or 'Unknown'}")
    
    def _get_activity_icon(self, action):
        """Get icon for activity type."""
        icon_mapping = {
            'CREATE': '📄',
            'UPDATE': '✏️',
            'DELETE': '🗑️',
            'SIGN': '✍️',
            'LOGIN': '🔐',
            'WORKFLOW_COMPLETE': '✅',
            'WORKFLOW_TRANSITION': '🔄'
        }
        return icon_mapping.get(action, '📊')
    
    def _get_activity_color(self, action):
        """Get color for activity type."""
        color_mapping = {
            'CREATE': 'bg-green-500',
            'UPDATE': 'bg-blue-500',
            'DELETE': 'bg-red-500',
            'SIGN': 'bg-purple-500',
            'LOGIN': 'bg-indigo-500',
            'WORKFLOW_COMPLETE': 'bg-emerald-500',
            'WORKFLOW_TRANSITION': 'bg-orange-500'
        }
        return color_mapping.get(action, 'bg-gray-500')