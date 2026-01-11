"""
Core Celery tasks including hybrid backup.
"""
from celery import shared_task
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@shared_task(name='apps.core.tasks.run_hybrid_backup')
def run_hybrid_backup():
    """
    Run the hybrid backup script from host system.
    Creates backup using pg_dump + storage files.
    
    Note: Script must be run from host, not from within container,
    as it needs docker-compose access to execute commands in containers.
    """
    # Script is at /home/user/project/scripts/backup-hybrid.sh on host
    # From container perspective, we need to trigger it via docker exec or external call
    
    try:
        logger.info("Starting hybrid backup...")
        logger.warning("Hybrid backup must be run from host system using: ./scripts/backup-hybrid.sh")
        logger.warning("Celery-triggered backups require host-level docker access")
        
        # Return instruction for now - full automation requires host-level cron or orchestration
        return {
            'success': False,
            'error': 'Backup must be run from host system with docker-compose access',
            'instruction': 'Run: ./scripts/backup-hybrid.sh from project root'
        }
        
        # Alternative: Use docker socket mounting or host command execution
        # For production, recommend: cron job on host or external orchestration tool
        
        # Placeholder for future implementation:
        result = subprocess.run(
            ['/bin/bash', '/app/../scripts/backup-hybrid.sh'],
            capture_output=True,
            text=True,
            check=True,
            cwd='/app/..'
        )
        
        logger.info(f"Backup completed successfully")
        logger.info(result.stdout)
        
        return {
            'success': True,
            'output': result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e.stderr}")
        return {
            'success': False,
            'error': e.stderr,
            'output': e.stdout
        }
    except Exception as e:
        logger.error(f"Backup failed with exception: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
