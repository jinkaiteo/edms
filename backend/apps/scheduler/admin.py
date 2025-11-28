"""
Django Admin Configuration for Scheduler Module (S3)

Provides comprehensive admin interface for scheduler monitoring and management.
Superuser-only access for system administration.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json

from .models import ScheduledTask, NotificationQueue
from .notification_admin import NotificationQueueAdmin
from .automated_tasks import (
    process_document_effective_dates, 
    process_document_obsoletion_dates,
    perform_system_health_check,
    check_workflow_timeouts,
    cleanup_workflow_tasks
)


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    """Admin interface for scheduled tasks with monitoring capabilities."""
    
    list_display = [
        'name', 
        'status_badge', 
        'last_run_time', 
        'schedule_display', 
        'run_count',
        'success_rate_display',
        'is_enabled',
        'actions_column'
    ]
    
    list_filter = [
        'status',
        'task_type',
        'frequency_type',
        'created_at',
        'last_run'
    ]
    
    search_fields = [
        'name',
        'description',
        'task_type'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_run',
        'total_runs',
        'successful_runs',
        'failed_runs',
        'last_error',
        'execution_history_display'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': (
                'name',
                'description',
                'task_type',
                'status'
            )
        }),
        ('Schedule Configuration', {
            'fields': (
                'frequency_type',
                'cron_expression',
                'interval_value'
            )
        }),
        ('Execution Statistics', {
            'fields': (
                'total_runs',
                'successful_runs',
                'failed_runs',
                'last_run',
                'last_error'
            ),
            'classes': ('collapse',)
        }),
        ('Execution History', {
            'fields': (
                'execution_history_display',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'ACTIVE': 'green',
            'INACTIVE': 'gray',
            'ERROR': 'red',
            'RUNNING': 'orange'
        }
        color = colors.get(obj.status, 'blue')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = 'Status'
    
    def last_run_time(self, obj):
        """Display last run time."""
        if obj.last_run:
            return obj.last_run.strftime('%Y-%m-%d %H:%M:%S')
        return 'Never'
    last_run_time.short_description = 'Last Run'
    
    def schedule_display(self, obj):
        """Display schedule configuration."""
        return f"{obj.get_frequency_type_display()}" + (f" ({obj.cron_expression})" if obj.cron_expression else "")
    schedule_display.short_description = 'Schedule'
    
    def run_count(self, obj):
        """Display total run count."""
        return obj.total_runs
    run_count.short_description = 'Runs'
    
    def is_enabled(self, obj):
        """Display enabled status."""
        return obj.status == 'ACTIVE'
    is_enabled.boolean = True
    is_enabled.short_description = 'Enabled'
    
    def success_rate_display(self, obj):
        """Display success rate with progress bar."""
        if obj.total_runs == 0:
            return format_html('<span style="color: gray;">No executions</span>')
        
        success_rate = (obj.successful_runs / obj.total_runs) * 100
        color = 'green' if success_rate >= 90 else 'orange' if success_rate >= 70 else 'red'
        
        return format_html(
            '<div style="background: #f0f0f0; border-radius: 3px; padding: 2px;">'
            '<div style="background: {}; width: {}%; height: 12px; border-radius: 2px;"></div>'
            '<small>{} % ({}/{})</small>'
            '</div>',
            color,
            success_rate,
            round(success_rate, 1),
            obj.successful_runs,
            obj.total_runs
        )
    success_rate_display.short_description = 'Success Rate'
    
    def actions_column(self, obj):
        """Action buttons for manual task execution."""
        return format_html(
            '<a class="button" style="background: #417690; color: white; padding: 5px 10px; '
            'text-decoration: none; border-radius: 3px; font-size: 11px; margin-right: 5px;" '
            'href="{}">Execute Now</a>'
            '<a class="button" style="background: #ba2121; color: white; padding: 5px 10px; '
            'text-decoration: none; border-radius: 3px; font-size: 11px;" '
            'href="{}">View Logs</a>',
            reverse('admin:scheduler_execute_task', args=[obj.pk]),
            reverse('admin:scheduler_task_logs', args=[obj.pk])
        )
    actions_column.short_description = 'Actions'
    
    def execution_history_display(self, obj):
        """Display execution history in a formatted table."""
        # Show basic execution stats based on available model fields
        if obj.total_runs == 0:
            return format_html('<em>No execution history available</em>')
        
        # Create simple execution summary
        last_run_str = obj.last_run.strftime('%Y-%m-%d %H:%M:%S') if obj.last_run else 'Never'
        success_rate = round((obj.successful_runs / obj.total_runs) * 100, 1) if obj.total_runs > 0 else 0
        
        html = f'''
        <div style="font-size: 12px; line-height: 1.4;">
            <strong>Execution Summary:</strong><br>
            • Total Runs: {obj.total_runs}<br>
            • Successful: {obj.successful_runs}<br>
            • Failed: {obj.failed_runs}<br>
            • Success Rate: {success_rate}%<br>
            • Last Run: {last_run_str}<br>
        '''
        
        if obj.last_error:
            html += f'• Last Error: {obj.last_error[:100]}...<br>'
            
        html += '</div>'
        return format_html(html)
    execution_history_display.short_description = 'Recent Executions'
    
    def get_urls(self):
        """Add custom URLs for task execution and monitoring."""
        from django.urls import path
        
        urls = super().get_urls()
        custom_urls = [
            path(
                'execute-task/<int:task_id>/',
                self.admin_site.admin_view(self.execute_task_view),
                name='scheduler_execute_task'
            ),
            path(
                'task-logs/<int:task_id>/',
                self.admin_site.admin_view(self.task_logs_view),
                name='scheduler_task_logs'
            ),
            path(
                'system-health/',
                self.admin_site.admin_view(self.system_health_view),
                name='scheduler_system_health'
            ),
            path(
                'dashboard/',
                self.admin_site.admin_view(self.dashboard_view),
                name='scheduler_scheduledtask_dashboard'
            ),
            path(
                'notifications/',
                self.admin_site.admin_view(self.notification_dashboard_view),
                name='scheduler_notification_dashboard'
            ),
        ]
        return custom_urls + urls
    
    def execute_task_view(self, request, task_id):
        """Execute a scheduled task manually."""
        try:
            task = ScheduledTask.objects.get(pk=task_id)
            
            # Map task names to actual Celery tasks
            task_mapping = {
                'process_document_effective_dates': process_document_effective_dates,
                'process_document_obsoletion_dates': process_document_obsoletion_dates,
                'perform_system_health_check': perform_system_health_check,
                'check_workflow_timeouts': check_workflow_timeouts,
                'cleanup_workflow_tasks': cleanup_workflow_tasks
            }
            
            celery_task = task_mapping.get(task.task_function)
            
            if celery_task:
                result = celery_task.apply()
                messages.success(
                    request, 
                    f"Task '{task.task_function}' executed successfully. Result: {result.result}"
                )
            else:
                messages.error(request, f"Task '{task.task_function}' not found in task mapping.")
                
        except ScheduledTask.DoesNotExist:
            messages.error(request, f"Task with ID {task_id} not found.")
        except Exception as e:
            messages.error(request, f"Error executing task: {str(e)}")
        
        return redirect('admin:scheduler_scheduledtask_changelist')
    
    def task_logs_view(self, request, task_id):
        """View detailed logs for a specific task."""
        try:
            task = ScheduledTask.objects.get(pk=task_id)
            
            # Use actual model fields that exist
            logs_data = {
                'task_info': {
                    'id': task.id,
                    'name': task.name,
                    'task_function': task.task_function,
                    'task_module': task.task_module,
                    'description': task.description,
                    'status': task.status,
                    'task_type': task.task_type
                },
                'schedule': {
                    'frequency_type': task.frequency_type,
                    'cron_expression': task.cron_expression,
                    'interval_value': task.interval_value,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                },
                'execution_statistics': {
                    'total_runs': task.total_runs,
                    'successful_runs': task.successful_runs,
                    'failed_runs': task.failed_runs,
                    'success_rate': round((task.successful_runs / task.total_runs * 100), 2) if task.total_runs > 0 else 0,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'last_error': task.last_error
                },
                'configuration': {
                    'timeout_seconds': task.timeout_seconds,
                    'max_retries': task.max_retries,
                    'retry_delay_seconds': task.retry_delay_seconds,
                    'task_kwargs': task.task_kwargs
                },
                'metadata': {
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                    'created_by': task.created_by.username if task.created_by else None
                }
            }
            
            return JsonResponse(logs_data, json_dumps_params={'indent': 2})
        except ScheduledTask.DoesNotExist:
            return JsonResponse({'error': f'Task with ID {task_id} not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error retrieving task logs: {str(e)}'}, status=500)
    
    def system_health_view(self, request):
        """Perform and display system health check."""
        try:
            result = perform_system_health_check.apply()
            return JsonResponse(result.result, json_dumps_params={'indent': 2})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def dashboard_view(self, request):
        """Scheduler dashboard with system overview."""
        from django.template.response import TemplateResponse
        
        # Get task statistics
        total_tasks = ScheduledTask.objects.count()
        active_tasks = ScheduledTask.objects.filter(status='ACTIVE').count()
        
        recent_executions = []
        for task in ScheduledTask.objects.all():
            if task.total_runs > 0:
                # Create mock recent execution data based on available fields
                recent_executions.append({
                    'task_name': task.name,
                    'timestamp': task.last_run.strftime('%Y-%m-%d %H:%M:%S') if task.last_run else 'Never',
                    'success': task.successful_runs > 0,
                    'duration': 'N/A'
                })
        
        recent_executions.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        context = {
            'title': 'Scheduler Dashboard',
            'total_tasks': total_tasks,
            'active_tasks': active_tasks,
            'inactive_tasks': total_tasks - active_tasks,
            'recent_executions': recent_executions[:10],
            'opts': ScheduledTask._meta,
            'has_permission': True
        }
        
        return TemplateResponse(request, 'admin/scheduler/dashboard.html', context)
    
    def notification_dashboard_view(self, request):
        """Notification dashboard with comprehensive notification overview."""
        from django.template.response import TemplateResponse
        from django.conf import settings
        
        # Get notification statistics
        from .models import NotificationQueue
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        stats = {
            'total': NotificationQueue.objects.count(),
            'pending': NotificationQueue.objects.filter(status='PENDING').count(),
            'sent': NotificationQueue.objects.filter(status='SENT').count(),
            'failed': NotificationQueue.objects.filter(status='FAILED').count(),
        }
        
        # Recent notifications (last 24 hours)
        from datetime import timedelta
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_notifications = NotificationQueue.objects.filter(
            created_at__gte=recent_cutoff
        ).order_by('-created_at')[:10]
        
        # System information
        admin_count = User.objects.filter(is_superuser=True).count()
        users_with_email = User.objects.filter(email__isnull=False).exclude(email='').count()
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not configured')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')
        
        context = {
            'title': 'Notification Dashboard',
            'stats': stats,
            'recent_notifications': recent_notifications,
            'admin_count': admin_count,
            'users_with_email': users_with_email,
            'email_backend': email_backend,
            'from_email': from_email,
            'now': timezone.now(),
            'opts': NotificationQueue._meta,
            'has_permission': True
        }
        
        return TemplateResponse(request, 'admin/scheduler/notification_dashboard.html', context)


# Custom admin site configuration
class SchedulerAdminSite:
    """Custom methods for scheduler admin interface."""
    
    def get_app_list(self, request):
        """Customize the admin app list to highlight scheduler features."""
        app_list = super().get_app_list(request)
        
        # Add scheduler dashboard link
        for app in app_list:
            if app['app_label'] == 'scheduler':
                app['models'].insert(0, {
                    'name': 'Dashboard',
                    'object_name': 'dashboard',
                    'admin_url': reverse('admin:scheduler_dashboard'),
                    'add_url': None,
                    'view_only': True
                })
                app['models'].insert(1, {
                    'name': 'System Health',
                    'object_name': 'health',
                    'admin_url': reverse('admin:scheduler_system_health'),
                    'add_url': None,
                    'view_only': True
                })
                app['models'].insert(2, {
                    'name': 'Notification Dashboard',
                    'object_name': 'notification_dashboard',
                    'admin_url': reverse('admin:scheduler_notification_dashboard'),
                    'add_url': None,
                    'view_only': True
                })
        
        return app_list