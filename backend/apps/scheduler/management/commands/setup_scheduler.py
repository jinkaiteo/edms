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
        
        # Define scheduled tasks matching actual model fields
        scheduled_tasks = [
            {
                'name': 'Document Effective Date Processing',
                'description': 'Automatically process documents that have reached their effective date',
                'task_type': 'DOCUMENT_EFFECTIVE',
                'task_module': 'apps.scheduler.automated_tasks',
                'task_function': 'process_document_effective_dates',
                'frequency_type': 'HOURLY',
                'status': 'ACTIVE',
                'timeout_seconds': 300,
                'max_retries': 3,
                'metadata': {
                    'priority': 'HIGH',
                    'description': 'Process documents that have reached effective date'
                }
            },
            {
                'name': 'Document Obsoletion Processing',
                'description': 'Automatically obsolete documents that have reached their obsoletion date',
                'task_type': 'DOCUMENT_OBSOLETE',
                'task_module': 'apps.scheduler.automated_tasks',
                'task_function': 'process_document_obsoletion_dates',
                'frequency_type': 'HOURLY',
                'status': 'ACTIVE',
                'timeout_seconds': 300,
                'max_retries': 3,
                'metadata': {
                    'priority': 'HIGH',
                    'description': 'Process documents for obsoletion'
                }
            },
            {
                'name': 'Workflow Timeout Monitoring',
                'description': 'Monitor workflows for timeouts and send notifications',
                'task_type': 'WORKFLOW_TIMEOUT',
                'task_module': 'apps.scheduler.automated_tasks',
                'task_function': 'check_workflow_timeouts',
                'frequency_type': 'HOURLY',
                'interval_value': 4,
                'status': 'ACTIVE',
                'timeout_seconds': 600,
                'max_retries': 2,
                'metadata': {
                    'priority': 'MEDIUM',
                    'notification_enabled': True
                }
            },
            {
                'name': 'System Health Check',
                'description': 'Comprehensive system health monitoring and reporting',
                'task_type': 'HEALTH_CHECK',
                'task_module': 'apps.scheduler.automated_tasks',
                'task_function': 'perform_system_health_check',
                'frequency_type': 'HOURLY',
                'interval_value': 1,
                'status': 'ACTIVE',
                'timeout_seconds': 120,
                'max_retries': 1,
                'metadata': {
                    'priority': 'LOW',
                    'health_thresholds': {
                        'cpu_threshold': 80,
                        'memory_threshold': 85,
                        'disk_threshold': 90
                    }
                }
            }
        ]

        created_count = 0
        for task_config in scheduled_tasks:
            task, created = ScheduledTask.objects.get_or_create(
                name=task_config['name'],
                defaults={
                    'description': task_config['description'],
                    'task_type': task_config['task_type'],
                    'task_module': task_config['task_module'],
                    'task_function': task_config['task_function'],
                    'frequency_type': task_config['frequency_type'],
                    'interval_value': task_config.get('interval_value', 1),
                    'status': task_config['status'],
                    'timeout_seconds': task_config['timeout_seconds'],
                    'max_retries': task_config['max_retries'],
                    'metadata': task_config['metadata'],
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
        self.stdout.write(f'   • Total active tasks: {ScheduledTask.objects.filter(status="ACTIVE").count()}')
        
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
            active_tasks = ScheduledTask.objects.filter(status='ACTIVE')
            self.stdout.write(f'   ✅ {active_tasks.count()} active scheduled tasks')
            
            # Check task types
            task_types = active_tasks.values_list('task_type', flat=True)
            unique_types = set(task_types)
            self.stdout.write(f'   ✅ Task types: {", ".join(unique_types)}')
            
            # Check frequency types
            frequency_types = active_tasks.values_list('frequency_type', flat=True)
            unique_frequencies = set(frequency_types)
            self.stdout.write(f'   ✅ Frequency types: {", ".join(unique_frequencies)}')
            
            # Check system user
            system_users = User.objects.filter(username='system_scheduler')
            if system_users.exists():
                self.stdout.write('   ✅ System scheduler user configured')
            else:
                self.stdout.write('   ⚠️  System scheduler user missing')
                
            self.stdout.write('   ✅ Scheduler validation complete')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Validation error: {str(e)}')