"""
Task API Views for Workflow Tasks
Provides endpoints that match frontend expectations for task data.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def author_tasks(request):
    """Get tasks assigned to the current user (matching frontend expectations)."""
    try:
        from apps.scheduler.models import ScheduledTask
        user = request.user
        
        # Get workflow tasks assigned to this user
        tasks = ScheduledTask.objects.filter(
            task_type='workflow_task',
            metadata__assignee=user.username,
            status='PENDING'
        ).order_by('-created_at')
        
        # Convert to frontend expected format
        task_list = []
        for task in tasks:
            metadata = task.metadata
            
            # Parse due date
            due_date = None
            is_overdue = False
            try:
                due_date_str = metadata.get('due_date')
                if due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    is_overdue = due_date < timezone.now()
            except:
                pass
            
            # Determine priority class for styling
            priority = metadata.get('priority', 'normal').upper()
            priority_class = {
                'LOW': 'bg-gray-100 text-gray-800',
                'NORMAL': 'bg-blue-100 text-blue-800', 
                'HIGH': 'bg-orange-100 text-orange-800',
                'URGENT': 'bg-red-100 text-red-800'
            }.get(priority, 'bg-blue-100 text-blue-800')
            
            task_data = {
                'id': str(task.uuid),
                'name': task.name,
                'description': task.description,
                'task_type': metadata.get('task_type', 'REVIEW'),
                'priority': priority,
                'status': 'PENDING',
                'created_at': task.created_at.isoformat(),
                'due_date': due_date.isoformat() if due_date else None,
                'is_overdue': is_overdue,
                'assigned_by': metadata.get('assigned_by', 'System'),
                'workflow_type': 'REVIEW',
                'document_id': metadata.get('document_id'),
                'document_uuid': metadata.get('document_uuid'),
                'document_number': metadata.get('document_number'),
                'document_title': metadata.get('document_title'),
                'document_status': metadata.get('state_code', 'PENDING_REVIEW'),
                'document_version': 'v1.0',  # Default version
                'action_url': f"/document-management?doc={metadata.get('document_uuid')}" if metadata.get('document_uuid') else None,
                'priority_class': priority_class
            }
            
            task_list.append(task_data)
        
        return Response({'tasks': task_list})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e), 'tasks': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_summary(request):
    """Get task summary for the current user."""
    try:
        from apps.scheduler.models import ScheduledTask
        user = request.user
        
        # Get all workflow tasks for this user
        tasks = ScheduledTask.objects.filter(
            task_type='workflow_task',
            metadata__assignee=user.username,
            status='PENDING'
        )
        
        total_tasks = tasks.count()
        overdue_tasks = 0
        high_priority_tasks = 0
        upcoming_due_count = 0
        task_types = {}
        
        # Analyze tasks
        for task in tasks:
            metadata = task.metadata
            
            # Check if overdue
            try:
                due_date_str = metadata.get('due_date')
                if due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    if due_date < timezone.now():
                        overdue_tasks += 1
                    elif due_date < timezone.now() + timedelta(days=7):
                        upcoming_due_count += 1
            except:
                pass
            
            # Check priority
            priority = metadata.get('priority', 'normal')
            if priority in ['high', 'urgent']:
                high_priority_tasks += 1
            
            # Count task types
            task_type = metadata.get('task_type', 'REVIEW')
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        summary = {
            'total_tasks': total_tasks,
            'overdue_tasks': overdue_tasks,
            'high_priority_tasks': high_priority_tasks,
            'upcoming_due_count': upcoming_due_count,
            'task_types': task_types
        }
        
        return Response({'summary': summary})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_uuid):
    """Complete a task."""
    try:
        from apps.scheduler.models import ScheduledTask
        user = request.user
        
        # Get the task
        task = ScheduledTask.objects.get(
            uuid=task_uuid,
            metadata__assignee=user.username,
            task_type='workflow_task',
            status='PENDING'
        )
        
        completion_note = request.data.get('completion_note', 'Task completed via My Tasks page')
        
        # Update task status
        task.status = 'COMPLETED'
        task.metadata['completed_at'] = timezone.now().isoformat()
        task.metadata['completion_note'] = completion_note
        task.save()
        
        return Response({'success': True, 'message': 'Task completed successfully'})
        
    except ScheduledTask.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)