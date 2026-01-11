"""
Django management command to set up scheduled tasks in the admin interface.

This command creates ScheduledTask entries that will be visible in the Django admin
at /admin/scheduler/scheduledtask/ for better task management and monitoring.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.scheduler.models import ScheduledTask
from datetime import timedelta


class Command(BaseCommand):
    help = 'Set up scheduled tasks in the Django admin interface'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing scheduled tasks if they already exist'
        )

    def handle(self, *args, **options):
        """Create or update scheduled tasks in the admin interface."""
        
        update_existing = options['update']
        
        self.stdout.write(
            self.style.SUCCESS('🕐 Setting up scheduled tasks in Django admin...')
        )
        
        # Define tasks to create
        tasks_to_create = [
            {
                'name': 'Workflow Task Cleanup',
                'task_type': 'CLEANUP',
                'schedule_type': 'PERIODIC',
                'cron_expression': '0 */6 * * *',  # Every 6 hours
                'description': 'Clean up orphaned, irrelevant, and expired workflow tasks',
                'is_active': True,
                'task_function': 'apps.scheduler.automated_tasks.cleanup_workflow_tasks',
                'task_kwargs': '{"dry_run": false}',
                'priority': 6,
                'timeout_minutes': 60,
                'retry_count': 2,
                'retry_delay_minutes': 15,
            },
            {
                'name': 'Weekly Comprehensive Cleanup',
                'task_type': 'MAINTENANCE',
                'schedule_type': 'PERIODIC',
                'cron_expression': '0 2 * * 0',  # Sunday 2 AM
                'description': 'Weekly comprehensive workflow task cleanup and system maintenance',
                'is_active': True,
                'task_function': 'apps.scheduler.automated_tasks.cleanup_workflow_tasks',
                'task_kwargs': '{"dry_run": false}',
                'priority': 5,
                'timeout_minutes': 120,
                'retry_count': 2,
                'retry_delay_minutes': 30,
            },
            {
                'name': 'Document Effective Date Processing',
                'task_type': 'AUTOMATION',
                'schedule_type': 'PERIODIC', 
                'cron_expression': '0 * * * *',  # Every hour
                'description': 'Process pending document effective dates and activate documents',
                'is_active': True,
                'task_function': 'apps.scheduler.automated_tasks.process_document_effective_dates',
                'task_kwargs': '{}',
                'priority': 8,
                'timeout_minutes': 60,
                'retry_count': 3,
                'retry_delay_minutes': 10,
            },
            {
                'name': 'Workflow Timeout Monitoring',
                'task_type': 'MONITORING',
                'schedule_type': 'PERIODIC',
                'cron_expression': '30 */4 * * *',  # Every 4 hours at :30
                'description': 'Monitor workflow timeouts and send escalation notifications',
                'is_active': True,
                'task_function': 'apps.scheduler.automated_tasks.check_workflow_timeouts',
                'task_kwargs': '{}',
                'priority': 6,
                'timeout_minutes': 120,
                'retry_count': 2,
                'retry_delay_minutes': 20,
            },
            {
                'name': 'System Health Check',
                'task_type': 'MONITORING',
                'schedule_type': 'PERIODIC',
                'cron_expression': '15 */2 * * *',  # Every 2 hours at :15
                'description': 'Perform comprehensive system health monitoring',
                'is_active': True,
                'task_function': 'apps.scheduler.automated_tasks.perform_system_health_check',
                'task_kwargs': '{}',
                'priority': 4,
                'timeout_minutes': 60,
                'retry_count': 2,
                'retry_delay_minutes': 15,
            },
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for task_data in tasks_to_create:
            task_name = task_data['name']
            
            # Check if task already exists
            existing_task = ScheduledTask.objects.filter(name=task_name).first()
            
            if existing_task:
                if update_existing:
                    # Update existing task
                    for field, value in task_data.items():
                        setattr(existing_task, field, value)
                    existing_task.updated_at = timezone.now()
                    existing_task.save()
                    
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Updated existing task: {task_name}')
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⏭️ Skipped existing task: {task_name} (use --update to modify)')
                    )
                    skipped_count += 1
            else:
                # Create new task
                task_data['created_at'] = timezone.now()
                task_data['updated_at'] = timezone.now()
                
                # Calculate next run time based on cron
                task_data['next_run_time'] = self._calculate_next_run(task_data['cron_expression'])
                
                ScheduledTask.objects.create(**task_data)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created new task: {task_name}')
                )
                created_count += 1
        
        # Display summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('📊 SCHEDULED TASK SETUP SUMMARY:'))
        self.stdout.write(f'  ✅ Created: {created_count}')
        self.stdout.write(f'  🔄 Updated: {updated_count}')
        self.stdout.write(f'  ⏭️ Skipped: {skipped_count}')
        self.stdout.write('=' * 50)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎯 Tasks are now visible in Django admin at:')
        )
        self.stdout.write('   http://localhost:8000/admin/scheduler/scheduledtask/')
        
        self.stdout.write(
            self.style.WARNING(f'\n💡 Note: These are for visibility/management only.')
        )
        self.stdout.write('   Actual execution is handled by Celery Beat.')
        self.stdout.write('   Make sure Celery Beat is running: celery -A edms beat')

    def _calculate_next_run(self, cron_expression):
        """Calculate next run time based on cron expression."""
        # Simple fallback calculation without external dependencies
        try:
            # Basic cron parsing for common patterns
            if cron_expression == '0 */6 * * *':  # Every 6 hours
                return timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=6)
            elif cron_expression == '0 2 * * 0':  # Sunday 2 AM
                return timezone.now().replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=7)
            elif cron_expression == '0 * * * *':  # Every hour
                return timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            elif cron_expression == '30 */4 * * *':  # Every 4 hours at :30
                return timezone.now().replace(minute=30, second=0, microsecond=0) + timedelta(hours=4)
            elif cron_expression == '15 */2 * * *':  # Every 2 hours at :15
                return timezone.now().replace(minute=15, second=0, microsecond=0) + timedelta(hours=2)
            else:
                # Default fallback
                return timezone.now() + timedelta(hours=1)
        except:
            # Fallback to 1 hour from now if calculation fails
            return timezone.now() + timedelta(hours=1)