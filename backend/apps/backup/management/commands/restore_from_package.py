"""
Production-ready restore command for EDMS.

Usage:
    python manage.py restore_from_package /path/to/package.tar.gz --type full --confirm
    python manage.py restore_from_package /path/to/package.tar.gz --type database --dry-run
"""

import os
import tempfile
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.backup.models import RestoreJob, BackupJob
from apps.backup.api_views import SystemBackupViewSet
from apps.audit.services import audit_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Restore system from migration package with production safeguards'

    def add_arguments(self, parser):
        parser.add_argument(
            'package_path',
            type=str,
            help='Path to migration package file (.tar.gz)'
        )
        parser.add_argument(
            '--type',
            choices=['full', 'database', 'files'],
            default='full',
            help='Type of restore to perform (default: full)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate package without performing restore'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm destructive operation (required for actual restore)'
        )
        parser.add_argument(
            '--backup-current',
            action='store_true',
            help='Create backup of current system before restore'
        )
        parser.add_argument(
            '--skip-interactive',
            action='store_true',
            help='Skip interactive confirmation (for API/automated calls)'
        )
        parser.add_argument(
            '--with-reinit',
            action='store_true',
            help='DANGER: Reinitialize (wipe) the system before restore for catastrophic recovery'
        )

    def handle(self, *args, **options):
        package_path = options['package_path']
        restore_type = options['type']
        dry_run = options['dry_run']
        confirm = options['confirm']
        backup_current = options['backup_current']
        skip_interactive = options['skip_interactive']
        with_reinit = options.get('with_reinit', False)

        self.stdout.write(self.style.SUCCESS('🔄 EDMS System Restore'))
        self.stdout.write('=' * 50)
        
        # Validate package path
        if not os.path.exists(package_path):
            raise CommandError(f"Package file not found: {package_path}")
        
        # Get admin user for operation
        admin_user = User.objects.filter(is_staff=True, is_active=True).first()
        if not admin_user:
            raise CommandError("No admin user found for restore operation")

        self.stdout.write(f"Package: {package_path}")
        self.stdout.write(f"Type: {restore_type}")
        self.stdout.write(f"Size: {os.path.getsize(package_path):,} bytes")
        self.stdout.write()

        # Step 1: Validate package
        self.stdout.write("🔍 Validating package...")
        viewset = SystemBackupViewSet()
        
        validation_results = viewset.validate_backup_integrity(
            package_path, os.path.basename(package_path)
        )
        
        if not validation_results['valid']:
            raise CommandError(f"Package validation failed: {validation_results['error']}")
        
        self.stdout.write(self.style.SUCCESS("✅ Package validation passed"))
        self.stdout.write(f"  Archive members: {validation_results['details'].get('archive_members', 0)}")
        self.stdout.write(f"  Has database: {validation_results['details'].get('has_database', False)}")
        self.stdout.write(f"  Has storage: {validation_results['details'].get('has_storage', False)}")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS("🏁 Dry run completed - package is valid for restoration"))
            return

        # Step 2: Safety checks for actual restore
        if not confirm:
            self.stdout.write(self.style.ERROR("❌ Destructive operation requires --confirm flag"))
            self.stdout.write("This will OVERWRITE current system data!")
            return

        # Step 3: Optional current system backup
        if backup_current:
            self.stdout.write("💾 Creating backup of current system...")
            self.create_current_backup()

        # Step 4: Confirmation prompt
        import sys
        if skip_interactive or not sys.stdin.isatty():
            # Running in non-interactive mode (API call) - confirmations already handled
            self.stdout.write(self.style.NOTICE('✅ Running in non-interactive mode - confirmations verified'))
        else:
            # Interactive mode - require manual confirmation
            self.stdout.write(self.style.WARNING("⚠️  CRITICAL WARNING"))
            self.stdout.write("This operation will:")
            if restore_type in ['full', 'database']:
                self.stdout.write("  - OVERWRITE current database")
            if restore_type in ['full', 'files']:
                self.stdout.write("  - OVERWRITE current files")
            self.stdout.write("  - This action CANNOT be undone!")
            
            try:
                confirm_input = input("Type 'RESTORE' to proceed: ")
                if confirm_input != 'RESTORE':
                    self.stdout.write("Operation cancelled by user")
                    return
            except (EOFError, KeyboardInterrupt):
                self.stdout.write('\nOperation cancelled.')
                return

        # Optional catastrophic recovery reinit step
        if with_reinit:
            self.stdout.write(self.style.WARNING("\n\u26a0\ufe0f  WITH-REINIT OPTION ENABLED"))
            self.stdout.write(self.style.WARNING("This will perform a complete system reinitialization BEFORE restore."))
            self.stdout.write(self.style.WARNING("All non-core data will be wiped. Proceeding..."))
            from django.core.management import call_command
            try:
                call_command('system_reinit', confirm=True, skip_interactive=True)
                self.stdout.write(self.style.SUCCESS("\u2705 System reinit completed successfully"))
            except Exception as e:
                raise CommandError(f"System reinit failed: {str(e)}")

        # Step 5: Execute restore
        self.stdout.write(f"🔄 Executing {restore_type} restore...")
        
        try:
            # Create or get a default configuration for CLI backups
            from apps.backup.models import BackupConfiguration
            cli_config, created = BackupConfiguration.objects.get_or_create(
                name='cli_restore_config',
                defaults={
                    'backup_type': 'FULL',
                    'frequency': 'ON_DEMAND',
                    'schedule_time': '12:00:00',
                    'storage_path': os.path.dirname(package_path),
                    'created_by': admin_user
                }
            )
            
            # Force save and refresh the configuration to ensure it has an ID
            cli_config.save()
            cli_config.refresh_from_db()
            
            self.stdout.write(f"  Using configuration: {cli_config.name} (ID: {cli_config.id})")
            
            # Create temporary backup job for restore tracking
            temp_backup_job = BackupJob.objects.create(
                job_name=f"restore_source_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                backup_type='FULL',  # Assume full restore for CLI
                backup_file_path=package_path,
                status='COMPLETED',
                backup_size=os.path.getsize(package_path),
                triggered_by=admin_user,
                started_at=timezone.now(),
                completed_at=timezone.now(),
                configuration_id=cli_config.id  # Explicitly set the configuration_id
            )
            
            # Create restore job
            restore_job = RestoreJob.objects.create(
                backup_job=temp_backup_job,
                restore_type=restore_type.upper() + '_RESTORE',
                target_location='/app',
                status='RUNNING',
                requested_by=admin_user,
                started_at=timezone.now()
            )
            
            # Copy package to temporary location for restore
            temp_path = f"/tmp/restore_package_{restore_job.uuid}.tar.gz"
            shutil.copy2(package_path, temp_path)
            
            # Execute restore
            success = viewset._execute_restore_operation(
                temp_path, restore_type, restore_job, admin_user
            )
            
            if success:
                restore_job.status = 'COMPLETED'
                restore_job.completed_at = timezone.now()
                restore_job.save()
                
                self.stdout.write(self.style.SUCCESS("✅ Restore completed successfully!"))
                self.stdout.write(f"Restore Job ID: {restore_job.uuid}")
                self.stdout.write(f"Items restored: {restore_job.restored_items_count}")
                self.stdout.write(f"Items failed: {restore_job.failed_items_count}")
                
                # Attempt to automatically import workflow history from the package
                try:
                    import tarfile
                    import tempfile
                    import json
                    from django.core.management import call_command

                    if package_path.endswith('.tar.gz') or package_path.endswith('.tgz'):
                        self.stdout.write("📜 Scanning package for workflow history (database_backup.json)...")
                        with tarfile.open(package_path, 'r:gz') as tar:
                            member = None
                            # Prefer .../database/database_backup.json; fallback to any database_backup.json
                            for m in tar.getmembers():
                                name_low = m.name.lower()
                                if name_low.endswith('/database/database_backup.json') or name_low.endswith('database_backup.json'):
                                    member = m
                                    # Prefer the database/ path; break only if found preferred path
                                    if '/database/' in name_low:
                                        break
                            if member is not None:
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmpf:
                                    extracted = tar.extractfile(member)
                                    tmpf.write(extracted.read())
                                    tmp_json_path = tmpf.name
                                self.stdout.write(self.style.NOTICE(f"➡️  Importing workflow history from {member.name}"))
                                # Run the dedicated importer which resolves natural keys reliably
                                call_command('import_workflow_history', backup_json=tmp_json_path, verbose=True)
                                # Optionally verify and print summary (non-fatal)
                                self.stdout.write(self.style.NOTICE("🔎 Verifying workflow history after import..."))
                                call_command('verify_workflow_history', backup_json=tmp_json_path, verbose=False)
                            else:
                                self.stdout.write(self.style.WARNING("⚠️  No database_backup.json found in package; skipping workflow history import."))
                    else:
                        self.stdout.write(self.style.WARNING("⚠️  Package is not a .tar.gz archive; skipping workflow history import."))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠️  Workflow history import/verification encountered an issue: {e}"))
                
                # Log audit event
                audit_service.log_user_action(
                    user=admin_user,
                    action='CLI_RESTORE_COMPLETED',
                    object_type='RestoreJob',
                    object_id=restore_job.id,
                    description=f'CLI restore completed from package {os.path.basename(package_path)}',
                    additional_data={
                        'package_path': package_path,
                        'restore_type': restore_type,
                        'success': True,
                        'package_size': os.path.getsize(package_path)
                    }
                )
            else:
                restore_job.status = 'FAILED'
                restore_job.completed_at = timezone.now()
                restore_job.save()
                raise CommandError("Restore operation failed")
            
            # Cleanup temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Restore failed: {str(e)}"))
            raise CommandError(f"Restore operation failed: {str(e)}")

    def create_current_backup(self):
        """Create a backup of the current system before restore."""
        from django.core.management import call_command
        
        try:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"/tmp/pre_restore_backup_{timestamp}.tar.gz"
            
            call_command(
                'create_backup',
                type='full',
                output=backup_path,
                compress=True,
                verify=True
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Current system backed up to: {backup_path}"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Failed to create current backup: {str(e)}"))
            self.stdout.write("Proceeding without backup...")