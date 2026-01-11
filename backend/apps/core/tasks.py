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
    Run the hybrid backup script.
    Creates backup using pg_dump + storage files.
    """
    script_path = Path(__file__).resolve().parent.parent.parent.parent / 'scripts' / 'backup-hybrid.sh'
    
    try:
        logger.info("Starting hybrid backup...")
        
        result = subprocess.run(
            ['/bin/bash', str(script_path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(script_path.parent.parent)
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
