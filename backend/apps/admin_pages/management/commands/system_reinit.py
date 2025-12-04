"""
EDMS System Reinit Management Command

This command performs a complete system reset by:
1. Removing all user data (documents, audit trails, workflows)
2. Clearing file storage directories
3. Resetting database to initial state
4. Creating fresh superuser account (admin/test123)
5. Maintaining system configurations and templates

WARNING: This is a DESTRUCTIVE operation that cannot be undone!
Use only for development, testing, or complete system reset scenarios.
"""

import os
import shutil
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

# Import all models that need to be reset
from apps.users.models import User, Role, UserRole, MFADevice
from apps.documents.models import (
    Document, DocumentVersion, DocumentDependency, DocumentAccessLog, 
    DocumentComment, DocumentAttachment, DocumentType
)
from apps.workflows.models import (
    WorkflowInstance, WorkflowTransition, WorkflowRule, WorkflowNotification,
    DocumentWorkflow, DocumentTransition, WorkflowType
)
from apps.audit.models import (
    AuditTrail, SystemEvent, LoginAudit, UserSession, DatabaseChangeLog,
    ComplianceEvent, AuditEvent
)
from apps.backup.models import BackupJob, RestoreJob, BackupConfiguration
from apps.scheduler.models import ScheduledTask  # Handle carefully due to table issues
from apps.security.models import PDFGenerationLog, DigitalSignature, SecurityEvent
from apps.placeholders.models import DocumentTemplate, TemplatePlaceholder, DocumentGeneration, PlaceholderCache, PlaceholderDefinition

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Completely reset the EDMS system to initial state (DESTRUCTIVE OPERATION)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the destructive operation (required for execution)'
        )
        parser.add_argument(
            '--preserve-backups',
            action='store_true',
            help='Keep existing backup files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually doing it'
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        preserve_templates = True  # Always preserve templates and placeholders - they are core system infrastructure
        preserve_backups = options['preserve_backups']
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING('🚨 EDMS SYSTEM REINIT OPERATION'))
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('🔍 DRY RUN MODE - No changes will be made'))
        
        # Safety check
        if not confirm and not dry_run:
            self.stdout.write(self.style.ERROR('❌ DESTRUCTIVE OPERATION REQUIRES --confirm FLAG'))
            self.stdout.write('This will DELETE ALL:')
            self.stdout.write('  - User accounts (except new admin)')
            self.stdout.write('  - Documents and files')
            self.stdout.write('  - Audit trails and logs')
            self.stdout.write('  - Workflows and processes')
            self.stdout.write('  - System activity history')
            self.stdout.write('')
            self.stdout.write('Use: python manage.py system_reinit --confirm')
            return

        # Display current system state
        self.display_current_state()

        if not dry_run:
            # Final confirmation for non-dry-run
            self.stdout.write(self.style.ERROR('\n⚠️  FINAL WARNING: This operation CANNOT be undone!'))
            confirm_text = input('Type "RESET SYSTEM" to proceed: ')
            if confirm_text != "RESET SYSTEM":
                self.stdout.write('Operation cancelled.')
                return

        # Execute reset operations
        try:
            with transaction.atomic():
                if dry_run:
                    self.stdout.write('\n🔍 DRY RUN - Operations that would be performed:')
                    self.display_reset_plan(preserve_templates, preserve_backups)
                else:
                    self.stdout.write('\n🔄 Executing system reset...')
                    self.execute_system_reset(preserve_templates, preserve_backups)
                    self.stdout.write(self.style.SUCCESS('\n✅ System reset completed successfully!'))
                    self.display_final_state()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ System reset failed: {str(e)}'))
            logger.error(f'System reset failed: {str(e)}', exc_info=True)
            raise CommandError(f'System reset failed: {str(e)}')

    def display_current_state(self):
        """Display current system state before reset."""
        self.stdout.write('\n📊 CURRENT SYSTEM STATE:')
        self.stdout.write('-' * 40)
        
        try:
            self.stdout.write(f'Users: {User.objects.count()}')
            self.stdout.write(f'Documents: {Document.objects.count()}')
            self.stdout.write(f'Document Versions: {DocumentVersion.objects.count()}')
            self.stdout.write(f'Workflows: {WorkflowInstance.objects.count()}')
            self.stdout.write(f'Audit Trails: {AuditTrail.objects.count()}')
            self.stdout.write(f'Backup Jobs: {BackupJob.objects.count()}')
            
            # File system analysis
            self.stdout.write('\n📁 File Storage:')
            storage_locations = [
                '/app/storage/documents',
                '/app/storage/media', 
                '/storage/backups',
                '/opt/edms/backups'
            ]
            
            for location in storage_locations:
                if os.path.exists(location):
                    files = len([f for f in os.listdir(location) 
                               if os.path.isfile(os.path.join(location, f))])
                    self.stdout.write(f'  {location}: {files} files')
                else:
                    self.stdout.write(f'  {location}: Not found')
                    
        except Exception as e:
            self.stdout.write(f'Error analyzing current state: {str(e)}')

    def display_reset_plan(self, preserve_templates, preserve_backups):
        """Display what would be reset in dry run mode."""
        self.stdout.write('\n📋 RESET PLAN:')
        self.stdout.write('-' * 30)
        
        self.stdout.write('🗑️  DATABASE TABLES TO CLEAR:')
        self.stdout.write('  - All user accounts (new admin will be created)')
        self.stdout.write('  - All documents and versions')
        self.stdout.write('  - All workflows and instances')
        self.stdout.write('  - All audit trails and logs')
        self.stdout.write('  - All backup/restore jobs')
        
        self.stdout.write('  ✅ Document templates and placeholders (core system - always preserved)')
            
        self.stdout.write('\n🗂️  FILE DIRECTORIES TO CLEAR:')
        self.stdout.write('  - /app/storage/documents (all user documents)')
        self.stdout.write('  - /app/storage/media (all media files)')
        
        if not preserve_backups:
            self.stdout.write('  - /storage/backups (backup files)')
            self.stdout.write('  - /opt/edms/backups (backup files)')
        else:
            self.stdout.write('  ✅ Backup files (preserved)')
            
        self.stdout.write('\n👤 SUPERUSER TO CREATE:')
        self.stdout.write('  - Username: admin')
        self.stdout.write('  - Password: test123')
        self.stdout.write('  - Email: admin@edms.local')
        self.stdout.write('  - Staff: True, Superuser: True')

    def execute_system_reset(self, preserve_templates, preserve_backups):
        """Execute the actual system reset."""
        self.stdout.write('Phase 1: Clearing database records...')
        self.clear_database_records(preserve_templates)
        
        self.stdout.write('Phase 2: Clearing file storage...')
        self.clear_file_storage(preserve_backups)
        
        self.stdout.write('Phase 3: Creating superuser...')
        self.create_superuser()
        
        self.stdout.write('Phase 4: Initializing core system data...')
        self.initialize_core_data()

    def clear_database_records(self, preserve_templates):
        """Clear all user data from database tables."""
        # Order matters - delete dependent objects first
        
        # STEP 1: Clear workflow dependencies first (proper cascade order)
        try:
            # Try to clear workflow tasks if the model exists
            # Note: WorkflowTask may not exist in current schema
            WorkflowNotification.objects.all().delete()
            self.stdout.write('  ✅ Workflow notifications cleared first')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Workflow dependencies cleanup warning: {str(e)}')
            
        # STEP 2: Clear workflow-related objects in proper order
        try:
            DocumentTransition.objects.all().delete()
            DocumentWorkflow.objects.all().delete()
            WorkflowInstance.objects.all().delete()
            self.stdout.write('  ✅ Workflows cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Workflow cleanup warning: {str(e)}')

        # Document related
        try:
            DocumentAccessLog.objects.all().delete()
            DocumentComment.objects.all().delete()
            DocumentAttachment.objects.all().delete()
            DocumentDependency.objects.all().delete()
            DocumentVersion.objects.all().delete()
            Document.objects.all().delete()
            self.stdout.write('  ✅ Documents cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Document cleanup warning: {str(e)}')

        # Audit and logging
        try:
            ComplianceEvent.objects.all().delete()
            DatabaseChangeLog.objects.all().delete()
            UserSession.objects.all().delete()
            LoginAudit.objects.all().delete()
            SystemEvent.objects.all().delete()
            AuditTrail.objects.all().delete()
            self.stdout.write('  ✅ Audit trails cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Audit cleanup warning: {str(e)}')

        # Backup and restore
        try:
            RestoreJob.objects.all().delete()
            BackupJob.objects.all().delete()
            # Keep BackupConfiguration for future use
            self.stdout.write('  ✅ Backup jobs cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Backup cleanup warning: {str(e)}')

        # Security logs
        try:
            SecurityEvent.objects.all().delete()
            DigitalSignature.objects.all().delete()
            PDFGenerationLog.objects.all().delete()
            self.stdout.write('  ✅ Security logs cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Security cleanup warning: {str(e)}')

        # Templates (conditional)
        if not preserve_templates:
            try:
                PlaceholderCache.objects.all().delete()
                DocumentGeneration.objects.all().delete()
                TemplatePlaceholder.objects.all().delete()
                DocumentTemplate.objects.all().delete()
                self.stdout.write('  ✅ Templates cleared')
            except Exception as e:
                self.stdout.write(f'  ⚠️  Template cleanup warning: {str(e)}')

        # Scheduler (handle carefully due to potential table issues)
        try:
            # Only clear if table exists
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'scheduler_scheduledtask'
                    );
                """)
                if cursor.fetchone()[0]:
                    ScheduledTask.objects.all().delete()
                    self.stdout.write('  ✅ Scheduled tasks cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Scheduler cleanup warning: {str(e)}')

        # STEP 9: Clear user-related objects first
        try:
            UserRole.objects.all().delete()
            MFADevice.objects.all().delete()
            self.stdout.write('  ✅ User roles and MFA devices cleared')
        except Exception as e:
            self.stdout.write(f'  ⚠️  User roles cleanup warning: {str(e)}')

        # STEP 10: Handle core infrastructure FK references before deleting users
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Create system admin to preserve FK references
            system_admin, created = User.objects.get_or_create(
                username='system_admin_temp',
                defaults={
                    'email': 'system@edms.local',
                    'is_staff': True,
                    'is_superuser': True,
                    'first_name': 'System',
                    'last_name': 'Administrator'
                }
            )
            
            # Update all core infrastructure to reference system admin
            DocumentType.objects.all().update(created_by=system_admin)
            WorkflowType.objects.all().update(created_by=system_admin) 
            PlaceholderDefinition.objects.all().update(created_by=system_admin)
            
            try:
                BackupConfiguration.objects.filter(created_by__isnull=False).update(created_by=system_admin)
            except:
                pass  # BackupConfiguration might not have created_by field
                
            self.stdout.write('  ✅ Core infrastructure references updated to system admin')
        except Exception as e:
            self.stdout.write(f'  ⚠️  Infrastructure reference update warning: {str(e)}')

        # STEP 11: Delete all users except system admin
        try:
            User = get_user_model()
            deleted_count = User.objects.exclude(username='system_admin_temp').count()
            User.objects.exclude(username='system_admin_temp').delete()
            self.stdout.write(f'  ✅ Users cleared ({deleted_count} users deleted, core infrastructure preserved)')
        except Exception as e:
            self.stdout.write(f'  ⚠️  User deletion warning: {str(e)}')

    def clear_file_storage(self, preserve_backups):
        """Clear file storage directories."""
        storage_dirs = [
            '/app/storage/documents',
            '/app/storage/media'
        ]
        
        if not preserve_backups:
            storage_dirs.extend([
                '/storage/backups',
                '/opt/edms/backups'
            ])

        for storage_dir in storage_dirs:
            try:
                if os.path.exists(storage_dir):
                    # Clear contents but keep directory structure
                    for item in os.listdir(storage_dir):
                        item_path = os.path.join(storage_dir, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    self.stdout.write(f'  ✅ Cleared {storage_dir}')
                else:
                    # Create directory if it doesn't exist
                    os.makedirs(storage_dir, exist_ok=True)
                    self.stdout.write(f'  ✅ Created {storage_dir}')
            except Exception as e:
                self.stdout.write(f'  ⚠️  Error clearing {storage_dir}: {str(e)}')

    def create_superuser(self):
        """Create or update the admin superuser account."""
        try:
            User = get_user_model()
            
            # Remove temporary system admin if it exists
            User.objects.filter(username='system_admin_temp').delete()
            
            # Get or create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@edms.local',
                    'is_staff': True,
                    'is_superuser': True,
                    'first_name': 'System',
                    'last_name': 'Administrator'
                }
            )
            
            if not created:
                # Update existing admin user
                admin_user.email = 'admin@edms.local'
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.first_name = 'System'
                admin_user.last_name = 'Administrator'
                admin_user.save()
                
            # Set password
            admin_user.set_password('test123')
            admin_user.save()
            
            # Update core infrastructure to reference the admin user
            DocumentType.objects.all().update(created_by=admin_user)
            WorkflowType.objects.all().update(created_by=admin_user) 
            PlaceholderDefinition.objects.all().update(created_by=admin_user)
            
            try:
                BackupConfiguration.objects.filter(created_by__isnull=False).update(created_by=admin_user)
            except:
                pass  # BackupConfiguration might not have created_by field
            
            action = 'created' if created else 'updated'
            self.stdout.write(f'  ✅ Superuser {action}: {admin_user.username}')
            self.stdout.write(f'  📧 Email: {admin_user.email}')
            self.stdout.write(f'  🔑 Password: test123')
            self.stdout.write(f'  🛡️ Core infrastructure references updated')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Error with superuser: {str(e)}')
            raise

    def initialize_core_data(self):
        """Initialize essential system data."""
        try:
            # Set up basic system configurations if needed
            from django.core.management import call_command
            
            # Initialize placeholders if they don't exist
            try:
                call_command('setup_placeholders', verbosity=0)
                self.stdout.write('  ✅ Core placeholders initialized')
            except Exception as e:
                self.stdout.write(f'  ⚠️  Placeholder setup warning: {str(e)}')

        except Exception as e:
            self.stdout.write(f'  ⚠️  Core data initialization warning: {str(e)}')

    def display_final_state(self):
        """Display system state after reset."""
        self.stdout.write('\n📊 FINAL SYSTEM STATE:')
        self.stdout.write('-' * 40)
        
        try:
            self.stdout.write(f'Users: {User.objects.count()}')
            self.stdout.write(f'Documents: {Document.objects.count()}')
            self.stdout.write(f'Workflows: {WorkflowInstance.objects.count()}')
            self.stdout.write(f'Audit Trails: {AuditTrail.objects.count()}')
            
            # Display superuser info
            admin_user = User.objects.filter(username='admin').first()
            if admin_user:
                self.stdout.write(f'\n👤 ADMIN ACCOUNT:')
                self.stdout.write(f'  Username: {admin_user.username}')
                self.stdout.write(f'  Email: {admin_user.email}')
                self.stdout.write(f'  Password: test123')
                self.stdout.write(f'  Superuser: {admin_user.is_superuser}')
                self.stdout.write(f'  Staff: {admin_user.is_staff}')

            self.stdout.write('\n🎯 SYSTEM READY FOR:')
            self.stdout.write('  - Fresh user registration')
            self.stdout.write('  - Document upload and management') 
            self.stdout.write('  - Workflow configuration')
            self.stdout.write('  - Development and testing')

        except Exception as e:
            self.stdout.write(f'Error analyzing final state: {str(e)}')