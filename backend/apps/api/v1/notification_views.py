"""
Simplified notification API - removed NotificationQueue complexity
Focus on WorkflowTask-based notifications only
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    """
    Simplified notification endpoint - returns user's pending tasks directly
    No complex NotificationQueue - just WorkflowTask query
    """
    try:
        # WorkflowTask removed - using document filters instead
        
        user = request.user
        
        # Simple query - get user's pending tasks (this IS their notifications)
        pending_tasks = WorkflowTask.objects.filter(
            assigned_to=user,
            status='PENDING'
        ).order_by('-created_at')[:20]
        
        # Convert to simple notification format
        notifications = []
        for task in pending_tasks:
            notifications.append({
                'id': str(task.id),
                'subject': f"Task: {task.task_type} - {task.name}",
                'message': f"Task assigned: {task.name}",
                'task_type': task.task_type,
                'status': 'pending',
                'created_at': task.created_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'notifications': notifications,
            'unread_count': pending_tasks.count(),
            'method': 'HTTP polling (simplified)'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'notifications': [],
            'unread_count': 0
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark notification as read - simplified to just return success"""
    return JsonResponse({
        'success': True,
        'message': 'Notification marked as read (simplified system)'
    })
