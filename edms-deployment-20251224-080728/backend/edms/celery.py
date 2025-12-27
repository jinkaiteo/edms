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

# Explicitly import backup tasks to ensure they're registered
try:
    import apps.backup.tasks
except ImportError as e:
    import logging
    logging.error(f"Failed to import backup tasks: {e}")

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
    
    # S3 Notification Queue Processing - runs every 5 minutes
    'process-notification-queue': {
        'task': 'apps.scheduler.notification_service.process_notification_queue',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {
            'expires': 300,   # Task expires after 5 minutes
            'priority': 9,    # Highest priority
        }
    },
    
    # S3 Daily Summary Notifications - runs daily at 8 AM
    'send-daily-summary': {
        'task': 'apps.scheduler.notification_service.send_daily_summary_notifications',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 7,    # High priority
        }
    },
    
    # S3 Workflow Task Cleanup - runs every 6 hours
    'cleanup-workflow-tasks': {
        'task': 'apps.scheduler.automated_tasks.cleanup_workflow_tasks',
        'schedule': crontab(minute=0, hour='*/6'),  # 00:00, 06:00, 12:00, 18:00
        'kwargs': {'dry_run': False},
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 6,    # Medium priority
        }
    },
    
    # S3 Weekly Comprehensive Cleanup - runs Sundays at 2 AM
    'weekly-comprehensive-cleanup': {
        'task': 'apps.scheduler.automated_tasks.cleanup_workflow_tasks',
        'schedule': crontab(minute=0, hour=2, day_of_week=0),  # Sunday 02:00
        'kwargs': {'dry_run': False},
        'options': {
            'expires': 7200,  # Task expires after 2 hours
            'priority': 5,    # Lower priority for weekly maintenance
        }
    },
    
    # S4 Backup System - Daily Full Backup - runs daily at 2 AM
    'backup-daily-full': {
        'task': 'apps.backup.tasks.run_scheduled_backup',
        'schedule': crontab(minute=0, hour=2),  # Daily at 02:00
        'kwargs': {'backup_name': 'backup-daily-full'},
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 9,    # Highest priority - critical infrastructure
        }
    },
    
    # S4 Backup System - Weekly Export - runs Sundays at 3 AM
    'backup-weekly-export': {
        'task': 'apps.backup.tasks.run_scheduled_backup',
        'schedule': crontab(minute=0, hour=3, day_of_week=0),  # Sunday 03:00
        'kwargs': {'backup_name': 'backup-weekly-export'},
        'options': {
            'expires': 7200,  # Task expires after 2 hours
            'priority': 8,    # High priority
        }
    },
    
    # S4 Backup System - Monthly Archive - runs 1st of month at 4 AM
    'backup-monthly-archive': {
        'task': 'apps.backup.tasks.run_scheduled_backup',
        'schedule': crontab(minute=0, hour=4, day_of_month=1),  # 1st of month at 04:00
        'kwargs': {'backup_name': 'backup-monthly-archive'},
        'options': {
            'expires': 10800,  # Task expires after 3 hours
            'priority': 7,     # High priority
        }
    },
    
    # S4 Backup System - Cleanup Old Backups - runs daily at 5 AM
    'backup-cleanup': {
        'task': 'apps.backup.tasks.cleanup_old_backups',
        'schedule': crontab(minute=0, hour=5),  # Daily at 05:00
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 5,    # Medium priority
        }
    },
}

# Task routing configuration
app.conf.task_routes = {
    'apps.documents.tasks.*': {'queue': 'documents'},
    'apps.workflows.tasks.*': {'queue': 'workflows'},
    'apps.scheduler.automated_tasks.cleanup_workflow_tasks': {'queue': 'maintenance'},
    'apps.scheduler.automated_tasks.*': {'queue': 'scheduler'},
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