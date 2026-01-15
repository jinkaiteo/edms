"""
Celery Results Cleanup Service

Automatically cleans up old Celery task execution records.
"""

import logging
from datetime import timedelta
from typing import Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)

try:
    from django_celery_results.models import TaskResult
    CELERY_RESULTS_AVAILABLE = True
except ImportError:
    CELERY_RESULTS_AVAILABLE = False
    TaskResult = None


class CeleryResultsCleanupService:
    """Service for cleaning up old Celery task execution records"""
    
    def cleanup(self, days_to_keep: int = 7, remove_revoked: bool = True) -> Dict[str, Any]:
        """
        Clean up old task results from django_celery_results.
        
        Args:
            days_to_keep: Number of days of history to keep (default: 7)
            remove_revoked: Whether to remove all REVOKED tasks regardless of age (default: True)
        
        Returns:
            Dict with cleanup statistics
        """
        if not CELERY_RESULTS_AVAILABLE or not TaskResult:
            return {
                'success': False,
                'error': 'django-celery-results not available'
            }
        
        try:
            stats = {
                'success': True,
                'timestamp': timezone.now().isoformat(),
                'total_before': TaskResult.objects.count(),
                'deleted_old': 0,
                'deleted_revoked': 0,
                'total_deleted': 0,
                'total_after': 0
            }
            
            # 1. Delete old records (older than days_to_keep)
            cutoff_date = timezone.now() - timedelta(days=days_to_keep)
            old_results = TaskResult.objects.filter(date_done__lt=cutoff_date)
            old_count = old_results.count()
            
            if old_count > 0:
                old_results.delete()
                stats['deleted_old'] = old_count
                logger.info(f"Deleted {old_count} task results older than {days_to_keep} days")
            
            # 2. Delete REVOKED tasks (they're just noise in the logs)
            if remove_revoked:
                revoked_results = TaskResult.objects.filter(status='REVOKED')
                revoked_count = revoked_results.count()
                
                if revoked_count > 0:
                    revoked_results.delete()
                    stats['deleted_revoked'] = revoked_count
                    logger.info(f"Deleted {revoked_count} REVOKED task results")
            
            # 3. Calculate final statistics
            stats['total_deleted'] = stats['deleted_old'] + stats['deleted_revoked']
            stats['total_after'] = TaskResult.objects.count()
            
            logger.info(
                f"Celery results cleanup completed: "
                f"Deleted {stats['total_deleted']} records "
                f"({stats['total_before']} → {stats['total_after']})"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup Celery results: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
celery_cleanup_service = CeleryResultsCleanupService()
