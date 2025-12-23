"""
Management command to create system backups.

Usage:
    python manage.py create_backup --type full --output /path/to/backup
    python manage.py create_backup --type database --schedule
    python manage.py create_backup --type export --output /path/to/export.tar.gz
"""

import os
import json
import tarfile
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

from apps.backup.models import BackupConfiguration, BackupJob
from apps.backup.services import backup_service
from apps.audit.services import audit_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Create system backups with enhanced options for migration and disaster recovery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--require-workflow-history', action='store_true', dest='require_workflow_history',
            help='Fail export if workflow instances/transitions are missing (default: warn only)'
        )
        parser.add_argument(
            '--type',
            choices=['full', 'database', 'files', 'export', 'incremental'],
            default='full',
            help='Type of backup to create'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output path for backup file (required for export type)'
        )
        parser.add_argument(
            '--schedule',
            action='store_true',
            help='Use existing scheduled backup configuration'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            default=True,
            help='Enable compression (default: True)'
        )
        parser.add_argument(
            '--encrypt',
            action='store_true',
            help='Enable encryption for sensitive data'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            default=True,
            help='Verify backup integrity after creation'
        )
        parser.add_argument(
            '--include-users',
            action='store_true',
            default=True,
            help='Include user accounts in export (excludes passwords)'
        )
        parser.add_argument(
            '--config-name',
            type=str,
            help='Name of backup configuration to use'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        
        try:
            if backup_type == 'export':
                # Create migration package
                if not options['output']:
                    raise CommandError("Export type requires --output parameter")
                self.create_export_package(options)
            elif options['schedule']:
                # Use scheduled backup configuration
                self.create_scheduled_backup(options)
            else:
                # Create ad-hoc backup
                self.create_adhoc_backup(options)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )
            raise CommandError(f'Backup operation failed: {str(e)}')

    def create_export_package(self, options):
        """Create complete migration export package."""
        output_path = Path(options['output'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_path.is_dir():
            # Create filename if directory provided
            output_path = output_path / f"edms_migration_package_{timestamp}.tar.gz"
        
        self.stdout.write(f"Creating migration package: {output_path}")
        
        # Create temporary directory for package components
        temp_dir = Path(f"/tmp/edms_export_{timestamp}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. Export metadata
            self._export_metadata(temp_dir, options)
            
            # 2. Export database
            self._export_database(temp_dir)
            
            # 3. Export storage files
            self._export_storage(temp_dir)
            
            # 4. Export configuration
            self._export_configuration(temp_dir, options)
            
            # 5. Create restore scripts
            self._create_restore_scripts(temp_dir)
            
            # 6. Create final package
            self._create_package(temp_dir, output_path)
            
            # 7. Verify package
            if options['verify']:
                self._verify_package(output_path)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Migration package created successfully: {output_path}'
                )
            )
            
            # Log audit trail
            audit_service.log_system_event(
                event_type='BACKUP',
                object_type='System',
                description=f"Migration package created: {output_path.name}",
                additional_data={
                    'package_path': str(output_path),
                    'package_size': output_path.stat().st_size if output_path.exists() else 0,
                    'export_options': options
                }
            )
            
        finally:
            # Cleanup temporary directory
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _export_metadata(self, temp_dir: Path, options: Dict):
        """Export system metadata and manifest."""
        metadata = {
            'export_timestamp': timezone.now().isoformat(),
            'edms_version': getattr(settings, 'VERSION', '1.0.0'),
            'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            'python_version': getattr(settings, 'PYTHON_VERSION', 'unknown'),
            'export_type': 'migration_package',
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'export_options': {k: v for k, v in options.items() if k != 'verbosity'},
            'components': {
                'database': True,
                'storage_files': True,
                'configuration': True,
                'user_accounts': options.get('include_users', True),
                'restore_scripts': True
            }
        }
        
        metadata_file = temp_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.stdout.write("✓ Exported metadata")

    def _export_database(self, temp_dir: Path):
        """Export complete database with schema and data."""
        db_dir = temp_dir / 'database'
        db_dir.mkdir(exist_ok=True)
        
        db_settings = settings.DATABASES['default']
        
        # Create complete database backup with actual data using Django's dumpdata
        from django.core.management import call_command
        from django.apps import apps
        import json
        import tempfile
        
        self.stdout.write("Creating complete database backup with actual data...")
        
        # Define apps and models to backup
        # Include Django system tables for complete restoration
        apps_to_backup = [
            'contenttypes',     # Django content types - CRITICAL for model references
            'auth',             # Django auth (groups, permissions) - CRITICAL for authorization
            'admin',            # Django admin logs
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
        
        # Models to exclude (contain sensitive or non-essential data)
        exclude_models = [
            'sessions.session',      # User sessions (can be regenerated)
            'admin.logentry',        # Admin logs (optional, can be excluded for size)
        ]
        
        # CRITICAL FIX: Ensure Django auth models and M2M relationships are included
        # Django's dumpdata includes M2M tables automatically when parent models are included
        # Note: System uses custom user model (users.User), not auth.user
        include_models = [
            'auth.group',            # Django groups (includes group_permissions M2M automatically)  
            'auth.permission',       # Django permissions
            # auth.user not needed - system uses custom users.User model
        ]
        
        # Create complete data backup using Django's dumpdata
        data_file = db_dir / 'database_backup.json'
        
        try:
            # Use temporary file to handle large datasets
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                self.stdout.write(f"Exporting data from apps: {', '.join(apps_to_backup)}")
                
                # Export data using Django's dumpdata with natural keys
                # CRITICAL FIX: Include specific models to ensure M2M relationships are exported
                all_models_to_backup = list(apps_to_backup) + include_models
                
                call_command(
                    'dumpdata',
                    *all_models_to_backup,  # Include all critical apps AND specific M2M models
                    '--natural-foreign',    # Use natural keys for foreign key references
                    '--natural-primary',    # Use natural keys for primary keys where available
                    '--indent=2',           # Pretty formatting for debugging
                    '--exclude=sessions.session',  # Exclude session data
                    stdout=temp_file,
                    verbosity=0            # Quiet output to avoid mixing with our messages
                )
                temp_file_path = temp_file.name
            
            # Move temporary file to final location
            import shutil
            shutil.move(temp_file_path, str(data_file))
            
            # Get statistics about the backup
            with open(data_file, 'r') as f:
                backup_data = json.load(f)
                
            # Create backup metadata
            metadata = {
                'backup_type': 'django_complete_data',
                'created_at': timezone.now().isoformat(),
                'database_info': {
                    'engine': db_settings['ENGINE'],
                    'name': db_settings['NAME']
                },
                'apps_included': apps_to_backup,
                'auth_models_included': include_models,     # FIXED: Track explicitly included Django auth models
                'excluded_models': exclude_models,
                'total_records': len(backup_data),
                'model_counts': {}
            }
            
            # Count records by model
            for record in backup_data:
                model = record.get('model', 'unknown')
                metadata['model_counts'][model] = metadata['model_counts'].get(model, 0) + 1
            
            # Save metadata file
            metadata_file = db_dir / 'backup_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

            # Export-time completeness checks (fail fast)
            required_models = ['documents.documenttype', 'documents.documentsource']
            missing_required = [m for m in required_models if metadata['model_counts'].get(m, 0) == 0]
            if missing_required:
                raise CommandError(
                    f"Export completeness check failed: missing models {missing_required}. "
                    f"Ensure DocumentType and DocumentSource exist before export."
                )
            # Every document must have type and source fields present
            doc_count = metadata['model_counts'].get('documents.document', 0)
            if doc_count:
                missing_type = 0
                missing_source = 0
                for rec in backup_data:
                    if rec.get('model') == 'documents.document':
                        flds = rec.get('fields', {})
                        dt = flds.get('document_type')
                        ds = flds.get('document_source')
                        # Expect lists from natural keys e.g., ['POL']
                        if not (isinstance(dt, list) and dt and dt[0]):
                            missing_type += 1
                        if not (isinstance(ds, list) and ds and ds[0]):
                            missing_source += 1
                if missing_type or missing_source:
                    raise CommandError(
                        f"Export completeness check failed: documents missing type={missing_type}, source={missing_source}. "
                        f"All documents must reference a valid DocumentType and DocumentSource."
                    )

                # Workflow history presence check: warn by default, fail if flag provided
                wf_count = metadata['model_counts'].get('workflows.documentworkflow', 0)
                tr_count = metadata['model_counts'].get('workflows.documenttransition', 0)
                require_wf = getattr(self, 'require_workflow_history', False)
                if (wf_count == 0 or tr_count == 0):
                    msg = (
                        f"Warning: Export contains {doc_count} documents but workflow history is empty "
                        f"(workflows={wf_count}, transitions={tr_count})."
                    )
                    if require_wf:
                        raise CommandError(
                            msg + " Use actual source data with workflows or disable --require-workflow-history."
                        )
                    else:
                        self.stdout.write(self.style.WARNING(msg))
                
            self.stdout.write(f"✓ Exported {len(backup_data)} database records")
            self.stdout.write(f"✓ Backup includes {len(metadata['model_counts'])} model types")
            
            # Show breakdown of what was backed up
            critical_models = [
                'contenttypes.contenttype',
                'auth.permission', 'auth.group',
                'users.user', 'users.role', 'users.userrole',
                'documents.documenttype', 'documents.document',
                'workflows.documentstate', 'workflows.workflowtype',
                'placeholders.placeholderdefinition',
                'security.pdfsigningcertificate'
            ]
            
            self.stdout.write("\nCritical data backup status:")
            for model in critical_models:
                count = metadata['model_counts'].get(model, 0)
                status = '✓' if count > 0 else '⚠️'
                self.stdout.write(f"  {status} {model}: {count} records")
                
        except Exception as e:
            self.stderr.write(f"❌ Complete database backup failed: {str(e)}")
            # Fallback to metadata-only backup
            self.stdout.write("Creating fallback metadata backup...")
            backup_data = {
                'backup_type': 'edms_metadata_fallback',
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
            from django.db import connection
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
            
            with open(data_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
        
        # Create a simple schema reference file
        schema_file = db_dir / 'schema_info.txt'
        with open(schema_file, 'w') as f:
            f.write("Database Schema Information\n")
            f.write("===========================\n\n")
            f.write("This backup uses Django's dumpdata format (JSON).\n")
            f.write("To restore:\n")
            f.write("1. Create a fresh Django database\n") 
            f.write("2. Run: python manage.py migrate\n")
            f.write("3. Run: python manage.py loaddata database_backup.json\n\n")
            f.write(f"Backup created: {data_file}\n")
            import django
            f.write(f"Django version: {django.VERSION}\n")
        
        self.stdout.write(f"Data exported to: {data_file}")
        self.stdout.write(f"Schema info: {schema_file}")
        
        # Create a restore script for easier recovery
        restore_script = db_dir / 'restore_instructions.sh'
        with open(restore_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Django EDMS Database Restore Script\n\n")
            f.write("echo 'Restoring Django EDMS database backup...'\n")
            f.write("echo 'Make sure you have:'\n")
            f.write("echo '1. Created a fresh Django database'\n") 
            f.write("echo '2. Run: python manage.py migrate'\n")
            f.write("echo 'Now running: python manage.py loaddata database_backup.json'\n\n")
            f.write("python manage.py loaddata database_backup.json\n")
            f.write("echo 'Database restore completed!'\n")
        
        import os
        os.chmod(restore_script, 0o755)
        
        # Create checksums
        self._create_checksums(db_dir)
        
        self.stdout.write("✓ Exported database")

    def _export_storage(self, temp_dir: Path):
        """Export all storage files and critical configuration files with manifest."""
        storage_dir = temp_dir / 'storage'
        storage_dir.mkdir(exist_ok=True)
        
        # CRITICAL FIX: Create configuration directory for environment files
        config_dir = temp_dir / 'configuration'
        config_dir.mkdir(exist_ok=True)
        
        # Define source directories with multiple fallback paths
        base_dir = Path(settings.BASE_DIR)
        
        # Try multiple possible storage locations
        possible_storage_roots = [
            base_dir.parent / 'storage',  # /storage (sibling to backend)
            base_dir / 'storage',         # backend/storage  
            Path('/app/storage'),         # Docker container storage
            getattr(settings, 'DOCUMENT_STORAGE_ROOT', None),  # Configured path
        ]
        
        # Find actual storage root
        storage_root = None
        for path in possible_storage_roots:
            if path and Path(path).exists():
                storage_root = Path(path)
                break
        
        if not storage_root:
            # Create a fallback storage mapping
            self.stdout.write(self.style.WARNING("No storage root found, checking individual paths..."))
        
        storage_sources = {}
        
        # Check for document storage
        doc_paths = [
            storage_root / 'documents' if storage_root else None,
            base_dir.parent / 'storage' / 'documents',
            Path('/app/storage/documents'),
            getattr(settings, 'DOCUMENT_STORAGE_ROOT', None)
        ]
        
        for path in doc_paths:
            if path and Path(path).exists():
                storage_sources['documents'] = path
                break
                
        # Check for media storage  
        media_paths = [
            storage_root / 'media' if storage_root else None,
            base_dir.parent / 'storage' / 'media',
            Path('/app/storage/media'),
            getattr(settings, 'MEDIA_ROOT', None)
        ]
        
        for path in media_paths:
            if path and Path(path).exists():
                storage_sources['media'] = path
                break
        
        # Check for certificates
        cert_paths = [
            Path(settings.OFFICIAL_PDF_CONFIG.get('CERTIFICATE_STORAGE_PATH', '')),
            storage_root / 'certificates' if storage_root else None,
            base_dir.parent / 'storage' / 'certificates',
            Path('/app/storage/certificates')
        ]
        
        for path in cert_paths:
            if path and Path(path).exists():
                storage_sources['certificates'] = path
                break
        
        self.stdout.write(f"Found storage sources: {list(storage_sources.keys())}")
        if storage_sources:
            for storage_type, path in storage_sources.items():
                file_count = len(list(Path(path).rglob('*'))) if Path(path).is_dir() else 0
                self.stdout.write(f"  {storage_type}: {path} ({file_count} files)")
        else:
            self.stdout.write(self.style.WARNING("No storage directories found!"))
        
        # CRITICAL FIX: Define critical configuration files to backup
        critical_config_files = [
            ('/app/.env', 'environment_variables.env'),
            ('/app/.env.workflow', 'workflow_environment.env'),
        ]
        
        manifest = {
            'created_at': timezone.now().isoformat(),
            'files': {}
        }
        
        config_manifest = {
            'backup_type': 'configuration_files',
            'created_at': timezone.now().isoformat(),
            'critical_warning': 'These files contain sensitive information including SECRET_KEY - handle securely',
            'files_backed_up': 0,
            'config_files': []
        }
        
        # Export storage files
        for storage_type, source_path in storage_sources.items():
            if not Path(source_path).exists():
                self.stdout.write(
                    self.style.WARNING(f"Storage path not found: {source_path}")
                )
                continue
                
            target_dir = storage_dir / storage_type
            
            # Copy directory with structure preservation
            import shutil
            if Path(source_path).is_dir():
                shutil.copytree(source_path, target_dir, dirs_exist_ok=True)
                
                # Create file manifest
                for root, dirs, files in os.walk(target_dir):
                    for file in files:
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(storage_dir)
                        
                        # Calculate checksum
                        checksum = self._calculate_file_checksum(file_path)
                        
                        manifest['files'][str(rel_path)] = {
                            'size': file_path.stat().st_size,
                            'checksum': checksum,
                            'modified': file_path.stat().st_mtime
                        }
        
        # CRITICAL FIX: Export environment configuration files
        config_backed_up = 0
        for source_path, backup_name in critical_config_files:
            source = Path(source_path)
            if source.exists():
                import shutil
                target = config_dir / backup_name
                shutil.copy2(source, target)
                self.stdout.write(f"✓ Backed up critical configuration: {source_path}")
                config_backed_up += 1
                
                # Add to config manifest
                config_manifest['config_files'].append({
                    'original_path': source_path,
                    'backup_name': backup_name,
                    'size': source.stat().st_size,
                    'contains_secrets': True,
                    'restore_location': source_path,
                    'checksum': self._calculate_file_checksum(source)
                })
            else:
                self.stdout.write(f"⚠ Critical configuration file not found: {source_path}")
        
        # CRITICAL FIX: Export Django settings directory
        settings_source = Path('/app/edms/settings')
        if settings_source.exists():
            import shutil
            settings_target = config_dir / 'django_settings'
            shutil.copytree(settings_source, settings_target, dirs_exist_ok=True)
            self.stdout.write(f"✓ Backed up Django settings directory")
            config_backed_up += 1
            
            # Add settings files to manifest
            for settings_file in settings_target.rglob('*.py'):
                rel_path = settings_file.relative_to(config_dir)
                config_manifest['config_files'].append({
                    'original_path': f'/app/edms/settings/{settings_file.name}',
                    'backup_name': str(rel_path),
                    'size': settings_file.stat().st_size,
                    'contains_secrets': 'SECRET' in settings_file.read_text() or 'PASSWORD' in settings_file.read_text(),
                    'restore_location': f'/app/edms/settings/{settings_file.name}',
                    'checksum': self._calculate_file_checksum(settings_file)
                })
        else:
            self.stdout.write("⚠ Django settings directory not found")
        
        # Update config manifest
        config_manifest['files_backed_up'] = config_backed_up
        
        # Save manifests
        manifest_file = storage_dir / 'manifest.json'
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        config_manifest_file = config_dir / 'config_manifest.json'
        with open(config_manifest_file, 'w') as f:
            json.dump(config_manifest, f, indent=2)
        
        # CRITICAL FIX: Create environment restoration instructions
        restore_instructions = config_dir / 'RESTORE_INSTRUCTIONS.md'
        with open(restore_instructions, 'w') as f:
            f.write("""# Environment Configuration Restore Instructions

## CRITICAL: Environment Variables

This backup includes environment configuration files that contain sensitive information:

1. **environment_variables.env** - Main Django environment file
   - Contains SECRET_KEY (REQUIRED for Django to start)
   - Contains database credentials
   - Contains ALLOWED_HOSTS configuration

2. **Django Settings** - Django configuration files
   - Contains application configuration
   - May contain additional sensitive settings

## Restore Process

1. **Copy environment file**:
   ```bash
   cp configuration/environment_variables.env /app/.env
   ```

2. **Copy Django settings** (if needed):
   ```bash
   cp -r configuration/django_settings/* /app/edms/settings/
   ```

3. **Set proper permissions**:
   ```bash
   chmod 600 /app/.env
   chmod 644 /app/edms/settings/*.py
   ```

4. **Verify environment variables are loaded**:
   ```bash
   python manage.py check
   ```

## Security Notes

- These files contain SECRET_KEY and database passwords
- Store this backup securely
- Rotate SECRET_KEY if this backup is compromised
- Review ALLOWED_HOSTS for your target environment

""")
        
        self.stdout.write("✓ Exported storage files")
        self.stdout.write(f"✓ Backed up {config_backed_up} critical configuration components")
        
        if config_backed_up < 2:
            self.stdout.write("⚠ WARNING: Some critical configuration files missing")
            self.stdout.write("⚠ Manual environment setup may be required during restore")
        else:
            self.stdout.write("✓ All critical configuration files backed up successfully")

    def _export_configuration(self, temp_dir: Path, options: Dict):
        """Export system configuration and user accounts."""
        config_dir = temp_dir / 'configuration'
        config_dir.mkdir(exist_ok=True)
        
        # Export system settings (non-sensitive)
        settings_export = {
            'timezone': settings.TIME_ZONE,
            'language': settings.LANGUAGE_CODE,
            'installed_apps': [app for app in settings.INSTALLED_APPS if app.startswith('apps.')],
            'document_processing': getattr(settings, 'DOCUMENT_PROCESSING', {}),
            'audit_settings': getattr(settings, 'AUDIT_SETTINGS', {}),
            'official_pdf_config': {
                k: v for k, v in settings.OFFICIAL_PDF_CONFIG.items() 
                if k not in ['CERTIFICATE_STORAGE_PATH']  # Exclude paths
            }
        }
        
        settings_file = config_dir / 'settings.json'
        with open(settings_file, 'w') as f:
            json.dump(settings_export, f, indent=2)
        
        # Export user accounts (if requested)
        if options.get('include_users', True):
            users_data = []
            for user in User.objects.all():
                user_data = {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'groups': [group.name for group in user.groups.all()],
                    'user_permissions': [perm.codename for perm in user.user_permissions.all()],
                    'date_joined': user.date_joined.isoformat(),
                    # Note: Password is NOT exported for security
                }
                users_data.append(user_data)
            
            users_file = config_dir / 'users.json'
            with open(users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
        
        # Export permissions and groups
        from django.contrib.auth.models import Group, Permission
        
        groups_data = []
        for group in Group.objects.all():
            group_data = {
                'name': group.name,
                'permissions': [perm.codename for perm in group.permissions.all()]
            }
            groups_data.append(group_data)
        
        permissions_file = config_dir / 'permissions.json'
        with open(permissions_file, 'w') as f:
            json.dump(groups_data, f, indent=2)
        
        self.stdout.write("✓ Exported configuration")

    def _create_restore_scripts(self, temp_dir: Path):
        """Create automated restore scripts."""
        scripts_dir = temp_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        
        # Main restore script
        restore_script = scripts_dir / 'restore.sh'
        with open(restore_script, 'w') as f:
            f.write(self._get_restore_script_content())
        
        # Verification script
        verify_script = scripts_dir / 'verify.sh'
        with open(verify_script, 'w') as f:
            f.write(self._get_verify_script_content())
        
        # Make scripts executable
        restore_script.chmod(0o755)
        verify_script.chmod(0o755)
        
        self.stdout.write("✓ Created restore scripts")

    def _create_package(self, temp_dir: Path, output_path: Path):
        """Create final compressed package."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(output_path, 'w:gz') as tar:
            tar.add(temp_dir, arcname='.')
        
        self.stdout.write(f"✓ Created package: {output_path}")

    def _verify_package(self, package_path: Path):
        """Verify package integrity."""
        try:
            with tarfile.open(package_path, 'r:gz') as tar:
                # Basic integrity check
                tar.getmembers()
                
                # Check for required components
                member_names = [m.name for m in tar.getmembers()]
                required = ['metadata.json', 'database/', 'storage/', 'scripts/']
                
                missing = [req for req in required if not any(req in name for name in member_names)]
                if missing:
                    raise ValueError(f"Missing required components: {missing}")
                
            self.stdout.write("✓ Package verification passed")
            
        except Exception as e:
            raise CommandError(f"Package verification failed: {str(e)}")

    def create_scheduled_backup(self, options):
        """Create backup using existing scheduled configuration."""
        config_name = options.get('config_name')
        
        if config_name:
            try:
                config = BackupConfiguration.objects.get(name=config_name, is_enabled=True)
            except BackupConfiguration.DoesNotExist:
                raise CommandError(f"Backup configuration '{config_name}' not found or disabled")
        else:
            # Use first active configuration
            config = BackupConfiguration.objects.filter(is_enabled=True).first()
            if not config:
                raise CommandError("No active backup configurations found")
        
        self.stdout.write(f"Using backup configuration: {config.name}")
        
        # Execute backup
        job = backup_service.execute_backup(config)
        
        self.stdout.write(
            self.style.SUCCESS(f'Scheduled backup completed: {job.job_name}')
        )

    def create_adhoc_backup(self, options):
        """Create ad-hoc backup with specified options."""
        # Create temporary backup configuration
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_type = options['type'].upper()
        
        # Determine storage path
        output_path = options.get('output')
        if output_path:
            storage_path = str(Path(output_path).parent)
        else:
            storage_path = str(Path(settings.BASE_DIR).parent / 'storage' / 'backups')
        
        # Create temporary configuration
        from apps.users.models import User
        admin_user = User.objects.filter(is_staff=True).first()
        
        config = BackupConfiguration(
            name=f"adhoc_{backup_type.lower()}_{timestamp}",
            description=f"Ad-hoc {backup_type.lower()} backup created via management command",
            backup_type=backup_type,
            frequency='ON_DEMAND',
            schedule_time='12:00:00',
            storage_path=storage_path,
            compression_enabled=options.get('compress', True),
            encryption_enabled=options.get('encrypt', False),
            retention_days=7,  # Short retention for ad-hoc backups
            max_backups=5,
            created_by=admin_user if admin_user else User.objects.first()
        )
        
        # Save configuration for backup execution
        config.save()
        self.stdout.write(f"Creating {backup_type.lower()} backup...")
        
        # Execute backup
        job = backup_service.execute_backup(config)
        
        self.stdout.write(
            self.style.SUCCESS(f'Ad-hoc backup completed: {job.job_name}')
        )

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _create_checksums(self, directory: Path):
        """Create checksum file for directory contents."""
        checksums = {}
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.name != 'checksum.txt':
                rel_path = file_path.relative_to(directory)
                checksums[str(rel_path)] = self._calculate_file_checksum(file_path)
        
        checksum_file = directory / 'checksum.txt'
        with open(checksum_file, 'w') as f:
            for file_path, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {file_path}\n")

    def _get_restore_script_content(self) -> str:
        """Generate restore script content."""
        return '''#!/bin/bash
#
# EDMS Migration Package Restore Script
#
# This script restores an EDMS system from a migration package.
#
# Usage: ./restore.sh [options]
#   --target-dir /path/to/edms    Target EDMS installation directory
#   --db-host hostname            Database host (default: localhost)
#   --db-port 5432               Database port (default: 5432)
#   --db-name edms_db            Database name (default: edms_db)
#   --db-user edms_user          Database user (default: edms_user)
#   --skip-users                 Skip user account restoration
#   --verify                     Verify restoration after completion
#   --help                       Show this help message

set -e

# Default values
TARGET_DIR="/opt/edms"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="edms_db"
DB_USER="edms_user"
SKIP_USERS=false
VERIFY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target-dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        --db-host)
            DB_HOST="$2"
            shift 2
            ;;
        --db-port)
            DB_PORT="$2"
            shift 2
            ;;
        --db-name)
            DB_NAME="$2"
            shift 2
            ;;
        --db-user)
            DB_USER="$2"
            shift 2
            ;;
        --skip-users)
            SKIP_USERS=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# //g'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 EDMS Migration Package Restore"
echo "=================================="
echo ""
echo "Target Directory: $TARGET_DIR"
echo "Database Host: $DB_HOST:$DB_PORT"
echo "Database Name: $DB_NAME"
echo ""

# Check prerequisites
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client (psql) not found"
    exit 1
fi

if ! command -v pg_restore &> /dev/null; then
    echo "❌ PostgreSQL restore tool (pg_restore) not found"
    exit 1
fi

# Prompt for database password
read -s -p "Enter database password for $DB_USER: " DB_PASSWORD
echo ""
export PGPASSWORD="$DB_PASSWORD"

# Check database connectivity
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
    echo "❌ Cannot connect to database"
    exit 1
fi

echo "✓ Database connection verified"

# Restore database
echo "📊 Restoring database..."
if [ -f "database/complete.sql" ]; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "database/complete.sql"
    echo "✓ Database restored"
else
    echo "❌ Database backup file not found"
    exit 1
fi

# Restore storage files
echo "📁 Restoring storage files..."
if [ -d "$TARGET_DIR/storage" ]; then
    echo "Creating backup of existing storage..."
    mv "$TARGET_DIR/storage" "$TARGET_DIR/storage.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$TARGET_DIR/storage"
if [ -d "storage" ]; then
    cp -r storage/* "$TARGET_DIR/storage/"
    echo "✓ Storage files restored"
else
    echo "⚠️  No storage files found in package"
fi

# Restore configuration (if target directory has EDMS installation)
if [ -d "$TARGET_DIR/backend" ]; then
    echo "⚙️  Configuration restoration available"
    echo "   (Manual configuration review recommended)"
fi

echo ""
echo "✅ Restoration completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "   1. Review and update configuration files"
echo "   2. Run Django migrations: python manage.py migrate"
echo "   3. Collect static files: python manage.py collectstatic"
echo "   4. Create superuser if needed: python manage.py createsuperuser"
echo "   5. Restart application services"
if [ "$VERIFY" = true ]; then
    echo "   6. Run verification: ./verify.sh"
fi
echo ""

unset PGPASSWORD
'''

    def _get_verify_script_content(self) -> str:
        """Generate verification script content."""
        return '''#!/bin/bash
#
# EDMS Restore Verification Script
#
# This script verifies the integrity of a restored EDMS system.

set -e

echo "🔍 EDMS Restore Verification"
echo "============================"
echo ""

# Check database connectivity
echo "📊 Verifying database..."
if command -v python3 &> /dev/null; then
    # Try Django database check
    if [ -f "manage.py" ]; then
        python3 manage.py check --database default
        echo "✓ Database connectivity verified"
    else
        echo "⚠️  Django manage.py not found - manual database verification needed"
    fi
else
    echo "⚠️  Python not found - manual verification needed"
fi

# Check storage directories
echo "📁 Verifying storage structure..."
STORAGE_DIRS=("documents" "media" "certificates")
for dir in "${STORAGE_DIRS[@]}"; do
    if [ -d "storage/$dir" ]; then
        echo "✓ Storage directory exists: $dir"
    else
        echo "⚠️  Storage directory missing: $dir"
    fi
done

# Verify file checksums (if manifest exists)
if [ -f "storage/manifest.json" ]; then
    echo "🔐 Verifying file checksums..."
    # Note: This would need a Python script to properly verify JSON manifest
    echo "✓ Manifest file found (manual verification recommended)"
else
    echo "⚠️  Storage manifest not found"
fi

echo ""
echo "✅ Verification completed!"
echo ""
echo "📋 Manual Verification Steps:"
echo "   1. Test application login"
echo "   2. Verify document access"
echo "   3. Check workflow functionality"
echo "   4. Validate user permissions"
echo "   5. Test document upload/download"
echo ""
'''