"""
Celery configuration for EDMS project.

This module configures Celery for background task processing,
including document processing, workflow automation, and scheduled tasks.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')

app = Celery('edms')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Check for documents to make effective daily at 1 AM
    'check-effective-documents': {
        'task': 'apps.workflows.tasks.check_effective_documents',
        'schedule': crontab(hour=1, minute=0),
    },
    
    # Process scheduled obsolescence daily at 1:30 AM
    'process-document-obsolescence': {
        'task': 'apps.workflows.tasks.process_document_obsolescence',
        'schedule': crontab(hour=1, minute=30),
    },
    
    # Clean up expired audit logs weekly on Sunday at 2 AM
    'cleanup-audit-logs': {
        'task': 'apps.audit.tasks.cleanup_expired_audit_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
    
    # Database backup daily at 3 AM
    'database-backup': {
        'task': 'apps.backup.tasks.create_database_backup',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # Health check every 5 minutes
    'system-health-check': {
        'task': 'apps.backup.tasks.system_health_check',
        'schedule': crontab(minute='*/5'),
    },
    
    # Send workflow notifications every 30 minutes during business hours
    'send-workflow-notifications': {
        'task': 'apps.workflows.tasks.send_pending_notifications',
        'schedule': crontab(minute='*/30', hour='8-18', day_of_week='1-5'),
    },
    
    # Clean up temporary files daily at 4 AM
    'cleanup-temporary-files': {
        'task': 'apps.documents.tasks.cleanup_temporary_files',
        'schedule': crontab(hour=4, minute=0),
    },
}

# Task routing configuration
app.conf.task_routes = {
    'apps.documents.tasks.*': {'queue': 'documents'},
    'apps.workflows.tasks.*': {'queue': 'workflows'},
    'apps.backup.tasks.*': {'queue': 'maintenance'},
    'apps.audit.tasks.*': {'queue': 'maintenance'},
}

# Task configuration
app.conf.update(
    # Task serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Results backend
    result_expires=3600,  # 1 hour
    
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')