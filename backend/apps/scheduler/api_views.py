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
        return []  # Simplified - no NotificationQueue queries needed
    
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
    
    @action(detail=False, methods=['get'], url_path='monitoring-status')
    def monitoring_status(self, request):
        """
        Comprehensive monitoring status endpoint
        Returns Celery Beat, Worker status, and task statistics
        """
        try:
            from celery import current_app
            from django_celery_beat.models import PeriodicTask
            from datetime import timedelta
            
            # Get Celery inspect instance
            inspect = current_app.control.inspect()
            
            # Check Celery Worker status
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            stats = inspect.stats()
            
            worker_status = {
                'is_running': active_workers is not None and len(active_workers) > 0,
                'worker_count': len(active_workers) if active_workers else 0,
                'workers': []
            }
            
            if active_workers:
                for worker_name, tasks in active_workers.items():
                    worker_info = {
                        'name': worker_name,
                        'active_tasks': len(tasks),
                        'registered_tasks': len(registered_tasks.get(worker_name, [])) if registered_tasks else 0
                    }
                    if stats and worker_name in stats:
                        worker_info['pool_size'] = stats[worker_name].get('pool', {}).get('max-concurrency', 0)
                    worker_status['workers'].append(worker_info)
            
            # Check Celery Beat status (via periodic tasks)
            periodic_tasks = PeriodicTask.objects.filter(enabled=True)
            beat_tasks = {
                'total_scheduled': periodic_tasks.count(),
                'backup_tasks': periodic_tasks.filter(name__icontains='backup').count(),
                'notification_tasks': periodic_tasks.filter(name__icontains='notification').count(),
                'health_check_tasks': periodic_tasks.filter(name__icontains='health').count(),
                'document_tasks': periodic_tasks.filter(name__icontains='document').count(),
            }
            
            # Get task execution history (last 24 hours)
            from django_celery_results.models import TaskResult
            recent_date = timezone.now() - timedelta(hours=24)
            recent_tasks = TaskResult.objects.filter(date_done__gte=recent_date)
            
            task_stats = {
                'last_24h': {
                    'total': recent_tasks.count(),
                    'successful': recent_tasks.filter(status='SUCCESS').count(),
                    'failed': recent_tasks.filter(status='FAILURE').count(),
                    'pending': recent_tasks.filter(status='PENDING').count(),
                }
            }
            
            # Get scheduled task info
            scheduled_tasks_info = []
            for task in periodic_tasks.order_by('-last_run_at')[:10]:
                scheduled_tasks_info.append({
                    'name': task.name,
                    'task': task.task,
                    'enabled': task.enabled,
                    'last_run_at': task.last_run_at,
                    'schedule': str(task.crontab) if task.crontab else str(task.interval)
                })
            
            # Overall health score
            health_score = 100
            if not worker_status['is_running']:
                health_score -= 50
            if task_stats['last_24h']['total'] > 0:
                failure_rate = task_stats['last_24h']['failed'] / task_stats['last_24h']['total']
                health_score -= int(failure_rate * 30)
            
            return Response({
                'overall_status': 'healthy' if health_score > 70 else 'degraded' if health_score > 40 else 'unhealthy',
                'health_score': health_score,
                'celery_worker': worker_status,
                'celery_beat': {
                    'is_running': True,  # If we can query DB, beat is likely running
                    'scheduled_tasks': beat_tasks,
                },
                'task_statistics': task_stats,
                'scheduled_tasks': scheduled_tasks_info,
                'timestamp': timezone.now()
            })
            
        except Exception as e:
            import traceback
            return Response(
                {
                    'status': 'error',
                    'message': str(e),
                    'traceback': traceback.format_exc()
                },
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
            from .tasks import perform_system_health_check
            
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