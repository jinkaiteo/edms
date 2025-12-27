"""
Celery Tasks for Backup System

These tasks are executed by Celery Beat on a schedule to automate backups.
"""

from celery import shared_task
from django.utils import timezone
import logging
import os

logger = logging.getLogger(__name__)


@shared_task(name='apps.backup.tasks.run_scheduled_backup', bind=True)
def run_scheduled_backup(self, backup_name=None):
    """
    Generic scheduled backup task that determines which backup to run
    based on the task name or backup_name parameter
    
    This single task handles all scheduled backups (daily, weekly, monthly)
    """
    from .services import BackupService
    from .models import BackupConfiguration
    
    # Determine which backup to run based on periodic task name
    task_name = self.request.id if hasattr(self, 'request') else 'unknown'
    
    logger.info(f"Starting scheduled backup: {backup_name or task_name}")
    
    try:
        # Map task names to configuration names
        config_mapping = {
            'backup-daily-full': 'daily_full_backup',
            'backup-weekly-export': 'production_weekly_export',
            'backup-monthly-archive': 'production_monthly_archive',
        }
        
        # Determine which configuration to use
        if backup_name and backup_name in config_mapping:
            config_name = config_mapping[backup_name]
        else:
            # Default to daily if not specified
            config_name = 'daily_full_backup'
        
        # Get the backup configuration
        config = BackupConfiguration.objects.filter(
            name=config_name,
            is_enabled=True
        ).first()
        
        if not config:
            # Try alternative configuration names
            alt_configs = BackupConfiguration.objects.filter(
                is_enabled=True,
                frequency='DAILY'
            ).first()
            
            if alt_configs:
                config = alt_configs
            else:
                logger.warning(f"No enabled backup configuration found for {config_name}")
                return {
                    'status': 'skipped',
                    'reason': f'Configuration {config_name} not found or disabled'
                }
        
        # Determine backup type from configuration
        backup_type = config.backup_type
        
        # Execute backup using the service
        service = BackupService()
        result = service.execute_backup(
            configuration=config,
            triggered_by=None  # System initiated
        )
        
        logger.info(f"Scheduled backup completed successfully: {result.job_name}")
        
        return {
            'status': 'success',
            'job_name': result.job_name,
            'backup_size': result.backup_size,
            'configuration': config.name,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name='apps.backup.tasks.cleanup_old_backups')
def cleanup_old_backups():
    """
    Clean up old backups based on retention policy
    Scheduled to run daily at 5:00 AM
    """
    from .models import BackupJob, BackupConfiguration
    from datetime import timedelta
    
    logger.info("Starting scheduled backup cleanup")
    
    try:
        total_deleted = 0
        total_space_freed = 0
        
        # Get all configurations with retention settings
        configs = BackupConfiguration.objects.filter(
            is_enabled=True,
            retention_days__gt=0
        )
        
        for config in configs:
            cutoff_date = timezone.now() - timedelta(days=config.retention_days)
            
            # Find old backups for this configuration
            old_backups = BackupJob.objects.filter(
                configuration=config,
                created_at__lt=cutoff_date,
                status='COMPLETED'
            )
            
            for backup in old_backups:
                # Delete backup files
                if backup.file_path and os.path.exists(backup.file_path):
                    try:
                        file_size = os.path.getsize(backup.file_path)
                        os.remove(backup.file_path)
                        total_space_freed += file_size
                        total_deleted += 1
                        logger.info(f"Deleted old backup: {backup.job_name}")
                    except Exception as e:
                        logger.error(f"Failed to delete backup file {backup.file_path}: {e}")
                
                # Delete database record
                backup.delete()
        
        logger.info(f"Backup cleanup completed: {total_deleted} backups deleted, "
                   f"{total_space_freed / 1024 / 1024:.2f} MB freed")
        
        return {
            'status': 'success',
            'backups_deleted': total_deleted,
            'space_freed_mb': total_space_freed / 1024 / 1024,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }
