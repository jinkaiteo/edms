"""
API Views for Author Task Management

Provides REST API endpoints for document authors to view and manage their tasks.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .author_notifications import author_notification_service
from .models import WorkflowTask
from ..documents.models import Document

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_author_tasks(request):
    """
    Get all pending tasks for the authenticated user.
    
    Returns tasks where the user is the document author and needs to take action.
    """
    try:
        user = request.user
        
        # Get tasks from the notification service
        tasks = author_notification_service.get_author_pending_tasks(user)
        
        # Add additional context for each task
        for task in tasks:
            # Add action URLs for frontend
            if task.get('document_uuid'):
                task['action_url'] = f"/document-management?doc={task['document_uuid']}"
            
            # Add priority styling
            task['priority_class'] = {
                'URGENT': 'bg-red-100 border-red-500 text-red-800',
                'HIGH': 'bg-orange-100 border-orange-500 text-orange-800', 
                'NORMAL': 'bg-blue-100 border-blue-500 text-blue-800',
                'LOW': 'bg-gray-100 border-gray-500 text-gray-800'
            }.get(task.get('priority', 'NORMAL'), 'bg-gray-100 border-gray-500 text-gray-800')
        
        return Response({
            'tasks': tasks,
            'task_count': len(tasks),
            'overdue_count': len([t for t in tasks if t.get('is_overdue', False)])
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch tasks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_id):
    """
    Mark a task as completed.
    
    Expected payload:
    {
        "completion_note": "Optional note about task completion"
    }
    """
    try:
        user = request.user
        completion_note = request.data.get('completion_note', '')
        
        success = author_notification_service.mark_task_completed(
            task_id=task_id,
            user=user,
            completion_note=completion_note
        )
        
        if success:
            return Response({
                'message': 'Task completed successfully',
                'task_id': task_id
            })
        else:
            return Response(
                {'error': 'Task not found or you do not have permission to complete it'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        return Response(
            {'error': f'Failed to complete task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_summary(request):
    """
    Get a summary of tasks for the dashboard.
    """
    try:
        user = request.user
        tasks = author_notification_service.get_author_pending_tasks(user)
        
        # Calculate summary statistics
        total_tasks = len(tasks)
        overdue_tasks = len([t for t in tasks if t.get('is_overdue', False)])
        high_priority_tasks = len([t for t in tasks if t.get('priority') in ['HIGH', 'URGENT']])
        
        # Group by task type
        task_types = {}
        for task in tasks:
            task_type = task.get('task_type', 'UNKNOWN')
            if task_type not in task_types:
                task_types[task_type] = 0
            task_types[task_type] += 1
        
        # Get upcoming due dates (next 7 days)
        from django.utils import timezone
        upcoming_due = [
            t for t in tasks 
            if t.get('due_date') and 
            t['due_date'] <= timezone.now() + timezone.timedelta(days=7)
        ]
        
        return Response({
            'summary': {
                'total_tasks': total_tasks,
                'overdue_tasks': overdue_tasks,
                'high_priority_tasks': high_priority_tasks,
                'upcoming_due_count': len(upcoming_due),
                'task_types': task_types
            },
            'recent_tasks': tasks[:5],  # Most recent 5 tasks
            'needs_attention': overdue_tasks > 0 or high_priority_tasks > 0
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get task summary: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )