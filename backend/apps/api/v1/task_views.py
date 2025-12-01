"""
User Task API Views - Simplified endpoint for frontend notification system
Provides the expected /api/v1/workflows/tasks/user-tasks/ endpoint
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils import timezone

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tasks(request):
    """
    Get user's tasks (pending and completed) for task management.
    Endpoint: /api/v1/workflows/tasks/user-tasks/
    
    Query parameters:
    - status: 'pending' or 'completed' or 'all' (default: 'all')
    - limit: number of tasks to return (default: 20)
    """
    try:
        from apps.workflows.models import WorkflowTask
        
        user = request.user
        status_filter = request.GET.get('status', 'all').upper()
        limit = int(request.GET.get('limit', 20))
        
        print(f"🔍 API Debug: user={user.username}, status_filter='{status_filter}', limit={limit}")
        
        # Build query based on status filter
        query = WorkflowTask.objects.filter(assigned_to=user)
        
        if status_filter == 'PENDING':
            print("🔍 Filtering for PENDING tasks only")
            query = query.filter(status='PENDING')
        elif status_filter == 'COMPLETED':
            print("🔍 Filtering for COMPLETED tasks only")
            query = query.filter(status='COMPLETED')
        else:
            print("🔍 Returning ALL tasks (no status filter)")
        # 'ALL' or any other value returns both pending and completed
        
        user_tasks = query.select_related(
            'workflow_instance',
            'assigned_by'
        ).order_by('-created_at')[:limit]
        
        print(f"🔍 Query returned {user_tasks.count()} tasks")
        
        # Convert to the format expected by frontend
        tasks = []
        for task in user_tasks:
            try:
                # Get document info if available
                document = None
                if hasattr(task.workflow_instance, 'document'):
                    document = task.workflow_instance.document
                
                task_data = {
                    'id': str(task.uuid),
                    'name': task.name,
                    'description': task.description,
                    'task_type': task.task_type,
                    'priority': task.priority,
                    'status': task.status,
                    'created_at': task.created_at.isoformat(),
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'assigned_by': task.assigned_by.get_full_name() if task.assigned_by else 'System',
                    'workflow_type': str(getattr(task.workflow_instance, 'workflow_type', 'Unknown')),
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'completion_note': task.completion_note
                }
                
                # Add document info if available
                if document:
                    task_data.update({
                        'document_id': document.id,
                        'document_uuid': str(document.uuid),
                        'document_number': document.document_number,
                        'document_title': document.title,
                        'document_status': document.status,
                        'document_version': getattr(document, 'version_string', 'N/A')
                    })
                
                tasks.append(task_data)
                
            except Exception as task_error:
                # Skip problematic tasks but continue processing
                print(f"⚠️ Error processing task {task.uuid}: {task_error}")
                continue
        
        # Calculate task counts
        pending_count = len([t for t in tasks if t['status'] == 'PENDING'])
        completed_count = len([t for t in tasks if t['status'] == 'COMPLETED'])
        
        print(f"🔍 Final counts: pending={pending_count}, completed={completed_count}, total={len(tasks)}")
        
        return Response({
            'success': True,
            'tasks': tasks,
            'task_count': len(tasks),
            'pending_count': pending_count,
            'completed_count': completed_count,
            'status_filter': status_filter.lower(),
            'method': 'WorkflowTask query (enhanced)',
            'user': user.username,
            'debug_original_filter': request.GET.get('status', 'none_provided')
        })
        
    except Exception as e:
        print(f"❌ Error in user_tasks endpoint: {e}")
        # Fallback to empty response to keep frontend working
        return Response({
            'success': False,
            'tasks': [],
            'task_count': 0,
            'error': str(e),
            'method': 'error fallback'
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_id):
    """
    Mark a task as completed.
    Endpoint: /api/v1/workflows/tasks/user-tasks/<task_id>/complete/
    """
    try:
        from apps.workflows.models import WorkflowTask
        
        task = WorkflowTask.objects.get(uuid=task_id, assigned_to=request.user)
        completion_note = request.data.get('completion_note', 'Task completed via API')
        
        # Mark task as completed
        task.status = 'COMPLETED'
        task.completed_at = timezone.now()
        task.completion_note = completion_note
        task.save()
        
        return Response({
            'success': True,
            'message': 'Task completed successfully',
            'task_id': str(task.uuid)
        })
        
    except WorkflowTask.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Task not found or not assigned to you'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)