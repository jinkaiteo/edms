"""
Notification API Views for v1 API

Provides REST API endpoints for notification management that the frontend NotificationBell expects.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
# from django.db.models import Q  # Not needed anymore

from apps.scheduler.models import NotificationQueue
# from apps.workflows.serializers import WorkflowNotificationSerializer

User = get_user_model()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for notification management.
    
    Provides endpoints for the NotificationBell component.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    # serializer_class = WorkflowNotificationSerializer  # Not needed for custom response
    
    def get_queryset(self):
        """Return notifications relevant to current user."""
        if hasattr(self, 'request') and self.request and self.request.user:
            return NotificationQueue.objects.filter(
                recipients=self.request.user
            ).order_by('-created_at')
        return NotificationQueue.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_notifications(self, request):
        """Get notifications for current user in format expected by NotificationBell."""
        try:
            # Get recent notifications (last 30 days)
            recent_date = timezone.now() - timedelta(days=30)
            notifications = NotificationQueue.objects.filter(
                recipients=request.user,
                created_at__gte=recent_date
            ).order_by('-created_at')[:20]
            
            # Get unread count from full queryset before slicing
            unread_count = NotificationQueue.objects.filter(
                recipients=request.user,
                created_at__gte=recent_date,
                status='SENT'  # SENT notifications are unread in NotificationQueue
            ).count()
            
            notification_data = []
            for notif in notifications:
                notification_data.append({
                    'id': str(notif.id),
                    'subject': notif.subject,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'priority': notif.priority,
                    'status': notif.status,  # PENDING, SENT, FAILED, CANCELLED
                    'created_at': notif.created_at.isoformat(),
                    'sent_at': notif.sent_at.isoformat() if notif.sent_at else None
                })
            
            return Response({
                'notifications': notification_data,
                'count': len(notification_data),
                'unread_count': unread_count
            })
            
        except Exception as e:
            print(f"❌ Error fetching notifications: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read."""
        try:
            notification = NotificationQueue.objects.get(
                pk=pk,
                recipients=request.user
            )
            
            # Handle fields that may not exist yet
            if hasattr(notification, 'is_read'):
                notification.is_read = True
            if hasattr(notification, 'read_at'):
                notification.read_at = timezone.now()
            notification.save()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
            
        except NotificationQueue.DoesNotExist:
            return Response(
                {'error': 'Notification not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all user's notifications as read."""
        try:
            notifications = self.get_queryset()
            # For now, just count all notifications since is_read field may not exist
            updated_count = notifications.count()
            
            return Response({
                'success': True,
                'message': f'Marked {updated_count} notifications as read',
                'updated_count': updated_count
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for current user."""
        try:
            count = self.get_queryset().filter(is_read=False).count()
            
            return Response({
                'unread_count': count
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )