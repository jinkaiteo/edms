"""
Management command to restore system from backups.

Usage:
    python manage.py restore_backup --package /path/to/migration_package.tar.gz
    python manage.py restore_backup --backup-job 12345 --type database
    python manage.py restore_backup --from-file /path/to/backup.tar.gz --target /restore/location
"""

import os
import json
import tarfile
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.utils import timezone

from apps.backup.models import BackupJob, RestoreJob
from apps.backup.services import restore_service
from apps.audit.services import audit_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Restore system from backups or migration packages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--package',
            type=str,
            help='Path to migration package (.tar.gz file)'
        )
        parser.add_argument(
            '--backup-job',
            type=str,
            help='UUID of backup job to restore from'
        )
        parser.add_argument(
            '--from-file',
            type=str,
            help='Path to backup file to restore from'
        )
        parser.add_argument(
            '--type',
            choices=['full', 'database', 'files', 'selective'],
            default='full',
            help='Type of restore operation'
        )
        parser.add_argument(
            '--target',
            type=str,
            default='/tmp/edms_restore',
            help='Target location for file restoration'
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Skip user account restoration'
        )
        parser.add_argument(
            '--skip-database',
            action='store_true',
            help='Skip database restoration'
        )
        parser.add_argument(
            '--skip-files',
            action='store_true',
            help='Skip file restoration'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            default=True,
            help='Verify restoration integrity'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually doing it'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restoration without confirmation prompts'
        )

    def handle(self, *args, **options):
        try:
            if options['package']:
                # Restore from migration package
                self.restore_from_package(options)
            elif options['backup_job']:
                # Restore from existing backup job
                self.restore_from_backup_job(options)
            elif options['from_file']:
                # Restore from backup file
                self.restore_from_file(options)
            else:
                raise CommandError(
                    "Must specify --package, --backup-job, or --from-file"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Restoration failed: {str(e)}')
            )
            raise CommandError(f'Restoration operation failed: {str(e)}')

    def restore_from_package(self, options):
        """Restore from migration package."""
        package_path = Path(options['package'])
        
        if not package_path.exists():
            raise CommandError(f"Package file not found: {package_path}")
        
        if not package_path.name.endswith('.tar.gz'):
            raise CommandError("Package must be a .tar.gz file")
        
        self.stdout.write(f"Restoring from migration package: {package_path}")
        
        # Create temporary extraction directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract package
            self._extract_package(package_path, temp_path)
            
            # Verify package integrity
            self._verify_package_integrity(temp_path)
            
            # Load metadata
            metadata = self._load_metadata(temp_path)
            
            # Show restoration plan
            self._show_restoration_plan(metadata, options)
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING("Dry run completed - no changes made")
                )
                return
            
            # Confirm restoration
            if not options['force'] and not self._confirm_restoration():
                self.stdout.write("Restoration cancelled")
                return
            
            # Execute restoration
            self._execute_package_restoration(temp_path, metadata, options)

    def restore_from_backup_job(self, options):
        """Restore from existing backup job."""
        try:
            backup_job = BackupJob.objects.get(uuid=options['backup_job'])
        except BackupJob.DoesNotExist:
            raise CommandError(f"Backup job not found: {options['backup_job']}")
        
        if backup_job.status != 'COMPLETED':
            raise CommandError(f"Backup job is not completed: {backup_job.status}")
        
        if not backup_job.backup_file_path or not os.path.exists(backup_job.backup_file_path):
            raise CommandError("Backup file not found or missing")
        
        self.stdout.write(f"Restoring from backup job: {backup_job.job_name}")
        
        # Create restore job
        restore_job = RestoreJob.objects.create(
            backup_job=backup_job,
            restore_type=options['type'].upper(),
            target_location=options['target'],
            requested_by=None  # System restore
        )
        
        # Execute restore
        completed_job = restore_service.restore_from_backup(
            backup_job=backup_job,
            restore_type=options['type'].upper(),
            target_location=options['target'],
            requested_by=None,
            options=options
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Backup restoration completed: {completed_job.uuid}')
        )

    def restore_from_file(self, options):
        """Restore from backup file."""
        backup_path = Path(options['from_file'])
        
        if not backup_path.exists():
            raise CommandError(f"Backup file not found: {backup_path}")
        
        # Create temporary backup job record for restoration
        backup_job = BackupJob(
            job_name=f"temp_restore_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            backup_type=options['type'].upper(),
            backup_file_path=str(backup_path),
            status='COMPLETED'
        )
        
        self.stdout.write(f"Restoring from backup file: {backup_path}")
        
        # Execute restore
        completed_job = restore_service.restore_from_backup(
            backup_job=backup_job,
            restore_type=options['type'].upper(),
            target_location=options['target'],
            requested_by=None,
            options=options
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'File restoration completed: {completed_job.uuid}')
        )

    def _extract_package(self, package_path: Path, extract_path: Path):
        """Extract migration package to temporary directory."""
        self.stdout.write("Extracting migration package...")
        
        try:
            with tarfile.open(package_path, 'r:gz') as tar:
                tar.extractall(extract_path)
            
            self.stdout.write("✓ Package extracted successfully")
            
        except Exception as e:
            raise CommandError(f"Failed to extract package: {str(e)}")

    def _verify_package_integrity(self, package_path: Path):
        """Verify package integrity and required components."""
        self.stdout.write("Verifying package integrity...")
        
        # Check required components
        required_files = ['metadata.json']
        required_dirs = ['database', 'storage', 'scripts']
        
        missing_components = []
        
        for req_file in required_files:
            if not (package_path / req_file).exists():
                missing_components.append(f"file: {req_file}")
        
        for req_dir in required_dirs:
            if not (package_path / req_dir).is_dir():
                missing_components.append(f"directory: {req_dir}")
        
        if missing_components:
            raise CommandError(
                f"Package is missing required components: {', '.join(missing_components)}"
            )
        
        # Verify checksums if available
        checksum_file = package_path / 'database' / 'checksum.txt'
        if checksum_file.exists():
            self._verify_checksums(package_path / 'database')
        
        self.stdout.write("✓ Package integrity verified")

    def _verify_checksums(self, directory: Path):
        """Verify file checksums."""
        checksum_file = directory / 'checksum.txt'
        
        if not checksum_file.exists():
            return
        
        import hashlib
        
        with open(checksum_file, 'r') as f:
            for line in f:
                if '  ' in line:
                    expected_checksum, rel_path = line.strip().split('  ', 1)
                    file_path = directory / rel_path
                    
                    if file_path.exists():
                        # Calculate current checksum
                        hash_sha256 = hashlib.sha256()
                        with open(file_path, 'rb') as file_f:
                            for chunk in iter(lambda: file_f.read(4096), b""):
                                hash_sha256.update(chunk)
                        current_checksum = hash_sha256.hexdigest()
                        
                        if current_checksum != expected_checksum:
                            raise CommandError(f"Checksum mismatch for {rel_path}")

    def _load_metadata(self, package_path: Path) -> Dict[str, Any]:
        """Load package metadata."""
        metadata_file = package_path / 'metadata.json'
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            raise CommandError(f"Failed to load package metadata: {str(e)}")

    def _show_restoration_plan(self, metadata: Dict[str, Any], options: Dict[str, Any]):
        """Show what will be restored."""
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("Restoration Plan:"))
        self.stdout.write("=" * 50)
        
        # Package information
        self.stdout.write(f"Package Type: {metadata.get('export_type', 'unknown')}")
        self.stdout.write(f"EDMS Version: {metadata.get('edms_version', 'unknown')}")
        self.stdout.write(f"Export Date: {metadata.get('export_timestamp', 'unknown')}")
        
        # Components to restore
        components = metadata.get('components', {})
        self.stdout.write("")
        self.stdout.write("Components to restore:")
        
        if not options['skip_database'] and components.get('database'):
            self.stdout.write("  ✓ Database (schema and data)")
        else:
            self.stdout.write("  ✗ Database (skipped)")
        
        if not options['skip_files'] and components.get('storage_files'):
            self.stdout.write("  ✓ Storage files (documents, media, certificates)")
        else:
            self.stdout.write("  ✗ Storage files (skipped)")
        
        if not options['skip_users'] and components.get('user_accounts'):
            self.stdout.write("  ✓ User accounts and permissions")
        else:
            self.stdout.write("  ✗ User accounts (skipped)")
        
        if components.get('configuration'):
            self.stdout.write("  ✓ System configuration")
        
        self.stdout.write("")

    def _confirm_restoration(self) -> bool:
        """Ask user to confirm restoration."""
        self.stdout.write(
            self.style.WARNING(
                "⚠️  WARNING: This will overwrite existing data!"
            )
        )
        self.stdout.write("Current database and files will be replaced.")
        
        response = input("Do you want to continue? (yes/no): ")
        return response.lower() in ['yes', 'y']

    def _execute_package_restoration(self, package_path: Path, metadata: Dict[str, Any], options: Dict[str, Any]):
        """Execute the complete package restoration."""
        self.stdout.write("")
        self.stdout.write("Starting restoration...")
        
        try:
            # 1. Restore database
            if not options['skip_database']:
                self._restore_database_from_package(package_path)
            
            # 2. Restore storage files
            if not options['skip_files']:
                self._restore_storage_from_package(package_path, options)
            
            # 3. Restore user accounts
            if not options['skip_users']:
                self._restore_users_from_package(package_path)
            
            # 4. Apply configuration
            self._apply_configuration_from_package(package_path)
            
            # 5. Verify restoration
            if options['verify']:
                self._verify_restoration(package_path)
            
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS("✅ Package restoration completed successfully!")
            )
            
            # Log audit trail
            audit_service.log_system_event(
                event_type='PACKAGE_RESTORE_COMPLETED',
                object_type='System',
                description="Migration package restored successfully",
                additional_data={
                    'package_metadata': metadata,
                    'restore_options': options
                }
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Restoration failed: {str(e)}")
            )
            raise

    def _restore_database_from_package(self, package_path: Path):
        """Restore database from package."""
        self.stdout.write("📊 Restoring database...")
        
        db_file = package_path / 'database' / 'complete.sql'
        if not db_file.exists():
            raise CommandError("Database backup file not found in package")
        
        db_settings = settings.DATABASES['default']
        
        # Restore database
        cmd = [
            'psql',
            '-h', db_settings['HOST'],
            '-p', str(db_settings['PORT']),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', str(db_file)
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            self.stdout.write("✓ Database restored successfully")
            
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Database restoration failed: {e.stderr.decode()}")

    def _restore_storage_from_package(self, package_path: Path, options: Dict[str, Any]):
        """Restore storage files from package."""
        self.stdout.write("📁 Restoring storage files...")
        
        storage_source = package_path / 'storage'
        if not storage_source.exists():
            self.stdout.write("⚠️  No storage files found in package")
            return
        
        # Determine target storage directory
        storage_root = Path(settings.BASE_DIR).parent / 'storage'
        
        # Create backup of existing storage
        if storage_root.exists() and not options.get('force'):
            backup_name = f"storage_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = storage_root.parent / backup_name
            shutil.move(str(storage_root), str(backup_path))
            self.stdout.write(f"✓ Existing storage backed up to: {backup_path}")
        
        # Copy storage files
        storage_root.mkdir(parents=True, exist_ok=True)
        
        for item in storage_source.iterdir():
            if item.name != 'manifest.json':
                target = storage_root / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(target), dirs_exist_ok=True)
                else:
                    shutil.copy2(str(item), str(target))
        
        self.stdout.write("✓ Storage files restored successfully")

    def _restore_users_from_package(self, package_path: Path):
        """Restore user accounts from package."""
        self.stdout.write("👥 Restoring user accounts...")
        
        users_file = package_path / 'configuration' / 'users.json'
        permissions_file = package_path / 'configuration' / 'permissions.json'
        
        if not users_file.exists():
            self.stdout.write("⚠️  No user data found in package")
            return
        
        try:
            # Restore groups and permissions first
            if permissions_file.exists():
                with open(permissions_file, 'r') as f:
                    groups_data = json.load(f)
                
                for group_data in groups_data:
                    group, created = Group.objects.get_or_create(name=group_data['name'])
                    if created:
                        # Add permissions to group
                        for perm_codename in group_data.get('permissions', []):
                            try:
                                permission = Permission.objects.get(codename=perm_codename)
                                group.permissions.add(permission)
                            except Permission.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f"Permission not found: {perm_codename}")
                                )
            
            # Restore users
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            with transaction.atomic():
                for user_data in users_data:
                    username = user_data['username']
                    
                    # Check if user exists
                    try:
                        user = User.objects.get(username=username)
                        # Update existing user
                        for field in ['email', 'first_name', 'last_name', 'is_active', 'is_staff']:
                            if field in user_data:
                                setattr(user, field, user_data[field])
                        user.save()
                        action = "updated"
                    except User.DoesNotExist:
                        # Create new user
                        user = User.objects.create_user(
                            username=username,
                            email=user_data.get('email', ''),
                            first_name=user_data.get('first_name', ''),
                            last_name=user_data.get('last_name', ''),
                            is_active=user_data.get('is_active', True),
                            is_staff=user_data.get('is_staff', False),
                            is_superuser=user_data.get('is_superuser', False)
                        )
                        # Note: Password will need to be reset
                        user.set_unusable_password()
                        user.save()
                        action = "created"
                    
                    # Add user to groups
                    for group_name in user_data.get('groups', []):
                        try:
                            group = Group.objects.get(name=group_name)
                            user.groups.add(group)
                        except Group.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f"Group not found: {group_name}")
                            )
                    
                    self.stdout.write(f"✓ User {action}: {username}")
            
            self.stdout.write("✓ User accounts restored successfully")
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  All user passwords need to be reset!"
                )
            )
            
        except Exception as e:
            raise CommandError(f"User restoration failed: {str(e)}")

    def _apply_configuration_from_package(self, package_path: Path):
        """Apply configuration from package."""
        self.stdout.write("⚙️  Configuration restoration available")
        
        config_file = package_path / 'configuration' / 'settings.json'
        if config_file.exists():
            self.stdout.write(
                "Configuration data found - manual review recommended for production settings"
            )

    def _verify_restoration(self, package_path: Path):
        """Verify restoration integrity."""
        self.stdout.write("🔍 Verifying restoration...")
        
        # Verify database connectivity
        try:
            from django.core.management import execute_from_command_line
            from django.db import connection
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    self.stdout.write("✓ Database connectivity verified")
                else:
                    self.stdout.write("⚠️  Database connectivity issue")
        except Exception as e:
            self.stdout.write(f"⚠️  Database verification failed: {str(e)}")
        
        # Verify storage structure
        storage_root = Path(settings.BASE_DIR).parent / 'storage'
        storage_dirs = ['documents', 'media']
        
        for storage_dir in storage_dirs:
            if (storage_root / storage_dir).exists():
                self.stdout.write(f"✓ Storage directory verified: {storage_dir}")
            else:
                self.stdout.write(f"⚠️  Storage directory missing: {storage_dir}")
        
        self.stdout.write("✓ Restoration verification completed")