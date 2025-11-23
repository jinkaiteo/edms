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

# S3 Scheduler Module - Celery Beat Schedule for automated tasks
app.conf.beat_schedule = {
    # S3 Document Effective Date Processing - runs every hour
    'process-document-effective-dates': {
        'task': 'apps.scheduler.automated_tasks.process_document_effective_dates',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 8,    # High priority
        }
    },
    
    # S3 Document Obsoletion Processing - runs every hour  
    'process-document-obsoletion-dates': {
        'task': 'apps.scheduler.automated_tasks.process_document_obsoletion_dates',
        'schedule': crontab(minute=15),  # Every hour at minute 15
        'options': {
            'expires': 3600,
            'priority': 8,
        }
    },
    
    # S3 Workflow Timeout Monitoring - runs every 4 hours
    'check-workflow-timeouts': {
        'task': 'apps.scheduler.automated_tasks.check_workflow_timeouts',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {
            'expires': 7200,  # Task expires after 2 hours
            'priority': 6,    # Medium priority
        }
    },
    
    # S3 System Health Check - runs every 30 minutes
    'perform-system-health-check': {
        'task': 'apps.scheduler.automated_tasks.perform_system_health_check',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {
            'expires': 1800,  # Task expires after 30 minutes
            'priority': 4,    # Low priority
        }
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