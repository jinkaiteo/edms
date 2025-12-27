"""
Celery Beat Schedule Configuration for Automated Tasks

This module defines the scheduled execution of automated maintenance tasks
including workflow cleanup, document lifecycle management, and system health checks.
"""

from celery.schedules import crontab
from django.conf import settings

# Default schedule configuration
CELERY_BEAT_SCHEDULE = {
    # Workflow task cleanup - Run every 6 hours
    'cleanup-workflow-tasks': {
        'task': 'apps.scheduler.automated_tasks.cleanup_workflow_tasks',
        'schedule': crontab(minute=0, hour='*/6'),  # 00:00, 06:00, 12:00, 18:00
        'kwargs': {'dry_run': False},
        'options': {
            'description': 'Clean up orphaned, irrelevant, and expired workflow tasks',
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
    
    # Document effective date processing - Run every hour
    'process-document-effective-dates': {
        'task': 'apps.scheduler.automated_tasks.process_document_effective_dates',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {
            'description': 'Process pending document effective dates and activate documents',
            'expires': 1800,  # Task expires after 30 minutes
        }
    },
    
    # Document obsoletion processing - Run daily at 1 AM
    'process-document-obsoletion-dates': {
        'task': 'apps.scheduler.automated_tasks.process_document_obsoletion_dates',
        'schedule': crontab(minute=0, hour=1),  # 01:00 daily
        'options': {
            'description': 'Process document obsoletion dates and mark documents obsolete',
            'expires': 3600,
        }
    },
    
    # Workflow timeout monitoring - Run every 4 hours
    'check-workflow-timeouts': {
        'task': 'apps.scheduler.automated_tasks.check_workflow_timeouts',
        'schedule': crontab(minute=30, hour='*/4'),  # 00:30, 04:30, 08:30, 12:30, 16:30, 20:30
        'options': {
            'description': 'Monitor workflow timeouts and send escalation notifications',
            'expires': 7200,  # 2 hours
        }
    },
    
    # System health monitoring - Run every 2 hours
    'system-health-check': {
        'task': 'apps.scheduler.automated_tasks.perform_system_health_check',
        'schedule': crontab(minute=15, hour='*/2'),  # XX:15 every 2 hours
        'options': {
            'description': 'Perform comprehensive system health monitoring',
            'expires': 3600,
        }
    },
    
    # Weekly comprehensive cleanup - Run Sundays at 2 AM
    'weekly-comprehensive-cleanup': {
        'task': 'apps.scheduler.automated_tasks.cleanup_workflow_tasks',
        'schedule': crontab(minute=0, hour=2, day_of_week=0),  # Sunday 02:00
        'kwargs': {'dry_run': False},
        'options': {
            'description': 'Weekly comprehensive workflow task cleanup and maintenance',
            'expires': 7200,
        }
    },
}

# Allow override from Django settings
if hasattr(settings, 'EDMS_CELERY_BEAT_SCHEDULE'):
    CELERY_BEAT_SCHEDULE.update(settings.EDMS_CELERY_BEAT_SCHEDULE)

# Timezone configuration
CELERY_TIMEZONE = getattr(settings, 'TIME_ZONE', 'UTC')

# Beat scheduler configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Enable UTC for consistent scheduling across timezones
CELERY_ENABLE_UTC = True