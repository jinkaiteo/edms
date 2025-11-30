"""
User Task API Views - Alternative endpoint to bypass routing conflicts
Provides clean endpoints for frontend task integration without conflicts.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tasks(request):
    """Get tasks assigned to the current user - ALTERNATIVE ENDPOINT."""
    try:
        from apps.scheduler.models import ScheduledTask
        user = request.user
        
        print(f"🎯 USER_TASKS API - User: {user.username} (ID: {user.id})")
        
        # FIXED: Get tasks from WorkflowTask model (where the actual tasks are stored)
        from apps.workflows.models import WorkflowTask
        tasks = WorkflowTask.objects.filter(
            assigned_to=user,
            status='PENDING'
        ).order_by('-created_at')
        
        print(f"📊 USER_TASKS API - Found {tasks.count()} tasks")
        
        # Convert WorkflowTasks to frontend expected format
        task_list = []
        for task in tasks:
            # Extract document info from task_data JSON field
            task_data_json = task.task_data or {}
            document_uuid = task_data_json.get('document_uuid', '')
            document_number = task_data_json.get('document_number', 'Unknown')
            
            # Parse due date
            due_date = None
            is_overdue = False
            if task.due_date:
                due_date = task.due_date
                is_overdue = due_date < timezone.now()
            
            # Determine priority class for styling
            priority = (task.priority or 'NORMAL').upper()
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
                'task_type': 'APPROVE' if task.task_type == 'APPROVE' else 'REVIEW',
                'priority': priority,
                'status': 'PENDING',
                'created_at': task.created_at.isoformat(),
                'due_date': due_date.isoformat() if due_date else None,
                'is_overdue': is_overdue,
                'assigned_by': task.assigned_by.get_full_name() if task.assigned_by else 'System',
                'workflow_type': 'REVIEW',
                'document_id': task_data_json.get('document_workflow_id'),
                'document_uuid': document_uuid,
                'document_number': document_number,
                'document_title': task.name,
                'document_status': 'PENDING_APPROVAL' if task.task_type == 'APPROVE' else 'PENDING_REVIEW',
                'document_version': 'v1.0',
                'action_url': f"/document-management?doc={document_uuid}" if document_uuid else None,
                'priority_class': priority_class
            }
            
            task_list.append(task_data)
        
        print(f"✅ USER_TASKS API - Returning {len(task_list)} tasks")
        return Response({'tasks': task_list, 'success': True})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ USER_TASKS API - Error: {e}")
        return Response({'error': str(e), 'tasks': [], 'success': False}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_task_summary(request):
    """Get task summary for the current user - ALTERNATIVE ENDPOINT."""
    try:
        from apps.scheduler.models import ScheduledTask
        user = request.user
        
        print(f"📊 USER_TASK_SUMMARY API - User: {user.username}")
        
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
        
        print(f"✅ USER_TASK_SUMMARY API - Total: {total_tasks}")
        return Response({'summary': summary, 'success': True})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ USER_TASK_SUMMARY API - Error: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_user_task(request, task_uuid):
    """Complete a user task - ALTERNATIVE ENDPOINT."""
    try:
        from apps.scheduler.models import ScheduledTask
        user = request.user
        
        print(f"🎯 COMPLETE_USER_TASK API - User: {user.username}, Task: {task_uuid}")
        
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
        
        print(f"✅ COMPLETE_USER_TASK API - Task completed successfully")
        return Response({'success': True, 'message': 'Task completed successfully'})
        
    except ScheduledTask.DoesNotExist:
        print(f"❌ COMPLETE_USER_TASK API - Task not found")
        return Response({'error': 'Task not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ COMPLETE_USER_TASK API - Error: {e}")
        return Response({'error': str(e)}, status=500)