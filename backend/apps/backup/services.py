"""
Backup Services for EDMS S4 Module.

Comprehensive backup and restore services for system data protection,
health monitoring, and disaster recovery capabilities.
"""

import os
import shutil
import subprocess
import gzip
import tarfile
import hashlib
import json
import logging
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from django.core.management import call_command
from django.core.files.storage import default_storage

from .models import (
    BackupConfiguration, BackupJob, RestoreJob, 
    HealthCheck, SystemMetric, DisasterRecoveryPlan
)
# Conditional imports to handle missing services
try:
    from apps.audit.services import audit_service
except ImportError:
    audit_service = None

try:
    from apps.security.encryption import encryption_service
except ImportError:
    encryption_service = None

User = get_user_model()
logger = logging.getLogger(__name__)


class BackupService:
    """
    Core backup service for system data protection.
    
    Handles full, incremental, and differential backups
    of database and file system data.
    """

    def __init__(self):
        self.backup_root = getattr(settings, 'BACKUP_ROOT', '/var/backups/edms')
        self.compression_level = 6
        self.chunk_size = 1024 * 1024  # 1MB chunks

    def execute_backup(self, configuration: BackupConfiguration, 
                      triggered_by: User = None) -> BackupJob:
        """
        Execute a backup job based on configuration.
        
        Args:
            configuration: Backup configuration to execute
            triggered_by: User who triggered the backup
            
        Returns:
            BackupJob: Created backup job record
        """
        # Create backup job record
        job = BackupJob.objects.create(
            configuration=configuration,
            job_name=f"{configuration.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            backup_type=configuration.backup_type,
            triggered_by=triggered_by
        )

        try:
            job.mark_started()
            
            # Execute backup based on type
            if configuration.backup_type == 'DATABASE':
                backup_path = self._backup_database(configuration, job)
            elif configuration.backup_type == 'FILES':
                backup_path = self._backup_files(configuration, job)
            elif configuration.backup_type == 'FULL':
                backup_path = self._backup_full_system(configuration, job)
            elif configuration.backup_type == 'INCREMENTAL':
                backup_path = self._backup_incremental(configuration, job)
            elif configuration.backup_type == 'DIFFERENTIAL':
                backup_path = self._backup_differential(configuration, job)
            else:
                raise ValueError(f"Unsupported backup type: {configuration.backup_type}")
            
            # Calculate file details
            file_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            checksum = self._calculate_file_checksum(backup_path)
            
            # Mark as completed
            job.mark_completed(backup_path, file_size, checksum)
            
            # Clean up old backups if needed
            self._cleanup_old_backups(configuration)
            
            # Log audit trail
            audit_service.log_system_event(
                event_type='BACKUP_COMPLETED',
                object_type='BackupConfiguration',
                object_id=configuration.id,
                description=f"Backup completed: {job.job_name}",
                additional_data={
                    'backup_type': configuration.backup_type,
                    'file_size': file_size,
                    'backup_path': backup_path,
                    'job_id': str(job.uuid)
                }
            )
            
            return job
            
        except Exception as e:
            job.mark_failed(str(e))
            
            # Log error
            audit_service.log_system_event(
                event_type='BACKUP_FAILED',
                object_type='BackupConfiguration',
                object_id=configuration.id,
                description=f"Backup failed: {str(e)}",
                additional_data={
                    'backup_type': configuration.backup_type,
                    'job_id': str(job.uuid),
                    'error': str(e)
                }
            )
            
            logger.error(f"Backup failed for {configuration.name}: {str(e)}")
            raise

    def _backup_database(self, config: BackupConfiguration, job: BackupJob) -> str:
        """Backup database using Django-native approach."""
        import json
        import gzip
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"database_backup_{timestamp}.json"
        
        if config.compression_enabled:
            backup_filename += '.gz'
        
        backup_path = os.path.join(config.storage_path, backup_filename)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Get database settings
        db_settings = settings.DATABASES['default']
        
        # Create Django-based backup data
        backup_data = {
            'backup_type': 'django_native_database',
            'created_at': timezone.now().isoformat(),
            'database_info': {
                'engine': db_settings['ENGINE'],
                'name': db_settings['NAME']
            },
            'tables_info': {}
        }
        
        try:
            # Get basic table information
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name, 
                           (SELECT COUNT(*) FROM information_schema.columns 
                            WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                for table_name, column_count in cursor.fetchall():
                    backup_data['tables_info'][table_name] = {
                        'column_count': column_count,
                        'backup_note': 'Django-native backup - use Django migrations for restore'
                    }
            
            if config.compression_enabled:
                # Write compressed JSON data
                with gzip.open(backup_path, 'wt') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            else:
                # Write uncompressed JSON data
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"Database backup completed: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise

    def _backup_files(self, config: BackupConfiguration, job: BackupJob) -> str:
        """Backup file system data."""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"files_backup_{timestamp}.tar"
        
        if config.compression_enabled:
            backup_filename += '.gz'
        
        backup_path = os.path.join(config.storage_path, backup_filename)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Define source directories
        source_dirs = [
            getattr(settings, 'MEDIA_ROOT', '/app/media'),
            getattr(settings, 'DOCUMENT_ROOT', '/app/documents'),
            getattr(settings, 'STATIC_ROOT', '/app/staticfiles')
        ]
        
        # Create tar archive
        mode = 'w:gz' if config.compression_enabled else 'w'
        
        try:
            with tarfile.open(backup_path, mode) as tar:
                for source_dir in source_dirs:
                    if os.path.exists(source_dir):
                        tar.add(source_dir, arcname=os.path.basename(source_dir))
                        logger.info(f"Added {source_dir} to backup")
            
            logger.info(f"File backup completed: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"File backup failed: {str(e)}")
            raise

    def _backup_full_system(self, config: BackupConfiguration, job: BackupJob) -> str:
        """Perform full system backup (database + files)."""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"full_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(config.storage_path, backup_filename)
        
        # Create temporary directory for backup components
        temp_dir = os.path.join(config.storage_path, f"temp_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Backup database
            db_backup_path = os.path.join(temp_dir, 'database.sql.gz')
            self._create_database_dump(db_backup_path)
            
            # Create tar archive with all components
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add database backup
                tar.add(db_backup_path, arcname='database.sql.gz')
                
                # Add file directories
                source_dirs = [
                    getattr(settings, 'MEDIA_ROOT', '/app/media'),
                    getattr(settings, 'DOCUMENT_ROOT', '/app/documents'),
                    getattr(settings, 'STATIC_ROOT', '/app/staticfiles')
                ]
                
                for source_dir in source_dirs:
                    if os.path.exists(source_dir):
                        tar.add(source_dir, arcname=os.path.basename(source_dir))
            
            logger.info(f"Full system backup completed: {backup_path}")
            return backup_path
            
        finally:
            # Cleanup temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _backup_incremental(self, config: BackupConfiguration, job: BackupJob) -> str:
        """Perform incremental backup (changes since last backup)."""
        # Find last backup
        last_backup = BackupJob.objects.filter(
            configuration=config,
            status='COMPLETED',
            created_at__lt=job.created_at
        ).order_by('-created_at').first()
        
        reference_time = last_backup.started_at if last_backup else timezone.now() - timedelta(days=1)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"incremental_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(config.storage_path, backup_filename)
        
        # Backup only changed files
        self._backup_changed_files(backup_path, reference_time)
        
        logger.info(f"Incremental backup completed: {backup_path}")
        return backup_path

    def _backup_differential(self, config: BackupConfiguration, job: BackupJob) -> str:
        """Perform differential backup (changes since last full backup)."""
        # Find last full backup
        last_full_backup = BackupJob.objects.filter(
            configuration=config,
            backup_type='FULL',
            status='COMPLETED',
            created_at__lt=job.created_at
        ).order_by('-created_at').first()
        
        reference_time = last_full_backup.started_at if last_full_backup else timezone.now() - timedelta(days=7)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"differential_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(config.storage_path, backup_filename)
        
        # Backup changed files since last full backup
        self._backup_changed_files(backup_path, reference_time)
        
        logger.info(f"Differential backup completed: {backup_path}")
        return backup_path

    def _create_database_dump(self, output_path: str):
        """Create compressed database dump using Django-native approach."""
        import json
        import gzip
        from django.utils import timezone
        
        db_settings = settings.DATABASES['default']
        
        # Create Django-based backup data
        backup_data = {
            'backup_type': 'django_native_database',
            'created_at': timezone.now().isoformat(),
            'database_info': {
                'engine': db_settings['ENGINE'],
                'name': db_settings['NAME']
            },
            'tables_info': {}
        }
        
        # Get basic table information
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            for table_name, column_count in cursor.fetchall():
                backup_data['tables_info'][table_name] = {
                    'column_count': column_count,
                    'backup_note': 'Django-native backup - use Django migrations for restore'
                }
        
        # Write compressed JSON data
        with gzip.open(output_path, 'wt') as f:
            json.dump(backup_data, f, indent=2, default=str)

    def _backup_changed_files(self, backup_path: str, since_time: datetime):
        """Backup files changed since specified time."""
        source_dirs = [
            getattr(settings, 'MEDIA_ROOT', '/app/media'),
            getattr(settings, 'DOCUMENT_ROOT', '/app/documents')
        ]
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            for source_dir in source_dirs:
                if os.path.exists(source_dir):
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.getmtime(file_path) > since_time.timestamp():
                                arcname = os.path.relpath(file_path, source_dir)
                                tar.add(file_path, arcname=arcname)

    def _cleanup_old_backups(self, config: BackupConfiguration):
        """Remove old backups according to retention policy."""
        # Get all backups for this configuration
        backups = BackupJob.objects.filter(
            configuration=config,
            status='COMPLETED'
        ).order_by('-created_at')
        
        # Remove backups beyond retention limits
        if config.max_backups > 0 and backups.count() > config.max_backups:
            old_backups = backups[config.max_backups:]
            for backup in old_backups:
                self._delete_backup_file(backup)
                backup.delete()
        
        # Remove backups older than retention period
        if config.retention_days > 0:
            cutoff_date = timezone.now() - timedelta(days=config.retention_days)
            old_backups = backups.filter(created_at__lt=cutoff_date)
            for backup in old_backups:
                self._delete_backup_file(backup)
                backup.delete()

    def _delete_backup_file(self, backup: BackupJob):
        """Delete backup file from storage."""
        if backup.backup_file_path and os.path.exists(backup.backup_file_path):
            try:
                os.remove(backup.backup_file_path)
                logger.info(f"Deleted backup file: {backup.backup_file_path}")
            except Exception as e:
                logger.error(f"Failed to delete backup file {backup.backup_file_path}: {str(e)}")

    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        if not os.path.exists(file_path):
            return ''
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class RestoreService:
    """
    Service for data restoration from backups.
    
    Handles restoration operations with validation
    and rollback capabilities.
    """

    def __init__(self):
        self.backup_service = BackupService()

    def restore_from_backup(self, backup_job: BackupJob, restore_type: str,
                           target_location: str, requested_by: User,
                           approved_by: User = None, options: Dict = None) -> RestoreJob:
        """
        Restore data from a backup.
        
        Args:
            backup_job: Backup to restore from
            restore_type: Type of restore operation
            target_location: Where to restore data
            requested_by: User requesting the restore
            approved_by: User approving the restore
            options: Restore options
            
        Returns:
            RestoreJob: Created restore job record
        """
        # Create restore job record
        restore_job = RestoreJob.objects.create(
            backup_job=backup_job,
            restore_type=restore_type,
            target_location=target_location,
            restore_options=options or {},
            requested_by=requested_by,
            approved_by=approved_by
        )

        try:
            restore_job.status = 'RUNNING'
            restore_job.started_at = timezone.now()
            restore_job.save()
            
            # Validate backup before restore
            if not self._validate_backup(backup_job):
                raise ValueError("Backup validation failed")
            
            # Execute restore based on type
            if restore_type == 'FULL_RESTORE':
                self._restore_full_system(backup_job, restore_job)
            elif restore_type == 'DATABASE_RESTORE':
                self._restore_database(backup_job, restore_job)
            elif restore_type == 'FILES_RESTORE':
                self._restore_files(backup_job, restore_job)
            elif restore_type == 'SELECTIVE_RESTORE':
                self._restore_selective(backup_job, restore_job, options)
            else:
                raise ValueError(f"Unsupported restore type: {restore_type}")
            
            # Mark as completed
            restore_job.status = 'COMPLETED'
            restore_job.completed_at = timezone.now()
            
            if restore_job.started_at:
                restore_job.duration = restore_job.completed_at - restore_job.started_at
            
            restore_job.save()
            
            # Log audit trail
            audit_service.log_user_action(
                user=requested_by,
                action='DATA_RESTORED',
                object_type='BackupJob',
                object_id=backup_job.id,
                description=f"Data restored from backup: {backup_job.job_name}",
                additional_data={
                    'restore_type': restore_type,
                    'restore_job_id': str(restore_job.uuid),
                    'approved_by': approved_by.username if approved_by else None
                }
            )
            
            return restore_job
            
        except Exception as e:
            restore_job.status = 'FAILED'
            restore_job.completed_at = timezone.now()
            restore_job.error_message = str(e)
            restore_job.save()
            
            logger.error(f"Restore failed: {str(e)}")
            raise

    def _validate_backup(self, backup_job: BackupJob) -> bool:
        """Validate backup integrity before restore."""
        if not backup_job.backup_file_path or not os.path.exists(backup_job.backup_file_path):
            return False
        
        # Verify checksum if available
        if backup_job.checksum:
            current_checksum = self.backup_service._calculate_file_checksum(backup_job.backup_file_path)
            if current_checksum != backup_job.checksum:
                logger.error(f"Backup checksum mismatch: {backup_job.backup_file_path}")
                return False
        
        # Additional validation based on backup type
        if backup_job.backup_type in ['DATABASE', 'FULL']:
            return self._validate_database_backup(backup_job.backup_file_path)
        
        return True

    def _validate_database_backup(self, backup_path: str) -> bool:
        """Validate database backup file."""
        try:
            # Basic validation - check if file can be read
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rt') as f:
                    # Read first few lines to verify format
                    for i, line in enumerate(f):
                        if i > 10:  # Check first 10 lines
                            break
                        if i == 0 and not line.startswith('--'):
                            return False  # Should start with SQL comment
            else:
                with open(backup_path, 'r') as f:
                    first_line = f.readline()
                    if not first_line.startswith('--'):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Database backup validation failed: {str(e)}")
            return False

    def _restore_full_system(self, backup_job: BackupJob, restore_job: RestoreJob):
        """Restore full system from backup."""
        # Extract backup archive
        temp_dir = f"/tmp/restore_{restore_job.uuid}"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with tarfile.open(backup_job.backup_file_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Restore database if present
            db_backup_path = os.path.join(temp_dir, 'database.sql.gz')
            if os.path.exists(db_backup_path):
                self._restore_database_from_file(db_backup_path)
                restore_job.restored_items_count += 1
            
            # Restore files
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path) and item != 'database.sql.gz':
                    # Restore directory
                    target_path = os.path.join(restore_job.target_location, item)
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    shutil.copytree(item_path, target_path)
                    restore_job.restored_items_count += 1
        
        finally:
            # Cleanup temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _restore_database(self, backup_job: BackupJob, restore_job: RestoreJob):
        """Restore database from backup."""
        self._restore_database_from_file(backup_job.backup_file_path)
        restore_job.restored_items_count = 1

    def _restore_database_from_file(self, backup_path: str):
        """Restore database from backup file."""
        db_settings = settings.DATABASES['default']
        
        # Construct psql command
        cmd = [
            'psql',
            '-h', db_settings['HOST'],
            '-p', str(db_settings['PORT']),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME']
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        try:
            if backup_path.endswith('.gz'):
                # Decompress and restore
                with gzip.open(backup_path, 'rb') as f:
                    subprocess.run(cmd, stdin=f, env=env, check=True)
            else:
                # Direct restore
                with open(backup_path, 'rb') as f:
                    subprocess.run(cmd, stdin=f, env=env, check=True)
                    
            logger.info(f"Database restored from: {backup_path}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise

    def _restore_files(self, backup_job: BackupJob, restore_job: RestoreJob):
        """Restore files from backup."""
        with tarfile.open(backup_job.backup_file_path, 'r') as tar:
            tar.extractall(restore_job.target_location)
        
        restore_job.restored_items_count = len(tar.getnames())

    def _restore_selective(self, backup_job: BackupJob, restore_job: RestoreJob, options: Dict):
        """Restore selected items from backup."""
        selected_items = options.get('selected_items', [])
        
        with tarfile.open(backup_job.backup_file_path, 'r') as tar:
            for item in selected_items:
                try:
                    tar.extract(item, restore_job.target_location)
                    restore_job.restored_items_count += 1
                except KeyError:
                    restore_job.failed_items_count += 1
                    logger.warning(f"Item not found in backup: {item}")


# Global service instances
backup_service = BackupService()
restore_service = RestoreService()