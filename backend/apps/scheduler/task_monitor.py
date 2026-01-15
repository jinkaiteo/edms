"""
Task Monitor - Simple and Intuitive Scheduler Dashboard
Shows task execution history, next run times, and status
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from celery import current_app
from celery.schedules import crontab, schedule as celery_schedule
# TaskResult not available - will use alternative tracking
try:
    from django_celery_results.models import TaskResult
    CELERY_RESULTS_AVAILABLE = True
except ImportError:
    CELERY_RESULTS_AVAILABLE = False
    TaskResult = None

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Monitor scheduled tasks with execution history and next run times"""
    
    # Define critical tasks and their categories
    TASK_DEFINITIONS = {
        'apps.scheduler.automated_tasks.process_document_effective_dates': {
            'name': 'Process Effective Dates',
            'category': 'Document Processing',
            'description': 'Auto-activates documents that reached their effective date'
        },
        'apps.scheduler.automated_tasks.process_document_obsoletion_dates': {
            'name': 'Process Obsolescence Dates',
            'category': 'Document Processing',
            'description': 'Auto-obsoletes documents that reached their obsolescence date'
        },
        'apps.scheduler.automated_tasks.check_workflow_timeouts': {
            'name': 'Check Workflow Timeouts',
            'category': 'Workflow Management',
            'description': 'Monitors workflows for timeouts and sends escalations'
        },
        'apps.scheduler.automated_tasks.perform_system_health_check': {
            'name': 'System Health Check',
            'category': 'System Maintenance',
            'description': 'Performs comprehensive system health validation'
        },
        'apps.scheduler.automated_tasks.cleanup_workflow_tasks': {
            'name': 'Cleanup Workflow Tasks',
            'category': 'System Maintenance',
            'description': 'Cleans up orphaned and obsolete workflow tasks'
        },
        'apps.scheduler.notification_service.process_notification_queue': {
            'name': 'Process Notifications',
            'category': 'Notifications',
            'description': 'Processes queued email and alert notifications'
        },
        'apps.scheduler.notification_service.send_daily_summary_notifications': {
            'name': 'Daily Summary Emails',
            'category': 'Notifications',
            'description': 'Sends daily summary notifications to users'
        },
        'apps.core.tasks.run_hybrid_backup': {
            'name': 'Database Backup',
            'category': 'Backups',
            'description': 'Performs database and file system backups'
        },
        'apps.scheduler.celery_cleanup.cleanup_celery_results': {
            'name': 'Cleanup Celery Results',
            'category': 'System Maintenance',
            'description': 'Cleans up old task execution records and REVOKED tasks'
        },
    }
    
    def get_task_status(self):
        """Get comprehensive status of all scheduled tasks"""
        try:
            # Get scheduled tasks from Celery Beat
            beat_schedule = current_app.conf.beat_schedule or {}
            
            # Get registered tasks from workers
            inspect = current_app.control.inspect()
            registered_tasks_by_worker = inspect.registered() or {}
            all_registered_tasks = set()
            for worker_tasks in registered_tasks_by_worker.values():
                all_registered_tasks.update(worker_tasks)
            
            # Build task list
            tasks = []
            for schedule_name, schedule_config in beat_schedule.items():
                task_path = schedule_config.get('task')
                task_info = self._get_task_info(
                    schedule_name, 
                    task_path, 
                    schedule_config,
                    all_registered_tasks
                )
                tasks.append(task_info)
            
            # Group by category
            tasks_by_category = {}
            for task in tasks:
                category = task['category']
                if category not in tasks_by_category:
                    tasks_by_category[category] = []
                tasks_by_category[category].append(task)
            
            # Calculate overall statistics
            total_tasks = len(tasks)
            healthy_tasks = len([t for t in tasks if t['status'] == 'SUCCESS'])
            failed_tasks = len([t for t in tasks if t['status'] == 'FAILURE'])
            warning_tasks = len([t for t in tasks if t['status'] == 'WARNING'])
            
            return {
                'timestamp': timezone.now().isoformat(),
                'summary': {
                    'total_tasks': total_tasks,
                    'healthy': healthy_tasks,
                    'failed': failed_tasks,
                    'warnings': warning_tasks,
                    'overall_status': self._determine_overall_status(healthy_tasks, failed_tasks, warning_tasks, total_tasks)
                },
                'tasks': tasks,
                'tasks_by_category': tasks_by_category
            }
            
        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            return {
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'summary': {
                    'total_tasks': 0,
                    'healthy': 0,
                    'failed': 0,
                    'warnings': 0,
                    'overall_status': 'ERROR'
                },
                'tasks': [],
                'tasks_by_category': {}
            }
    
    def _get_task_info(self, schedule_name, task_path, schedule_config, registered_tasks):
        """Get detailed information about a single task"""
        task_def = self.TASK_DEFINITIONS.get(task_path, {
            'name': schedule_name,
            'category': 'Other',
            'description': 'Scheduled task'
        })
        
        # Get execution history
        last_run = self._get_last_run(task_path)
        
        # Calculate next run
        next_run = self._calculate_next_run(schedule_config.get('schedule'))
        
        # Check if registered
        is_registered = task_path in registered_tasks
        
        # Determine status
        status, status_message = self._determine_task_status(last_run, is_registered)
        
        return {
            'schedule_name': schedule_name,
            'task_path': task_path,
            'name': task_def['name'],
            'category': task_def['category'],
            'description': task_def['description'],
            'schedule': self._format_schedule(schedule_config.get('schedule')),
            'is_registered': is_registered,
            'last_run': last_run,
            'next_run': next_run,
            'status': status,
            'status_message': status_message,
            'statistics': self._get_task_statistics(task_path)
        }
    
    def _get_last_run(self, task_name):
        """Get information about the last task execution"""
        if not CELERY_RESULTS_AVAILABLE or not TaskResult:
            # Use Celery inspect as fallback
            return self._get_last_run_from_inspect(task_name)
        
        try:
            # Filter out REVOKED tasks - they're not meaningful executions
            # Get the most recent ACTUAL execution (SUCCESS, FAILURE, RETRY)
            last_result = TaskResult.objects.filter(
                task_name=task_name
            ).exclude(
                status='REVOKED'
            ).order_by('-date_done').first()
            
            if not last_result:
                return {
                    'timestamp': None,
                    'relative_time': 'Never run',
                    'status': 'PENDING',
                    'duration': None,
                    'result': None
                }
            
            duration = None
            if last_result.date_done and hasattr(last_result, 'date_created'):
                duration = (last_result.date_done - last_result.date_created).total_seconds()
            
            return {
                'timestamp': last_result.date_done.isoformat() if last_result.date_done else None,
                'relative_time': self._format_relative_time(last_result.date_done) if last_result.date_done else 'Unknown',
                'status': last_result.status,
                'duration': duration,
                'result': last_result.result if last_result.status == 'SUCCESS' else last_result.traceback
            }
            
        except Exception as e:
            logger.error(f"Failed to get last run for {task_name}: {str(e)}")
            return {
                'timestamp': None,
                'relative_time': 'Error',
                'status': 'UNKNOWN',
                'duration': None,
                'result': str(e)
            }
    
    def _get_last_run_from_inspect(self, task_name):
        """Fallback method when TaskResult is not available"""
        # Return basic info - task is registered and scheduled
        return {
            'timestamp': None,
            'relative_time': 'History not available',
            'status': 'SCHEDULED',
            'duration': None,
            'result': 'Task history tracking requires django-celery-results'
        }
    
    def _calculate_next_run(self, schedule_obj):
        """Calculate when the task will run next"""
        if not schedule_obj:
            return {
                'timestamp': None,
                'relative_time': 'Not scheduled'
            }
        
        try:
            now = timezone.now()
            
            if isinstance(schedule_obj, crontab):
                # Calculate next run from crontab
                next_run = schedule_obj.remaining_estimate(now)
                next_timestamp = now + next_run
            elif isinstance(schedule_obj, celery_schedule):
                # Calculate next run from interval
                next_run = schedule_obj.remaining_estimate(now)
                next_timestamp = now + next_run
            else:
                return {
                    'timestamp': None,
                    'relative_time': 'Unknown schedule type'
                }
            
            return {
                'timestamp': next_timestamp.isoformat(),
                'relative_time': self._format_relative_time(next_timestamp, future=True)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate next run: {str(e)}")
            return {
                'timestamp': None,
                'relative_time': 'Calculation error'
            }
    
    def _get_task_statistics(self, task_name):
        """Get statistics for task executions in last 24 hours"""
        if not CELERY_RESULTS_AVAILABLE or not TaskResult:
            return {
                'runs_24h': None,
                'success_count': None,
                'failure_count': None,
                'success_rate': None,
                'avg_duration': None
            }
        
        try:
            since = timezone.now() - timedelta(hours=24)
            
            # Exclude REVOKED tasks from statistics - they're not real executions
            results = TaskResult.objects.filter(
                task_name=task_name,
                date_done__gte=since
            ).exclude(
                status='REVOKED'
            )
            
            total_runs = results.count()
            success_count = results.filter(status='SUCCESS').count()
            failure_count = results.filter(status='FAILURE').count()
            
            # Calculate average duration
            durations = []
            for result in results:
                if result.date_done and hasattr(result, 'date_created'):
                    duration = (result.date_done - result.date_created).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else None
            
            return {
                'runs_24h': total_runs,
                'success_count': success_count,
                'failure_count': failure_count,
                'success_rate': (success_count / total_runs * 100) if total_runs > 0 else 100,
                'avg_duration': round(avg_duration, 2) if avg_duration else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics for {task_name}: {str(e)}")
            return {
                'runs_24h': 0,
                'success_count': 0,
                'failure_count': 0,
                'success_rate': 100,
                'avg_duration': None
            }
    
    def _determine_task_status(self, last_run, is_registered):
        """Determine overall status of a task"""
        if not is_registered:
            return 'CRITICAL', 'Task not registered in workers'
        
        if not last_run['timestamp']:
            return 'WARNING', 'Never executed'
        
        last_status = last_run['status']
        
        if last_status == 'SUCCESS':
            return 'SUCCESS', 'Running normally'
        elif last_status == 'FAILURE':
            return 'FAILURE', 'Last execution failed'
        elif last_status == 'RETRY':
            return 'WARNING', 'Task retrying'
        else:
            return 'WARNING', f'Status: {last_status}'
    
    def _determine_overall_status(self, healthy, failed, warnings, total):
        """Determine overall system status"""
        if failed > 0:
            return 'CRITICAL'
        elif warnings > 0:
            return 'WARNING'
        elif healthy == total:
            return 'HEALTHY'
        else:
            return 'UNKNOWN'
    
    def _format_schedule(self, schedule_obj):
        """Format schedule for display"""
        if not schedule_obj:
            return 'Not scheduled'
        
        if isinstance(schedule_obj, crontab):
            return f"Cron: {schedule_obj}"
        elif isinstance(schedule_obj, celery_schedule):
            return f"Every {schedule_obj.run_every}"
        else:
            return str(schedule_obj)
    
    def _format_relative_time(self, dt, future=False):
        """Format datetime as relative time"""
        if not dt:
            return 'Unknown'
        
        now = timezone.now()
        if future:
            delta = dt - now
        else:
            delta = now - dt
        
        seconds = int(delta.total_seconds())
        
        if seconds < 0:
            return 'Just now'
        elif seconds < 60:
            return f"{seconds}s {'from now' if future else 'ago'}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m {'from now' if future else 'ago'}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h {'from now' if future else 'ago'}"
        else:
            days = seconds // 86400
            return f"{days}d {'from now' if future else 'ago'}"


def get_task_status():
    """Get current task status - API endpoint function"""
    monitor = TaskMonitor()
    return monitor.get_task_status()


# API View function for Django URLs
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def task_status_api(request):
    """API endpoint for task status - for use in urls.py"""
    data = get_task_status()
    return JsonResponse(data)
