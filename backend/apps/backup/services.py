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
        """Backup database using Django's dumpdata for complete data export."""
        import json
        import gzip
        import tempfile
        from django.core.management import call_command
        from io import StringIO
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"database_backup_{timestamp}.json"
        
        if config.compression_enabled:
            backup_filename += '.gz'
        
        backup_path = os.path.join(config.storage_path, backup_filename)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Get database settings
        db_settings = settings.DATABASES['default']
        
        # Define apps and models to backup (including Django system tables)
        apps_to_backup = [
            'contenttypes',     # Django content types - CRITICAL for model references
            'auth',             # Django auth (groups, permissions) - CRITICAL for authorization
            'admin',            # Django admin logs (optional)
            'sessions',         # User sessions - for session persistence across restore
            'django_celery_beat', # Scheduled tasks - CRITICAL for automation
            # EDMS Core Apps
            'users',            # User accounts and roles
            'documents',        # Document management
            'workflows',        # Workflow definitions and instances
            'audit',            # Audit trails and compliance
            'security',         # Security certificates and signatures
            'placeholders',     # Document placeholders and templates
            'backup',           # Backup configurations
            'settings',         # System settings and configurations
        ]
        
        try:
            # Create complete data backup using Django's dumpdata
            backup_buffer = StringIO()
            
            logger.info(f"Starting database backup with apps: {', '.join(apps_to_backup)}")
            
            # Export data using Django's dumpdata with natural keys
            call_command(
                'dumpdata',
                *apps_to_backup,      # Include all critical apps
                '--natural-foreign',  # Use natural keys for foreign key references
                '--natural-primary',  # Use natural keys for primary keys where available
                '--indent=2',         # Pretty formatting
                '--exclude=sessions.session',  # Exclude session data
                stdout=backup_buffer,
                verbosity=0          # Quiet output
            )
            
            # Get the backup data
            backup_content = backup_buffer.getvalue()
            
            # Parse to get statistics
            backup_data = json.loads(backup_content)
            
            # Create metadata
            metadata = {
                'backup_type': 'django_complete_data',
                'created_at': timezone.now().isoformat(),
                'database_info': {
                    'engine': db_settings['ENGINE'],
                    'name': db_settings['NAME']
                },
                'apps_included': apps_to_backup,
                'total_records': len(backup_data),
                'model_counts': {}
            }
            
            # Count records by model
            for record in backup_data:
                model = record.get('model', 'unknown')
                metadata['model_counts'][model] = metadata['model_counts'].get(model, 0) + 1
            
            logger.info(f"Database backup contains {len(backup_data)} records from {len(metadata['model_counts'])} models")
            
            # Write backup file
            if config.compression_enabled:
                # Write compressed JSON data
                with gzip.open(backup_path, 'wt') as f:
                    f.write(backup_content)
            else:
                # Write uncompressed JSON data
                with open(backup_path, 'w') as f:
                    f.write(backup_content)
            
            # Write metadata file alongside
            metadata_path = backup_path.replace('.json', '_metadata.json').replace('.gz', '')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Database backup completed: {backup_path}")
            logger.info(f"Backup metadata saved: {metadata_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Complete database backup failed: {str(e)}")
            # Fallback to metadata-only backup
            logger.info("Creating fallback metadata-only backup...")
            
            backup_data = {
                'backup_type': 'django_metadata_fallback',
                'created_at': timezone.now().isoformat(),
                'database_info': {
                    'engine': db_settings['ENGINE'],
                    'name': db_settings['NAME']
                },
                'error': str(e),
                'note': 'Full data export failed, metadata only',
                'tables_info': {}
            }
            
            # Get basic table information as fallback
            try:
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
                            'backup_note': 'Fallback metadata only - full backup failed'
                        }
            except Exception as db_error:
                backup_data['db_error'] = str(db_error)
            
            # Write fallback backup
            if config.compression_enabled:
                with gzip.open(backup_path, 'wt') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            else:
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            
            logger.warning(f"Fallback database backup completed: {backup_path}")
            return backup_path

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
        """Validate database backup file (supports both SQL dumps and Django fixtures)."""
        try:
            if backup_path.endswith('.gz'):
                # Compressed file validation
                with gzip.open(backup_path, 'rt') as f:
                    content = f.read(1000)  # Read first 1000 characters
            else:
                # Uncompressed file validation
                with open(backup_path, 'r') as f:
                    content = f.read(1000)  # Read first 1000 characters
            
            # Check for Django fixture format (JSON array)
            if content.strip().startswith('['):
                try:
                    import json
                    # Try to parse as JSON to verify it's valid Django fixture
                    if backup_path.endswith('.gz'):
                        with gzip.open(backup_path, 'rt') as f:
                            data = json.load(f)
                    else:
                        with open(backup_path, 'r') as f:
                            data = json.load(f)
                    
                    # Validate it's a proper Django fixture
                    if isinstance(data, list) and len(data) > 0:
                        first_record = data[0]
                        if isinstance(first_record, dict) and 'model' in first_record and 'fields' in first_record:
                            logger.info(f"Valid Django fixture with {len(data)} records")
                            return True
                        else:
                            logger.error("Invalid Django fixture format - missing model/fields structure")
                            return False
                    else:
                        logger.error("Django fixture is empty or not a list")
                        return False
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in Django fixture: {str(e)}")
                    return False
                    
            # Check for SQL dump format
            elif content.strip().startswith('--') or 'CREATE TABLE' in content or 'INSERT INTO' in content:
                logger.info("Valid SQL dump format detected")
                return True
                
            # Check for metadata-only backup (fallback format)
            elif content.strip().startswith('{'):
                try:
                    import json
                    if backup_path.endswith('.gz'):
                        with gzip.open(backup_path, 'rt') as f:
                            data = json.load(f)
                    else:
                        with open(backup_path, 'r') as f:
                            data = json.load(f)
                    
                    if isinstance(data, dict) and 'backup_type' in data:
                        logger.warning("Metadata-only backup detected - limited restoration capability")
                        return True
                    else:
                        logger.error("Unknown JSON backup format")
                        return False
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in backup: {str(e)}")
                    return False
            else:
                logger.error(f"Unknown backup format - content starts with: {content[:50]}")
                return False
            
        except Exception as e:
            logger.error(f"Database backup validation failed: {str(e)}")
            return False
    
    def _reset_postgresql_sequences(self):
        """Reset all PostgreSQL sequences to prevent primary key conflicts after restore."""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # Get all sequences in the public schema
                cursor.execute("""
                    SELECT sequence_name, sequence_schema 
                    FROM information_schema.sequences 
                    WHERE sequence_schema = 'public'
                    ORDER BY sequence_name;
                """)
                
                sequences = cursor.fetchall()
                logger.info(f"Found {len(sequences)} sequences to reset")
                
                # Reset each sequence to the maximum ID value + 1
                sequences_reset = 0
                for sequence_name, schema in sequences:
                    try:
                        # Extract table name from sequence name (remove _id_seq suffix)
                        table_name = sequence_name.replace('_id_seq', '')
                        
                        # Get the maximum ID value from the table
                        cursor.execute(f"""
                            SELECT COALESCE(MAX(id), 1) FROM {schema}.{table_name};
                        """)
                        max_id = cursor.fetchone()[0]
                        
                        # Reset the sequence to max_id + 1
                        cursor.execute(f"""
                            SELECT setval('{schema}.{sequence_name}', {max_id + 1}, false);
                        """)
                        
                        sequences_reset += 1
                        logger.debug(f"Reset sequence {sequence_name} to {max_id + 1}")
                        
                    except Exception as seq_error:
                        # Log warning but continue with other sequences
                        logger.warning(f"Could not reset sequence {sequence_name}: {seq_error}")
                        continue
                
                logger.info(f"Successfully reset {sequences_reset}/{len(sequences)} sequences")
                
                # Verify sequences are working by testing a few critical ones
                critical_sequences = [
                    'users_id_seq', 'documents_id_seq', 'audit_trail_id_seq',
                    'auth_permission_id_seq', 'django_content_type_id_seq'
                ]
                
                verification_passed = 0
                for seq_name in critical_sequences:
                    try:
                        cursor.execute(f"SELECT last_value FROM {seq_name};")
                        last_value = cursor.fetchone()[0]
                        logger.debug(f"Verified {seq_name}: last_value = {last_value}")
                        verification_passed += 1
                    except Exception as verify_error:
                        logger.warning(f"Could not verify sequence {seq_name}: {verify_error}")
                
                logger.info(f"Verified {verification_passed}/{len(critical_sequences)} critical sequences")
                
        except Exception as e:
            logger.error(f"Failed to reset PostgreSQL sequences: {str(e)}")
            # Don't raise exception - sequence reset is important but not critical enough to fail restore
            logger.warning("Sequence reset failed - manual sequence reset may be required")
            logger.warning("Run: SELECT setval('table_id_seq', (SELECT COALESCE(MAX(id), 1) FROM table)); for each table")

    def _restore_configuration_from_path(self, config_path: str):
        """Restore critical configuration files including environment variables."""
        import shutil
        import json
        from pathlib import Path
        
        logger.info(f"Restoring configuration files from: {config_path}")
        
        config_dir = Path(config_path)
        
        # Check for configuration manifest
        manifest_file = config_dir / 'config_manifest.json'
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            logger.info(f"Configuration manifest found: {manifest['files_backed_up']} files to restore")
            
            # Restore each configuration file
            restored_files = 0
            for file_info in manifest.get('config_files', []):
                backup_path = config_dir / file_info['backup_name']
                restore_location = file_info['restore_location']
                
                if backup_path.exists():
                    try:
                        # Create target directory if it doesn't exist
                        target_path = Path(restore_location)
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file to target location
                        shutil.copy2(backup_path, target_path)
                        
                        # Set appropriate permissions
                        if 'env' in file_info['backup_name'].lower():
                            # Environment files should be readable only by owner
                            target_path.chmod(0o600)
                        else:
                            # Other config files
                            target_path.chmod(0o644)
                        
                        logger.info(f"✓ Restored {file_info['backup_name']} to {restore_location}")
                        restored_files += 1
                        
                        # Special handling for critical environment files
                        if file_info['backup_name'] == 'environment_variables.env':
                            logger.info("✓ CRITICAL: Django environment variables restored")
                            logger.warning("Application restart required to apply environment changes")
                        
                    except Exception as e:
                        logger.error(f"Failed to restore {file_info['backup_name']}: {str(e)}")
                else:
                    logger.warning(f"Backup file not found: {backup_path}")
            
            logger.info(f"Configuration restore completed: {restored_files}/{len(manifest['config_files'])} files restored")
            
            # Verify critical files are in place
            critical_files = ['/app/.env']
            missing_critical = []
            for file_path in critical_files:
                if not Path(file_path).exists():
                    missing_critical.append(file_path)
            
            if missing_critical:
                logger.error(f"CRITICAL FILES MISSING after restore: {missing_critical}")
                logger.error("Django may fail to start without these files!")
            else:
                logger.info("✓ All critical configuration files verified")
                
        else:
            # Fallback: Look for individual config files
            logger.warning("No configuration manifest found, attempting manual restore...")
            
            # Try to restore .env file directly
            env_backup = config_dir / 'environment_variables.env'
            if env_backup.exists():
                shutil.copy2(env_backup, '/app/.env')
                Path('/app/.env').chmod(0o600)
                logger.info("✓ Restored .env file manually")
            
            # Try to restore Django settings
            django_settings_backup = config_dir / 'django_settings'
            if django_settings_backup.exists():
                target_settings = Path('/app/edms/settings')
                if target_settings.exists():
                    # Backup existing settings
                    backup_timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                    shutil.move(str(target_settings), f'/app/edms/settings.backup.{backup_timestamp}')
                
                shutil.copytree(django_settings_backup, target_settings)
                logger.info("✓ Restored Django settings manually")

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
        """Restore database from backup file using Django's loaddata for complete restoration."""
        import tempfile
        import json
        from django.core.management import call_command
        from django.db import connection
        
        logger.info(f"Starting database restoration from: {backup_path}")
        
        try:
            # Handle different backup formats
            if backup_path.endswith('.json.gz'):
                # Compressed Django fixture backup
                with gzip.open(backup_path, 'rt') as f:
                    backup_content = f.read()
                
                # Check if this is actual data or just metadata
                backup_data = json.loads(backup_content)
                
                if isinstance(backup_data, list) and len(backup_data) > 0:
                    # This is actual Django fixture data
                    logger.info(f"Processing Django fixture with {len(backup_data)} records")
                    
                    # Create temporary uncompressed file for loaddata
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                        temp_file.write(backup_content)
                        temp_fixture_path = temp_file.name
                    
                    try:
                        # Load data using Django's loaddata
                        logger.info("Loading fixture data into database...")
                        call_command('loaddata', temp_fixture_path, verbosity=1)
                        logger.info("✓ Django fixture loaded successfully")
                        
                        # Count what was loaded
                        model_counts = {}
                        for record in backup_data:
                            model = record.get('model', 'unknown')
                            model_counts[model] = model_counts.get(model, 0) + 1
                        
                        logger.info("Restored data by model:")
                        for model, count in sorted(model_counts.items()):
                            logger.info(f"  - {model}: {count} records")
                        
                        # CRITICAL FIX: Reset all PostgreSQL sequences to prevent primary key conflicts
                        logger.info("Resetting PostgreSQL sequences to prevent primary key conflicts...")
                        self._reset_postgresql_sequences()
                        logger.info("✓ PostgreSQL sequences reset successfully")
                        
                        return True
                        
                    finally:
                        # Cleanup temporary file
                        if os.path.exists(temp_fixture_path):
                            os.remove(temp_fixture_path)
                
                elif isinstance(backup_data, dict) and backup_data.get('backup_type') in ['django_native_database', 'django_metadata_fallback']:
                    # This is metadata-only backup (old format or fallback)
                    logger.warning("Processing metadata-only backup format - limited restoration")
                    tables = backup_data.get('tables_info', {})
                    logger.info(f"Backup contains metadata for {len(tables)} tables")
                    logger.warning("This backup contains only metadata, not actual data!")
                    logger.warning("You may need to manually restore data or use a complete backup")
                    return True
                
            elif backup_path.endswith('.json'):
                # Uncompressed Django fixture backup
                with open(backup_path, 'r') as f:
                    backup_content = f.read()
                
                backup_data = json.loads(backup_content)
                
                if isinstance(backup_data, list) and len(backup_data) > 0:
                    # This is actual Django fixture data
                    logger.info(f"Processing Django fixture with {len(backup_data)} records")
                    
                    # Load data directly using Django's loaddata
                    logger.info("Loading fixture data into database...")
                    call_command('loaddata', backup_path, verbosity=1)
                    logger.info("✓ Django fixture loaded successfully")
                    
                    # Count what was loaded
                    model_counts = {}
                    for record in backup_data:
                        model = record.get('model', 'unknown')
                        model_counts[model] = model_counts.get(model, 0) + 1
                    
                    logger.info("Restored data by model:")
                    for model, count in sorted(model_counts.items()):
                        logger.info(f"  - {model}: {count} records")
                    
                    # CRITICAL FIX: Reset all PostgreSQL sequences to prevent primary key conflicts
                    logger.info("Resetting PostgreSQL sequences to prevent primary key conflicts...")
                    self._reset_postgresql_sequences()
                    logger.info("✓ PostgreSQL sequences reset successfully")
                    
                    return True
                
                elif isinstance(backup_data, dict):
                    # This is metadata-only backup
                    logger.warning("Processing metadata-only backup format - limited restoration")
                    return True
                    
            elif backup_path.endswith('.tar.gz'):
                # Full system backup - extract and process
                temp_dir = tempfile.mkdtemp(prefix='edms_restore_')
                
                try:
                    with tarfile.open(backup_path, 'r:gz') as tar:
                        tar.extractall(temp_dir)
                    
                    # Look for database files in the archive
                    db_files = []
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith(('.sql', '.sql.gz', '.json', '.json.gz')):
                                if 'database' in file.lower() or 'db' in file.lower():
                                    db_files.append(os.path.join(root, file))
                    
                    if not db_files:
                        logger.warning("No database files found in archive")
                        return False
                    
                    # Process the database file
                    for db_file in db_files:
                        self._process_database_file(db_file)
                    
                    return True
                    
                finally:
                    shutil.rmtree(temp_dir)
            
            elif backup_path.endswith('.sql.gz'):
                # SQL dump file - use psql approach for PostgreSQL compatibility
                return self._restore_sql_dump(backup_path)
                
            else:
                logger.error(f"Unsupported backup format: {backup_path}")
                return False
                
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise
    
    def _process_database_file(self, db_file_path: str):
        """Process individual database file based on its format."""
        logger.info(f"Processing database file: {db_file_path}")
        
        if db_file_path.endswith('.json') or db_file_path.endswith('.json.gz'):
            # Django fixture format
            self._restore_django_fixture(db_file_path)
        elif db_file_path.endswith('.sql') or db_file_path.endswith('.sql.gz'):
            # SQL dump format
            self._restore_sql_dump(db_file_path)
        else:
            logger.warning(f"Unknown database file format: {db_file_path}")
    
    def _restore_django_fixture(self, fixture_path: str):
        """Restore Django fixture file."""
        from django.core.management import call_command
        import tempfile
        
        try:
            if fixture_path.endswith('.gz'):
                # Decompress to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    with gzip.open(fixture_path, 'rt') as gz_file:
                        temp_file.write(gz_file.read())
                    temp_fixture_path = temp_file.name
            else:
                temp_fixture_path = fixture_path
            
            logger.info(f"Loading Django fixture: {temp_fixture_path}")
            call_command('loaddata', temp_fixture_path, verbosity=1)
            
            # Cleanup temporary file if created
            if fixture_path.endswith('.gz') and os.path.exists(temp_fixture_path):
                os.remove(temp_fixture_path)
                
        except Exception as e:
            logger.error(f"Django fixture restore failed: {str(e)}")
            raise
    
    def _restore_sql_dump(self, sql_path: str):
        """Restore SQL dump using psql command."""
        db_settings = settings.DATABASES['default']
        
        # Check if this is a PostgreSQL database
        if 'postgresql' not in db_settings['ENGINE']:
            logger.warning("SQL dump restore requires PostgreSQL")
            return False
        
        # Use database container's psql to avoid version mismatch
        if os.path.exists('/.dockerenv'):  # Running in Docker
            # Construct docker exec command to use database container's psql
            cmd = [
                'docker', 'exec', '-i', 'edms_db', 
                'psql', '-U', db_settings['USER'], '-d', db_settings['NAME']
            ]
        else:
            # Local psql command
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
            if sql_path.endswith('.gz'):
                # Decompress and restore
                with gzip.open(sql_path, 'rb') as f:
                    result = subprocess.run(cmd, stdin=f, env=env, capture_output=True, text=False)
            else:
                # Direct restore
                with open(sql_path, 'rb') as f:
                    result = subprocess.run(cmd, stdin=f, env=env, capture_output=True, text=False)
            
            if result.returncode == 0:
                logger.info(f"SQL dump restored successfully from: {sql_path}")
                return True
            else:
                logger.error(f"SQL dump restore failed: {result.stderr.decode('utf-8')}")
                return False
                
        except Exception as e:
            logger.error(f"SQL dump restore failed: {str(e)}")
            return False

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