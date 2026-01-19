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

# Old backup module removed - using hybrid backup system via apps.core.tasks
# Backup tasks are now in apps.core.tasks.run_hybrid_backup (scheduled below)

# S3 Scheduler Module - Celery Beat Schedule for automated tasks
app.conf.beat_schedule = {
    # S3 Document Effective Date Processing - runs every hour
    'process-document-effective-dates': {
        'task': 'apps.scheduler.tasks.process_document_effective_dates',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 8,    # High priority
        }
    },
    
    # S3 Document Obsoletion Processing - runs every hour  
    'process-document-obsoletion-dates': {
        'task': 'apps.scheduler.tasks.process_document_obsoletion_dates',
        'schedule': crontab(minute=15),  # Every hour at minute 15
        'options': {
            'expires': 3600,
            'priority': 8,
        }
    },
    
    # S3 Workflow Timeout Monitoring - runs every 4 hours
    'check-workflow-timeouts': {
        'task': 'apps.scheduler.tasks.check_workflow_timeouts',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {
            'expires': 7200,  # Task expires after 2 hours
            'priority': 6,    # Medium priority
        }
    },
    
    # S3 System Health Check - runs every 30 minutes
    'perform-system-health-check': {
        'task': 'apps.scheduler.tasks.perform_system_health_check',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {
            'expires': 1800,  # Task expires after 30 minutes
            'priority': 4,    # Low priority
        }
    },
    
    # Note: Notification tasks disabled - not yet implemented
    # These are placeholders that currently do nothing (process 0 notifications)
    # Uncomment when notification system is ready:
    #
    # 'process-notification-queue': {
    #     'task': 'apps.scheduler.notification_service.process_notification_queue',
    #     'schedule': crontab(minute='*/5'),
    # },
    # 'send-daily-summary': {
    #     'task': 'apps.scheduler.notification_service.send_daily_summary_notifications',
    #     'schedule': crontab(hour=8, minute=0),
    # },
    
    # Note: Workflow cleanup tasks removed - WorkflowTask model no longer exists
    # The cleanup_workflow_tasks function is now a no-op since WorkflowTask was
    # replaced with document-filtering approach. No cleanup needed.
    
    # S4 Celery Results Cleanup - runs daily at 3 AM
    'cleanup-celery-results': {
        'task': 'apps.scheduler.celery_cleanup.cleanup_celery_results',
        'schedule': crontab(minute=0, hour=3),  # Daily at 03:00
        'kwargs': {'days_to_keep': 7, 'remove_revoked': True},
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 5,    # Low priority maintenance
        }
    },
    
    # S2 Data Integrity Checks - runs daily at 2 AM
    'run-daily-integrity-check': {
        'task': 'apps.audit.integrity_tasks.run_daily_integrity_check',
        'schedule': crontab(minute=0, hour=2),  # Daily at 02:00
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 7,    # High priority compliance
        }
    },
    
    # S2 Audit Trail Checksum Verification - runs weekly on Sunday at 1 AM
    'verify-audit-trail-checksums': {
        'task': 'apps.audit.integrity_tasks.verify_audit_trail_checksums',
        'schedule': crontab(minute=0, hour=1, day_of_week=0),  # Weekly Sunday at 01:00
        'options': {
            'expires': 7200,  # Task expires after 2 hours
            'priority': 7,    # High priority compliance
        }
    },
    
    # Note: Backup tasks removed - handled by host-level cron jobs
    # See: crontab -l for active backup schedule (daily, weekly, monthly)
}

# Task routing configuration
app.conf.task_routes = {
    'apps.documents.tasks.*': {'queue': 'documents'},
    'apps.workflows.tasks.*': {'queue': 'workflows'},
    'apps.scheduler.tasks.cleanup_workflow_tasks': {'queue': 'maintenance'},
    'apps.scheduler.tasks.*': {'queue': 'scheduler'},
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