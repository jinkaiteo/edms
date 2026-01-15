"""
Scheduler Tasks - Thin @shared_task Wrappers

This module contains all Celery task definitions for the scheduler.
Tasks are automatically discovered by Celery's autodiscover_tasks().

All business logic is delegated to service classes in services/
"""

from celery import shared_task
from celery.utils.log import get_task_logger

from .services.automation import document_automation_service
from .services.health import system_health_service
from .services.cleanup import celery_cleanup_service

logger = get_task_logger(__name__)


# ============================================================================
# Document Lifecycle Tasks
# ============================================================================

@shared_task(bind=True, max_retries=3)
def process_document_effective_dates(self):
    """
    Process documents with effective dates that have passed.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every hour via Celery Beat.
    """
    try:
        results = document_automation_service.process_effective_dates()
        logger.info(f"Processed {results['success_count']} effective dates successfully")
        return results
    except Exception as e:
        logger.error(f"Effective date processing task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


@shared_task(bind=True, max_retries=3)
def process_document_obsoletion_dates(self):
    """
    Process documents with obsoletion dates that have passed.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every hour via Celery Beat.
    """
    try:
        results = document_automation_service.process_obsoletion_dates()
        logger.info(f"Processed {results['success_count']} obsoletion dates successfully")
        return results
    except Exception as e:
        logger.error(f"Obsoletion processing task failed: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


# ============================================================================
# Workflow Monitoring Tasks
# ============================================================================

@shared_task
def check_workflow_timeouts():
    """
    Check for workflow timeouts and send escalation notifications.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every 4 hours via Celery Beat.
    """
    try:
        results = document_automation_service.check_workflow_timeouts()
        logger.info(f"Checked {results['checked_count']} workflows, found {results['timeout_count']} timeouts")
        return results
    except Exception as e:
        logger.error(f"Workflow timeout check failed: {str(e)}")
        raise


@shared_task
def cleanup_workflow_tasks(dry_run: bool = False):
    """
    Clean up orphaned and irrelevant workflow tasks.
    
    Note: This is now a no-op since WorkflowTask model was removed.
    Kept for backward compatibility with scheduled jobs.
    
    Celery task wrapper that delegates to DocumentAutomationService.
    Runs every 6 hours via Celery Beat.
    """
    try:
        results = document_automation_service.cleanup_workflow_tasks(dry_run=dry_run)
        logger.info("Workflow task cleanup completed (no-op)")
        return results
    except Exception as e:
        logger.error(f"Workflow task cleanup failed: {str(e)}")
        raise


# ============================================================================
# System Maintenance Tasks
# ============================================================================

@shared_task
def perform_system_health_check():
    """
    Perform comprehensive system health check.
    
    Celery task wrapper that delegates to SystemHealthService.
    Runs every 30 minutes via Celery Beat.
    """
    try:
        results = system_health_service.perform_health_check()
        logger.info(f"System health check completed: {results['overall_status']}")
        return results
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise


@shared_task(name='apps.scheduler.celery_cleanup.cleanup_celery_results')
def cleanup_celery_results(days_to_keep: int = 7, remove_revoked: bool = True):
    """
    Clean up old Celery task execution records.
    
    Celery task wrapper that delegates to CeleryResultsCleanupService.
    Runs daily at 03:00 via Celery Beat.
    
    Args:
        days_to_keep: Number of days of history to keep (default: 7)
        remove_revoked: Whether to remove all REVOKED tasks (default: True)
    """
    try:
        results = celery_cleanup_service.cleanup(days_to_keep, remove_revoked)
        
        if results['success']:
            logger.info(
                f"Celery results cleanup completed: "
                f"Deleted {results['total_deleted']} records "
                f"({results['total_before']} → {results['total_after']})"
            )
        else:
            logger.error(f"Celery results cleanup failed: {results.get('error')}")
        
        return results
    except Exception as e:
        logger.error(f"Celery results cleanup task failed: {str(e)}")
        raise


# ============================================================================
# Backward Compatibility Exports
# ============================================================================
# These are imported by monitoring_dashboard.py for manual triggering

__all__ = [
    'process_document_effective_dates',
    'process_document_obsoletion_dates',
    'check_workflow_timeouts',
    'perform_system_health_check',
    'cleanup_workflow_tasks',
    'cleanup_celery_results',
]
