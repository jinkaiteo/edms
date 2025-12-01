"""
API Views for Scheduler Module

Provides REST API endpoints for news feed, notifications, and system status.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import ScheduledTask
from .notification_service import notification_service
from ..documents.models import Document
from ..workflows.models import DocumentWorkflow

User = get_user_model()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for notification management.
    
    Provides endpoints for the news feed component.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications relevant to current user."""
        return []  # Simplified - no NotificationQueue
            Q(created_by=self.request.user)
        ).distinct()
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent notifications for current user."""
        try:
            # Get recent notifications (last 7 days)
            recent_date = timezone.now() - timedelta(days=7)
            notifications = self.get_queryset().filter(
                created_at__gte=recent_date
            ).order_by('-created_at')[:10]
            
            notification_data = []
            for notif in notifications:
                notification_data.append({
                    'id': notif.id,
                    'subject': notif.subject,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'priority': notif.priority,
                    'status': notif.status,
                    'created_at': notif.created_at,
                    'scheduled_at': notif.scheduled_at,
                    'sent_at': notif.sent_at
                })
            
            return Response(notification_data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks and workflows assigned to current user."""
        try:
            user = request.user
            
            # Get documents pending user action
            pending_reviews = Document.objects.filter(
                status='PENDING_REVIEW',
                reviewer=user
            ).values('id', 'document_number', 'title', 'status', 'created_at')
            
            pending_approvals = Document.objects.filter(
                status='PENDING_APPROVAL', 
                approver=user
            ).values('id', 'document_number', 'title', 'status', 'created_at')
            
            # Get user's draft documents
            my_drafts = Document.objects.filter(
                status='DRAFT',
                author=user
            ).values('id', 'document_number', 'title', 'status', 'created_at')
            
            # Get workflows assigned to user
            my_workflows = DocumentWorkflow.objects.filter(
                current_assignee=user,
                is_terminated=False
            ).select_related('document').values(
                'id', 'document__document_number', 'document__title', 
                'current_state__name', 'due_date', 'created_at'
            )
            
            return Response({
                'pending_reviews': list(pending_reviews),
                'pending_approvals': list(pending_approvals),
                'my_drafts': list(my_drafts),
                'my_workflows': list(my_workflows),
                'summary': {
                    'total_pending': len(pending_reviews) + len(pending_approvals),
                    'drafts_count': len(my_drafts),
                    'workflows_count': len(my_workflows)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """Send a test notification to current user."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            success = notification_service.send_immediate_notification(
                recipients=[request.user],
                subject='EDMS Test Notification',
                message=f'Hello {request.user.get_full_name()}, this is a test notification sent at {timezone.now()}. If you receive this, the notification system is working correctly.',
                notification_type='SYSTEM_TEST'
            )
            
            return Response({
                'success': success,
                'message': 'Test notification sent successfully' if success else 'Failed to send notification'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemStatusViewSet(viewsets.ViewSet):
    """
    API endpoints for system status information.
    
    Provides system health and status data for the news feed.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Get system health status."""
        try:
            from .automated_tasks import perform_system_health_check
            
            # Get recent health check result
            result = perform_system_health_check.apply()
            
            return Response(result.result if result.successful() else {
                'overall_status': 'ERROR',
                'error': 'Health check failed'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get system statistics for dashboard."""
        try:
            # Document statistics
            total_docs = Document.objects.count()
            active_docs = Document.objects.filter(is_active=True).count()
            effective_docs = Document.objects.filter(status='EFFECTIVE').count()
            
            # Recent activity (last 7 days)
            recent_date = timezone.now() - timedelta(days=7)
            recent_effective = Document.objects.filter(
                status='EFFECTIVE',
                effective_date__gte=recent_date
            ).count()
            
            recent_obsolete = Document.objects.filter(
                status='OBSOLETE',
                obsolescence_date__gte=recent_date
            ).count()
            
            # Workflow statistics
            active_workflows = DocumentWorkflow.objects.filter(
                is_terminated=False
            ).count()
            
            overdue_workflows = DocumentWorkflow.objects.filter(
                is_terminated=False,
                due_date__lt=timezone.now().date()
            ).count()
            
            # Scheduler statistics
            active_tasks = ScheduledTask.objects.filter(
                status='ACTIVE'
            ).count()
            
            return Response({
                'documents': {
                    'total': total_docs,
                    'active': active_docs,
                    'effective': effective_docs,
                    'recent_effective': recent_effective,
                    'recent_obsolete': recent_obsolete
                },
                'workflows': {
                    'active': active_workflows,
                    'overdue': overdue_workflows
                },
                'scheduler': {
                    'active_tasks': active_tasks
                },
                'timestamp': timezone.now()
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )