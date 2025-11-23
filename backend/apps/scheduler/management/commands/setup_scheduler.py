"""
Django management command to set up the scheduler system.

This command initializes:
- Scheduled task configurations
- Celery Beat schedule entries
- System monitoring tasks
- Health check automation

Usage: python manage.py setup_scheduler
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.scheduler.models import ScheduledTask
from apps.scheduler.automated_tasks import (
    process_document_effective_dates,
    process_document_obsoletion_dates, 
    check_workflow_timeouts,
    perform_system_health_check
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up EDMS scheduler system with automated tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all scheduled tasks (delete existing)',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up EDMS Scheduler System...')
        
        if options['reset']:
            self.stdout.write('🗑️ Resetting existing scheduled tasks...')
            ScheduledTask.objects.all().delete()
            self.stdout.write('✅ Existing tasks cleared')

        # Create system user if not exists
        system_user = self._get_or_create_system_user()
        
        # Define scheduled tasks
        scheduled_tasks = [
            {
                'name': 'Document Effective Date Processing',
                'task_name': 'process_document_effective_dates',
                'description': 'Automatically process documents that have reached their effective date',
                'schedule_type': 'HOURLY',
                'is_active': True,
                'task_data': {
                    'task_type': 'document_automation',
                    'priority': 'HIGH',
                    'max_execution_time': 300,
                    'retry_count': 3
                }
            },
            {
                'name': 'Document Obsoletion Processing',
                'task_name': 'process_document_obsoletion_dates',
                'description': 'Automatically obsolete documents that have reached their obsoletion date',
                'schedule_type': 'HOURLY',
                'is_active': True,
                'task_data': {
                    'task_type': 'document_automation',
                    'priority': 'HIGH',
                    'max_execution_time': 300,
                    'retry_count': 3
                }
            },
            {
                'name': 'Workflow Timeout Monitoring',
                'task_name': 'check_workflow_timeouts',
                'description': 'Monitor workflows for timeouts and send notifications',
                'schedule_type': 'EVERY_4_HOURS',
                'is_active': True,
                'task_data': {
                    'task_type': 'workflow_monitoring',
                    'priority': 'MEDIUM',
                    'max_execution_time': 600,
                    'notification_enabled': True
                }
            },
            {
                'name': 'System Health Check',
                'task_name': 'perform_system_health_check',
                'description': 'Comprehensive system health monitoring and reporting',
                'schedule_type': 'EVERY_30_MINUTES',
                'is_active': True,
                'task_data': {
                    'task_type': 'system_monitoring',
                    'priority': 'LOW',
                    'max_execution_time': 120,
                    'health_thresholds': {
                        'cpu_threshold': 80,
                        'memory_threshold': 85,
                        'disk_threshold': 90
                    }
                }
            },
            {
                'name': 'Daily Processing Summary',
                'task_name': 'generate_daily_summary',
                'description': 'Generate daily summary of document and workflow processing',
                'schedule_type': 'DAILY',
                'schedule_time': '06:00',
                'is_active': True,
                'task_data': {
                    'task_type': 'reporting',
                    'priority': 'LOW',
                    'email_recipients': ['admin@edms.local'],
                    'include_metrics': True
                }
            },
            {
                'name': 'Weekly Workflow Report',
                'task_name': 'generate_weekly_report',
                'description': 'Generate weekly workflow performance and compliance report',
                'schedule_type': 'WEEKLY',
                'schedule_time': '20:00',
                'schedule_day': 0,  # Sunday
                'is_active': True,
                'task_data': {
                    'task_type': 'reporting',
                    'priority': 'LOW',
                    'email_recipients': ['admin@edms.local'],
                    'include_compliance_metrics': True,
                    'include_performance_analytics': True
                }
            }
        ]

        created_count = 0
        for task_config in scheduled_tasks:
            task, created = ScheduledTask.objects.get_or_create(
                task_name=task_config['task_name'],
                defaults={
                    'name': task_config['name'],
                    'description': task_config['description'],
                    'schedule_type': task_config['schedule_type'],
                    'schedule_time': task_config.get('schedule_time'),
                    'schedule_day': task_config.get('schedule_day'),
                    'is_active': task_config['is_active'],
                    'task_data': task_config['task_data'],
                    'created_by': system_user
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✅ Created scheduled task: {task.name}')
            else:
                self.stdout.write(f'ℹ️  Scheduled task already exists: {task.name}')

        # Summary
        self.stdout.write(f'\n📊 Scheduler Setup Summary:')
        self.stdout.write(f'   • Created {created_count} new scheduled tasks')
        self.stdout.write(f'   • Total active tasks: {ScheduledTask.objects.filter(is_active=True).count()}')
        
        # Validation
        self.stdout.write(f'\n🔍 Validating scheduler configuration...')
        self._validate_scheduler_setup()
        
        self.stdout.write(f'\n✅ EDMS Scheduler setup complete!')
        self.stdout.write(f'')
        self.stdout.write(f'🚦 Next Steps:')
        self.stdout.write(f'   1. Start Celery worker: celery -A edms worker -l info')
        self.stdout.write(f'   2. Start Celery Beat scheduler: celery -A edms beat -l info')
        self.stdout.write(f'   3. Monitor tasks in Django admin or Flower')
        
    def _get_or_create_system_user(self):
        """Get or create system user for scheduled tasks."""
        try:
            system_user, created = User.objects.get_or_create(
                username='system_scheduler',
                defaults={
                    'email': 'system@edms.local',
                    'first_name': 'System',
                    'last_name': 'Scheduler',
                    'is_active': True,
                    'is_staff': False,
                    'department': 'System',
                    'position': 'Automated Scheduler'
                }
            )
            
            if created:
                self.stdout.write('✅ Created system scheduler user')
            else:
                self.stdout.write('ℹ️  System scheduler user already exists')
                
            return system_user
            
        except Exception as e:
            self.stdout.write(f'❌ Error creating system user: {str(e)}')
            # Fallback to first superuser
            return User.objects.filter(is_superuser=True).first()
    
    def _validate_scheduler_setup(self):
        """Validate scheduler configuration."""
        try:
            # Check active tasks
            active_tasks = ScheduledTask.objects.filter(is_active=True)
            self.stdout.write(f'   ✅ {active_tasks.count()} active scheduled tasks')
            
            # Check task types
            task_types = active_tasks.values_list('task_data__task_type', flat=True)
            unique_types = set(task_types)
            self.stdout.write(f'   ✅ Task types: {", ".join(unique_types)}')
            
            # Check schedule types
            schedule_types = active_tasks.values_list('schedule_type', flat=True)
            unique_schedules = set(schedule_types)
            self.stdout.write(f'   ✅ Schedule types: {", ".join(unique_schedules)}')
            
            # Check system user
            system_users = User.objects.filter(username='system_scheduler')
            if system_users.exists():
                self.stdout.write('   ✅ System scheduler user configured')
            else:
                self.stdout.write('   ⚠️  System scheduler user missing')
                
            self.stdout.write('   ✅ Scheduler validation complete')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Validation error: {str(e)}')