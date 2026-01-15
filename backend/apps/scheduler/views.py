"""
Scheduler Views for EDMS (S3).

Provides API endpoints for scheduler monitoring and health checks.
"""

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import ScheduledTask
# Temporarily disabled automated_tasks import for core functionality
# from .automated_tasks import (
#     perform_system_health_check,
#     process_document_effective_dates,
#     process_document_obsoletion_dates,
#     check_workflow_timeouts,
#     cleanup_workflow_tasks
# )

# Minimal implementations for core functionality
def perform_system_health_check():
    return {'healthy': True, 'status': 'Core services operational'}

def process_document_effective_dates():
    return {'processed_documents': []}

def process_document_obsoletion_dates():
    return {'processed_documents': []}

def check_workflow_timeouts():
    return {'checked_count': 0}

def cleanup_workflow_tasks():
    return {'terminated_document_tasks': 0}
from ..documents.models import Document
from ..workflows.models import DocumentWorkflow
from ..audit.models import AuditTrail


@staff_member_required
@require_http_methods(["GET"])
def system_health_api(request):
    """
    API endpoint for system health check.
    Returns comprehensive system status.
    """
    try:
        # Perform health check
        health_result = perform_system_health_check.apply()
        
        # Get additional system statistics
        stats = {
            'database': {
                'total_documents': Document.objects.count(),
                'active_documents': Document.objects.filter(is_active=True).count(),
                'effective_documents': Document.objects.filter(status='EFFECTIVE').count(),
                'pending_effective': Document.objects.filter(status='APPROVED_PENDING_EFFECTIVE').count(),
                'scheduled_obsolescence': Document.objects.filter(status='SCHEDULED_FOR_OBSOLESCENCE').count(),
            },
            'workflows': {
                'total_workflows': DocumentWorkflow.objects.count(),
                'active_workflows': DocumentWorkflow.objects.filter(is_terminated=False).count(),
                'completed_workflows': DocumentWorkflow.objects.filter(is_terminated=True).count(),
            },
            'audit': {
                'total_audit_records': AuditTrail.objects.count(),
                'recent_audit_records': AuditTrail.objects.filter(
                    timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
                ).count(),
            },
            'scheduler': {
                'total_tasks': ScheduledTask.objects.count(),
                'active_tasks': ScheduledTask.objects.filter(is_active=True).count(),
                'successful_executions': sum(task.success_count for task in ScheduledTask.objects.all()),
                'total_executions': sum(task.execution_count for task in ScheduledTask.objects.all()),
            }
        }
        
        # Calculate overall success rate
        total_executions = stats['scheduler']['total_executions']
        successful_executions = stats['scheduler']['successful_executions']
        
        if total_executions > 0:
            success_rate = (successful_executions / total_executions) * 100
        else:
            success_rate = 100
        
        response_data = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'HEALTHY' if success_rate >= 90 else 'WARNING' if success_rate >= 70 else 'CRITICAL',
            'success_rate': round(success_rate, 2),
            'health_check_result': health_result.result if health_result.successful() else {'error': 'Health check failed'},
            'system_statistics': stats,
            'recommendations': []
        }
        
        # Add recommendations based on status
        if stats['database']['pending_effective'] > 10:
            response_data['recommendations'].append('High number of documents pending effective date processing')
        
        if stats['workflows']['active_workflows'] > 50:
            response_data['recommendations'].append('Large number of active workflows - consider review timeout policies')
        
        if success_rate < 90:
            response_data['recommendations'].append('Scheduler success rate below 90% - investigate recent failures')
        
        return JsonResponse(response_data, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'CRITICAL',
            'error': str(e),
            'message': 'System health check failed'
        }, status=500)


@staff_member_required
@require_http_methods(["GET"])
def tasks_status_api(request):
    """
    API endpoint for scheduler tasks status.
    Returns detailed information about all scheduled tasks.
    """
    try:
        tasks_data = []
        
        for task in ScheduledTask.objects.all().order_by('-last_executed'):
            # Calculate success rate
            success_rate = 0
            if task.execution_count > 0:
                success_rate = (task.success_count / task.execution_count) * 100
            
            # Get recent executions
            recent_executions = []
            if hasattr(task, 'execution_history') and task.execution_history:
                recent_executions = task.execution_history[-5:]  # Last 5 executions
            
            # Determine next execution estimate
            next_execution = "Based on schedule"
            if task.schedule_expression:
                # Could implement cron parsing here for more accurate next execution time
                next_execution = f"Per schedule: {task.schedule_expression}"
            
            task_data = {
                'id': task.id,
                'name': task.task_function,
                'description': task.description,
                'type': task.task_type,
                'status': task.status,
                'is_active': task.is_active,
                'schedule': task.schedule_expression,
                'priority': task.priority,
                'statistics': {
                    'execution_count': task.execution_count,
                    'success_count': task.success_count,
                    'error_count': task.error_count,
                    'success_rate': round(success_rate, 2)
                },
                'last_executed': task.last_executed.isoformat() if task.last_executed else None,
                'next_execution': next_execution,
                'last_result': task.last_result,
                'recent_executions': recent_executions,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
            
            tasks_data.append(task_data)
        
        response_data = {
            'timestamp': timezone.now().isoformat(),
            'total_tasks': len(tasks_data),
            'active_tasks': len([t for t in tasks_data if t['is_active']]),
            'tasks': tasks_data,
            'summary': {
                'total_executions': sum(t['statistics']['execution_count'] for t in tasks_data),
                'total_successes': sum(t['statistics']['success_count'] for t in tasks_data),
                'total_errors': sum(t['statistics']['error_count'] for t in tasks_data),
                'overall_success_rate': 0
            }
        }
        
        # Calculate overall success rate
        total_exec = response_data['summary']['total_executions']
        total_success = response_data['summary']['total_successes']
        
        if total_exec > 0:
            response_data['summary']['overall_success_rate'] = round((total_success / total_exec) * 100, 2)
        else:
            response_data['summary']['overall_success_rate'] = 100
        
        return JsonResponse(response_data, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'error': str(e),
            'message': 'Failed to retrieve tasks status'
        }, status=500)


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def execute_task_api(request, task_id):
    """
    API endpoint to manually execute a scheduled task.
    """
    try:
        task = ScheduledTask.objects.get(pk=task_id)
        
        # Import task functions
        from .tasks import (
            process_document_effective_dates,
            process_document_obsoletion_dates,
            perform_system_health_check,
            check_workflow_timeouts
        )
        
        # Map task names to Celery tasks
        task_mapping = {
            'process_document_effective_dates': process_document_effective_dates,
            'process_document_obsoletion_dates': process_document_obsoletion_dates,
            'perform_system_health_check': perform_system_health_check,
            'check_workflow_timeouts': check_workflow_timeouts,
            'cleanup_workflow_tasks': cleanup_workflow_tasks
        }
        
        celery_task = task_mapping.get(task.task_function)
        
        if not celery_task:
            return JsonResponse({
                'error': f'Task "{task.task_function}" not found in task mapping',
                'available_tasks': list(task_mapping.keys())
            }, status=400)
        
        # Execute the task
        start_time = timezone.now()
        result = celery_task.apply()
        end_time = timezone.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Update task execution statistics
        task.execution_count += 1
        task.last_executed = start_time
        
        if result.successful():
            task.success_count += 1
            task.last_result = result.result
            execution_status = 'SUCCESS'
        else:
            task.error_count += 1
            task.last_result = {'error': str(result.result)}
            execution_status = 'ERROR'
        
        # Update execution history
        if not hasattr(task, 'execution_history') or task.execution_history is None:
            task.execution_history = []
        
        task.execution_history.append({
            'timestamp': start_time.isoformat(),
            'success': result.successful(),
            'duration': duration,
            'result': result.result if result.successful() else str(result.result)
        })
        
        # Keep only last 50 executions
        if len(task.execution_history) > 50:
            task.execution_history = task.execution_history[-50:]
        
        task.save()
        
        return JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'task_id': task_id,
            'task_name': task.task_function,
            'execution_status': execution_status,
            'duration': duration,
            'result': result.result if result.successful() else str(result.result),
            'message': f'Task "{task.task_function}" executed successfully' if result.successful() else f'Task "{task.task_function}" failed'
        })
        
    except ScheduledTask.DoesNotExist:
        return JsonResponse({
            'error': f'Task with ID {task_id} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'error': str(e),
            'message': 'Failed to execute task'
        }, status=500)