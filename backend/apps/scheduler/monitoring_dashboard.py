"""
Enhanced Scheduler Monitoring and Alerting System

This module provides comprehensive monitoring capabilities for the EDMS scheduler,
including visual indicators, manual task triggering, and real-time status monitoring.
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render
from celery import current_app
from celery.events.state import State
import json
import logging

from .automated_tasks import (
    process_document_effective_dates,
    process_document_obsoletion_dates,
    check_workflow_timeouts,
    perform_system_health_check,
    cleanup_workflow_tasks
)
from ..documents.models import Document
from ..workflows.models import DocumentWorkflow
from ..audit.models import AuditTrail

logger = logging.getLogger(__name__)


class SchedulerMonitoringService:
    """
    Comprehensive scheduler monitoring service providing:
    - Real-time task status monitoring
    - Manual task triggering capabilities  
    - Visual health indicators
    - Performance metrics and alerting
    """
    
    def __init__(self):
        self.available_tasks = {
            'process_document_effective_dates': {
                'name': 'Document Effective Date Processing',
                'description': 'Automatically activates documents that have reached their effective date',
                'category': 'Document Lifecycle',
                'priority': 'HIGH',
                'icon': '📅',
                'celery_task': process_document_effective_dates
            },
            'process_document_obsoletion_dates': {
                'name': 'Document Obsolescence Processing', 
                'description': 'Automatically obsoletes documents that have reached their obsolescence date',
                'category': 'Document Lifecycle',
                'priority': 'HIGH',
                'icon': '🗃️',
                'celery_task': process_document_obsoletion_dates
            },
            'check_workflow_timeouts': {
                'name': 'Workflow Timeout Monitoring',
                'description': 'Monitors workflows for timeouts and sends escalation notifications',
                'category': 'Workflow Monitoring',
                'priority': 'MEDIUM',
                'icon': '⏰',
                'celery_task': check_workflow_timeouts
            },
            'perform_system_health_check': {
                'name': 'System Health Check',
                'description': 'Performs comprehensive system health validation and monitoring',
                'category': 'System Monitoring',
                'priority': 'LOW',
                'icon': '🏥',
                'celery_task': perform_system_health_check
            },
            'cleanup_workflow_tasks': {
                'name': 'Workflow Cleanup',
                'description': 'Cleans up orphaned and obsolete workflow tasks',
                'category': 'Maintenance',
                'priority': 'LOW',
                'icon': '🧹',
                'celery_task': cleanup_workflow_tasks
            },
            # Backup System Tasks (S4 Module)
            'run_scheduled_backup': {
                'name': 'Scheduled Backup Execution',
                'description': 'Execute scheduled database and file backups (daily/weekly/monthly)',
                'category': 'Backup & Recovery',
                'priority': 'CRITICAL',
                'icon': '💾',
                'celery_task': None  # Will be imported dynamically
            },
            'cleanup_old_backups': {
                'name': 'Backup Retention Management',
                'description': 'Remove old backups based on configured retention policies',
                'category': 'Backup & Recovery',
                'priority': 'MEDIUM',
                'icon': '🗑️',
                'celery_task': None  # Will be imported dynamically
            }
        }
    
    def get_scheduler_status(self):
        """
        Get comprehensive scheduler status including:
        - Celery worker status
        - Task execution statistics
        - System health indicators
        - Recent execution history
        """
        try:
            # Check Celery worker status
            celery_status = self._check_celery_workers()
            
            # Get task execution statistics
            task_stats = self._get_task_statistics()
            
            # Get system health metrics
            health_metrics = self._get_health_metrics()
            
            # Get recent execution history
            recent_executions = self._get_recent_executions()
            
            # Calculate overall health score with detailed breakdown
            health_score, health_breakdown = self._calculate_health_score(celery_status, task_stats, health_metrics)
            
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': self._determine_overall_status(health_score),
                'health_score': health_score,
                'health_breakdown': health_breakdown,
                'celery_status': celery_status,
                'task_statistics': task_stats,
                'health_metrics': health_metrics,
                'recent_executions': recent_executions,
                'available_tasks': self._format_available_tasks(),
                'alerts': self._generate_alerts(celery_status, task_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {str(e)}")
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'CRITICAL',
                'error': str(e),
                'health_score': 0
            }
    
    def manually_execute_task(self, task_name, user=None, dry_run=False):
        """
        Manually execute a scheduled task with full audit trail.
        
        Args:
            task_name: Name of the task to execute
            user: User requesting the execution
            dry_run: Whether to perform a dry run (for applicable tasks)
        
        Returns:
            Execution result with status and details
        """
        if task_name not in self.available_tasks:
            return {
                'success': False,
                'error': f'Unknown task: {task_name}',
                'available_tasks': list(self.available_tasks.keys())
            }
        
        task_info = self.available_tasks[task_name]
        
        try:
            with transaction.atomic():
                # Create audit record for manual execution
                start_time = timezone.now()
                
                # Get an existing user for audit trail
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if not user or not user.is_authenticated:
                    # Use the first available staff user or admin user
                    user = User.objects.filter(is_staff=True, is_active=True).first()
                    if not user:
                        # If no staff users exist, use any active user
                        user = User.objects.filter(is_active=True).first()
                    if not user:
                        # If no users exist at all, create a minimal system user
                        user = User.objects.create(
                            username='admin',
                            email='admin@edms.local',
                            is_staff=True,
                            is_active=True
                        )
                
                AuditTrail.objects.create(
                    user=user,
                    action='TASK_EXECUTION_STARTED',
                    description=f'Manual execution: {task_info["name"]}'[:200],
                    field_changes={
                        'task_name': task_name,
                        'task_description': task_info['description'],
                        'dry_run': dry_run,
                        'execution_time': start_time.isoformat()
                    },
                    ip_address=getattr(user, '_current_ip', '127.0.0.1'),
                    user_agent=getattr(user, '_current_user_agent', 'Manual Execution')
                )
                
                # Execute the task
                celery_task = task_info['celery_task']
                
                # Handle tasks that support dry_run parameter
                if task_name == 'cleanup_workflow_tasks':
                    result = celery_task.apply(kwargs={'dry_run': dry_run})
                else:
                    result = celery_task.apply()
                
                end_time = timezone.now()
                duration = (end_time - start_time).total_seconds()
                
                # Create completion audit record
                AuditTrail.objects.create(
                    user=user,
                    action='TASK_EXECUTION_COMPLETED',
                    description=f'Completed: {task_info["name"]}'[:200],
                    field_changes={
                        'task_name': task_name,
                        'success': result.successful(),
                        'duration_seconds': duration,
                        'result': result.result if result.successful() else str(result.result),
                        'dry_run': dry_run
                    },
                    ip_address=getattr(user, '_current_ip', '127.0.0.1'),
                    user_agent=getattr(user, '_current_user_agent', 'Manual Execution')
                )
                
                return {
                    'success': result.successful(),
                    'task_name': task_name,
                    'task_display_name': task_info['name'],
                    'execution_time': start_time.isoformat(),
                    'duration_seconds': duration,
                    'result': result.result if result.successful() else str(result.result),
                    'dry_run': dry_run,
                    'executed_by': user.get_full_name() or user.username
                }
                
        except Exception as e:
            logger.error(f"Failed to execute task {task_name}: {str(e)}")
            
            # Create error audit record
            AuditTrail.objects.create(
                user=user,
                action='TASK_EXECUTION_FAILED',
                description=f'Failed: {task_info["name"]} - {str(e)}'[:200],
                field_changes={
                    'task_name': task_name,
                    'error': str(e),
                    'dry_run': dry_run
                },
                ip_address=getattr(user, '_current_ip', '127.0.0.1'),
                user_agent=getattr(user, '_current_user_agent', 'Manual Execution')
            )
            
            return {
                'success': False,
                'task_name': task_name,
                'error': str(e),
                'executed_by': user.get_full_name() or user.username
            }
    
    def _check_celery_workers(self):
        """Check status of Celery workers and beat scheduler."""
        try:
            inspect = current_app.control.inspect()
            
            # Check active workers
            active_workers = inspect.active() or {}
            
            # Check scheduled tasks from beat
            scheduled_tasks = inspect.scheduled() or {}
            
            # Check worker statistics
            stats = inspect.stats() or {}
            
            worker_count = len(active_workers)
            beat_status = 'RUNNING' if scheduled_tasks else 'UNKNOWN'
            
            return {
                'worker_count': worker_count,
                'workers_active': worker_count > 0,
                'beat_status': beat_status,
                'active_workers': list(active_workers.keys()),
                'scheduled_task_count': sum(len(tasks) for tasks in scheduled_tasks.values()),
                'worker_stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to check Celery workers: {str(e)}")
            return {
                'worker_count': 0,
                'workers_active': False,
                'beat_status': 'ERROR',
                'error': str(e)
            }
    
    def _get_task_statistics(self):
        """Get statistics about document processing tasks and backup jobs."""
        try:
            now = timezone.now()
            today = now.date()
            recent_24h = now - timezone.timedelta(hours=24)
            
            stats = {
                'documents_pending_effective': Document.objects.filter(
                    status='APPROVED_PENDING_EFFECTIVE',
                    effective_date__lte=today
                ).count(),
                'documents_scheduled_obsolescence': Document.objects.filter(
                    status='SCHEDULED_FOR_OBSOLESCENCE',
                    obsolescence_date__lte=today
                ).count(),
                'active_workflows': DocumentWorkflow.objects.filter(
                    is_terminated=False
                ).count(),
                'overdue_workflows': DocumentWorkflow.objects.filter(
                    is_terminated=False,
                    due_date__lt=today
                ).count(),
                'documents_processed_today': AuditTrail.objects.filter(
                    action__in=['DOCUMENT_EFFECTIVE_DATE_PROCESSED', 'DOCUMENT_OBSOLETED'],
                    timestamp__date=today
                ).count()
            }
            
            # Add backup statistics
            try:
                from apps.backup.models import BackupJob, BackupConfiguration
                
                stats['backup_jobs_last_24h'] = BackupJob.objects.filter(
                    created_at__gte=recent_24h
                ).count()
                
                stats['backup_jobs_failed_24h'] = BackupJob.objects.filter(
                    created_at__gte=recent_24h,
                    status='FAILED'
                ).count()
                
                stats['backup_jobs_completed_24h'] = BackupJob.objects.filter(
                    created_at__gte=recent_24h,
                    status='COMPLETED'
                ).count()
                
                stats['enabled_backup_configs'] = BackupConfiguration.objects.filter(
                    is_enabled=True,
                    status='ACTIVE'
                ).count()
                
                last_successful = BackupJob.objects.filter(
                    status='COMPLETED'
                ).order_by('-completed_at').first()
                
                if last_successful:
                    hours_since = (now - last_successful.completed_at).total_seconds() / 3600
                    stats['last_successful_backup_hours_ago'] = round(hours_since, 1)
                else:
                    stats['last_successful_backup_hours_ago'] = None
                    
            except Exception as backup_error:
                logger.warning(f"Could not fetch backup statistics: {str(backup_error)}")
                stats['backup_jobs_last_24h'] = 0
                stats['backup_jobs_failed_24h'] = 0
                stats['backup_jobs_completed_24h'] = 0
                stats['enabled_backup_configs'] = 0
                stats['last_successful_backup_hours_ago'] = None
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get task statistics: {str(e)}")
            return {}
    
    def _get_health_metrics(self):
        """Get system health metrics."""
        try:
            recent_time = timezone.now() - timezone.timedelta(hours=24)
            
            metrics = {
                'database_responsive': True,  # If we get here, DB is working
                'total_documents': Document.objects.count(),
                'recent_audit_records': AuditTrail.objects.filter(
                    timestamp__gte=recent_time
                ).count(),
                'scheduler_errors_24h': AuditTrail.objects.filter(
                    timestamp__gte=recent_time,
                    action__contains='FAILED'
                ).count(),
                'successful_automations_24h': AuditTrail.objects.filter(
                    timestamp__gte=recent_time,
                    action__in=['DOCUMENT_EFFECTIVE_DATE_PROCESSED', 'DOCUMENT_OBSOLETED']
                ).count()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get health metrics: {str(e)}")
            return {'database_responsive': False, 'error': str(e)}
    
    def _get_recent_executions(self, limit=10):
        """Get recent task executions from audit trail."""
        try:
            recent_executions = AuditTrail.objects.filter(
                action__in=[
                    'MANUAL_TASK_EXECUTION_COMPLETED',
                    'DOCUMENT_EFFECTIVE_DATE_PROCESSED', 
                    'DOCUMENT_OBSOLETED',
                    'WORKFLOW_HEALTH_WARNING',
                    'SYSTEM_HEALTH_CHECK'
                ]
            ).order_by('-timestamp')[:limit]
            
            return [{
                'timestamp': record.timestamp.isoformat(),
                'action': record.action,
                'description': record.description,
                'user': record.user.get_full_name() if record.user else 'System',
                'success': 'FAILED' not in record.action
            } for record in recent_executions]
            
        except Exception as e:
            logger.error(f"Failed to get recent executions: {str(e)}")
            return []
    
    def _calculate_health_score(self, celery_status, task_stats, health_metrics):
        """Calculate overall health score (0-100) with detailed breakdown."""
        score = 0
        breakdown = {
            'total_score': 0,
            'max_possible': 100,
            'components': {}
        }
        
        # Celery workers (30 points)
        workers_active = celery_status.get('workers_active', False)
        worker_count = celery_status.get('worker_count', 0)
        worker_score = 30 if workers_active else 0
        score += worker_score
        breakdown['components']['celery_workers'] = {
            'score': worker_score,
            'max_score': 30,
            'status': 'healthy' if workers_active else 'unhealthy',
            'details': f'{worker_count} active worker(s)',
            'recommendation': 'Working properly' if workers_active else 'Start Celery workers to enable task processing'
        }
        
        # Beat scheduler (20 points)
        beat_status = celery_status.get('beat_status', 'UNKNOWN')
        beat_score = 20 if beat_status == 'RUNNING' else 0
        score += beat_score
        breakdown['components']['beat_scheduler'] = {
            'score': beat_score,
            'max_score': 20,
            'status': 'healthy' if beat_status == 'RUNNING' else 'unhealthy',
            'details': f'Beat scheduler: {beat_status}',
            'recommendation': 'Scheduler running normally' if beat_status == 'RUNNING' else 'Start Celery Beat to enable scheduled tasks'
        }
        
        # Database responsiveness (20 points)
        db_responsive = health_metrics.get('database_responsive', False)
        db_score = 20 if db_responsive else 0
        score += db_score
        total_docs = health_metrics.get('total_documents', 0)
        breakdown['components']['database'] = {
            'score': db_score,
            'max_score': 20,
            'status': 'healthy' if db_responsive else 'unhealthy',
            'details': f'Database responsive, {total_docs} documents stored',
            'recommendation': 'Database operating normally' if db_responsive else 'Check database connectivity and restart if needed'
        }
        
        # Recent errors (20 points - deduct for errors)
        recent_errors = health_metrics.get('scheduler_errors_24h', 0)
        successful_automations = health_metrics.get('successful_automations_24h', 0)
        if recent_errors == 0:
            error_score = 20
            error_status = 'excellent'
            error_recommendation = 'No recent errors - system operating perfectly'
        elif recent_errors <= 5:
            error_score = 15
            error_status = 'good'
            error_recommendation = f'{recent_errors} minor errors in 24h - within acceptable range for development'
        elif recent_errors <= 10:
            error_score = 10
            error_status = 'warning'
            error_recommendation = f'{recent_errors} errors in 24h - investigate recurring issues'
        else:
            error_score = 0
            error_status = 'critical'
            error_recommendation = f'{recent_errors} errors in 24h - immediate attention required'
        
        score += error_score
        breakdown['components']['recent_errors'] = {
            'score': error_score,
            'max_score': 20,
            'status': error_status,
            'details': f'{recent_errors} errors, {successful_automations} successful automations in last 24h',
            'recommendation': error_recommendation
        }
        
        # Overdue workflows (10 points - deduct for overdue items)
        overdue = task_stats.get('overdue_workflows', 0)
        active_workflows = task_stats.get('active_workflows', 0)
        if overdue == 0:
            workflow_score = 10
            workflow_status = 'excellent'
            workflow_recommendation = 'All workflows on schedule'
        elif overdue <= 5:
            workflow_score = 5
            workflow_status = 'acceptable'
            workflow_recommendation = f'{overdue} overdue workflows - review and expedite'
        else:
            workflow_score = 0
            workflow_status = 'critical'
            workflow_recommendation = f'{overdue} overdue workflows - immediate action required'
        
        score += workflow_score
        breakdown['components']['workflow_timeliness'] = {
            'score': workflow_score,
            'max_score': 10,
            'status': workflow_status,
            'details': f'{overdue} overdue of {active_workflows} active workflows',
            'recommendation': workflow_recommendation
        }
        
        breakdown['total_score'] = min(100, score)
        breakdown['score_interpretation'] = self._get_score_interpretation(breakdown['total_score'])
        
        return min(100, score), breakdown
    
    def _get_score_interpretation(self, score):
        """Provide interpretation of the health score."""
        if score >= 95:
            return {
                'level': 'EXCELLENT',
                'description': 'System operating at peak performance with minimal issues',
                'color': 'green'
            }
        elif score >= 85:
            return {
                'level': 'VERY GOOD', 
                'description': 'System performing well with only minor issues',
                'color': 'green'
            }
        elif score >= 75:
            return {
                'level': 'GOOD',
                'description': 'System functioning properly but has some areas for improvement',
                'color': 'yellow-green'
            }
        elif score >= 60:
            return {
                'level': 'ACCEPTABLE',
                'description': 'System operational but requires attention to improve reliability',
                'color': 'yellow'
            }
        elif score >= 40:
            return {
                'level': 'WARNING',
                'description': 'System has significant issues that need addressing',
                'color': 'orange'
            }
        elif score >= 20:
            return {
                'level': 'CRITICAL',
                'description': 'System experiencing major problems requiring immediate attention',
                'color': 'red'
            }
        else:
            return {
                'level': 'FAILURE',
                'description': 'System is not functioning properly and requires urgent intervention',
                'color': 'red'
            }
    
    def _determine_overall_status(self, health_score):
        """Determine overall status based on health score."""
        if health_score >= 90:
            return 'EXCELLENT'
        elif health_score >= 75:
            return 'GOOD'
        elif health_score >= 50:
            return 'WARNING'
        elif health_score >= 25:
            return 'CRITICAL'
        else:
            return 'FAILURE'
    
    def _format_available_tasks(self):
        """Format available tasks for API response."""
        return {
            name: {
                'name': info['name'],
                'description': info['description'],
                'category': info['category'],
                'priority': info['priority'],
                'icon': info['icon']
            } for name, info in self.available_tasks.items()
        }
    
    def _generate_alerts(self, celery_status, task_stats):
        """Generate alerts based on current system status."""
        alerts = []
        
        if not celery_status.get('workers_active', False):
            alerts.append({
                'level': 'CRITICAL',
                'message': 'No Celery workers are active - automated tasks will not execute',
                'action': 'Check Celery worker containers and restart if necessary'
            })
        
        if celery_status.get('beat_status') != 'RUNNING':
            alerts.append({
                'level': 'CRITICAL', 
                'message': 'Celery beat scheduler is not running - scheduled tasks will not execute',
                'action': 'Check Celery beat container and restart if necessary'
            })
        
        pending_effective = task_stats.get('documents_pending_effective', 0)
        if pending_effective > 10:
            alerts.append({
                'level': 'WARNING',
                'message': f'{pending_effective} documents are pending effective date processing',
                'action': 'Consider manually triggering effective date processing'
            })
        
        overdue_workflows = task_stats.get('overdue_workflows', 0)
        if overdue_workflows > 5:
            alerts.append({
                'level': 'WARNING',
                'message': f'{overdue_workflows} workflows are overdue',
                'action': 'Review overdue workflows and consider escalation'
            })
        
        # Backup system alerts
        failed_backups = task_stats.get('backup_jobs_failed_24h', 0)
        if failed_backups > 0:
            alerts.append({
                'level': 'CRITICAL',
                'message': f'{failed_backups} backup job(s) failed in the last 24 hours',
                'action': 'Check backup logs and verify storage availability'
            })
        
        last_backup_hours = task_stats.get('last_successful_backup_hours_ago')
        if last_backup_hours is not None and last_backup_hours > 48:
            alerts.append({
                'level': 'CRITICAL',
                'message': f'No successful backup in {last_backup_hours:.1f} hours',
                'action': 'Verify backup system is running and investigate failures'
            })
        elif last_backup_hours is not None and last_backup_hours > 30:
            alerts.append({
                'level': 'WARNING',
                'message': f'Last successful backup was {last_backup_hours:.1f} hours ago',
                'action': 'Monitor backup system - may need attention soon'
            })
        
        enabled_backups = task_stats.get('enabled_backup_configs', 0)
        if enabled_backups == 0:
            alerts.append({
                'level': 'WARNING',
                'message': 'No backup configurations are enabled',
                'action': 'Enable backup configurations to ensure data protection'
            })
        
        return alerts


# Service instance
monitoring_service = SchedulerMonitoringService()


# API Views
def scheduler_status_api(request):
    """API endpoint for comprehensive scheduler status."""
    try:
        status_data = monitoring_service.get_scheduler_status()
        return JsonResponse(status_data, json_dumps_params={'indent': 2})
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
def manual_trigger_api(request):
    """API endpoint for manually triggering scheduler tasks."""
    try:
        data = json.loads(request.body)
        task_name = data.get('task_name')
        dry_run = data.get('dry_run', False)
        
        if not task_name:
            return JsonResponse({
                'error': 'task_name is required'
            }, status=400)
        
        # Pass user if authenticated, otherwise None (will use system user)
        user = request.user if request.user.is_authenticated else None
        
        result = monitoring_service.manually_execute_task(
            task_name=task_name,
            user=user,
            dry_run=dry_run
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


def scheduler_dashboard(request):
    """Render the scheduler monitoring dashboard - open access for internal monitoring."""
    # Allow open access for internal monitoring dashboard
    try:
        status_data = monitoring_service.get_scheduler_status()
        
        context = {
            'status_data': status_data,
            'page_title': 'EDMS Scheduler Monitoring Dashboard'
        }
        
        return render(request, 'scheduler/monitoring_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Failed to render scheduler dashboard: {str(e)}")
        context = {
            'error': str(e),
            'page_title': 'EDMS Scheduler Dashboard - Error'
        }
        return render(request, 'scheduler/monitoring_dashboard.html', context)