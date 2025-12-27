"""
Celery Configuration for EDMS Scheduler - Phase 3

This module configures Celery Beat for automated task scheduling including:
- Document effective date processing
- Document obsoletion processing  
- Workflow timeout monitoring
- System health checks
- Manual task triggering capabilities

Compliance: All automated actions create audit trails
"""

from celery.schedules import crontab
from django.conf import settings

# Celery Beat Schedule Configuration
CELERY_BEAT_SCHEDULE = {
    # Document effective date processing - runs every hour
    'process-effective-dates': {
        'task': 'apps.scheduler.automated_tasks.process_document_effective_dates',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {
            'expires': 3600,  # Task expires after 1 hour
            'priority': 8,    # High priority
        }
    },
    
    # Document obsoletion processing - runs every hour
    'process-obsoletion-dates': {
        'task': 'apps.scheduler.automated_tasks.process_document_obsoletion_dates', 
        'schedule': crontab(minute=15),  # Every hour at minute 15
        'options': {
            'expires': 3600,
            'priority': 8,
        }
    },
    
    # Workflow timeout monitoring - runs every 4 hours
    'check-workflow-timeouts': {
        'task': 'apps.scheduler.automated_tasks.check_workflow_timeouts',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {
            'expires': 7200,  # Task expires after 2 hours
            'priority': 6,    # Medium priority
        }
    },
    
    # System health check - runs every 30 minutes
    'system-health-check': {
        'task': 'apps.scheduler.automated_tasks.perform_system_health_check',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {
            'expires': 1800,  # Task expires after 30 minutes
            'priority': 4,    # Low priority
        }
    },
    
    # Daily document processing summary - runs at 6 AM daily
    'daily-processing-summary': {
        'task': 'apps.scheduler.automated_tasks.generate_daily_summary',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
        'options': {
            'expires': 3600,
            'priority': 3,
        }
    },
    
    # Weekly workflow performance report - runs Sunday at 8 PM
    'weekly-workflow-report': {
        'task': 'apps.scheduler.automated_tasks.generate_weekly_report',
        'schedule': crontab(hour=20, minute=0, day_of_week=0),  # Sunday 8 PM
        'options': {
            'expires': 7200,
            'priority': 2,
        }
    },
}

# Celery Task Routes - distribute tasks across queues
CELERY_TASK_ROUTES = {
    'apps.scheduler.automated_tasks.process_document_effective_dates': {
        'queue': 'document_processing',
        'routing_key': 'document.effective_dates',
    },
    'apps.scheduler.automated_tasks.process_document_obsoletion_dates': {
        'queue': 'document_processing', 
        'routing_key': 'document.obsoletion',
    },
    'apps.scheduler.automated_tasks.check_workflow_timeouts': {
        'queue': 'workflow_monitoring',
        'routing_key': 'workflow.timeouts',
    },
    'apps.scheduler.automated_tasks.perform_system_health_check': {
        'queue': 'system_monitoring',
        'routing_key': 'system.health',
    },
    'apps.scheduler.automated_tasks.*': {
        'queue': 'default',
        'routing_key': 'scheduler.default',
    },
}

# Task priority levels
CELERY_TASK_ANNOTATIONS = {
    'apps.scheduler.automated_tasks.process_document_effective_dates': {
        'rate_limit': '10/m',  # Max 10 per minute
        'time_limit': 300,     # 5 minute time limit
        'soft_time_limit': 240, # 4 minute soft limit
    },
    'apps.scheduler.automated_tasks.process_document_obsoletion_dates': {
        'rate_limit': '10/m',
        'time_limit': 300,
        'soft_time_limit': 240,
    },
    'apps.scheduler.automated_tasks.check_workflow_timeouts': {
        'rate_limit': '5/m',   # Max 5 per minute
        'time_limit': 600,     # 10 minute time limit
        'soft_time_limit': 540,
    },
    'apps.scheduler.automated_tasks.perform_system_health_check': {
        'rate_limit': '20/m',  # Max 20 per minute
        'time_limit': 120,     # 2 minute time limit
        'soft_time_limit': 100,
    },
}

# Queue configuration
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'document_processing': {
        'exchange': 'document_processing',
        'routing_key': 'document.*',
    },
    'workflow_monitoring': {
        'exchange': 'workflow_monitoring',
        'routing_key': 'workflow.*',
    },
    'system_monitoring': {
        'exchange': 'system_monitoring', 
        'routing_key': 'system.*',
    },
}

# Result backend configuration
CELERY_RESULT_BACKEND = getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour

# Task serialization
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Error handling
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Monitoring
CELERY_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# Security
CELERY_TASK_ALWAYS_EAGER = False  # Set to True for testing
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True