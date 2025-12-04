"""
EDMS Data Lifecycle Validation Command

Executes complete reinit → restore cycle with comprehensive validation
"""

import os
import json
import shutil
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

# Import validation functions
from apps.admin_pages.validation_utils import (
    validate_system_state, 
    compare_system_states,
    create_test_data,
    validate_backup_integrity,
    generate_validation_report
)


class Command(BaseCommand):
    help = 'Execute complete reinit → restore cycle with detailed validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full-cycle',
            action='store_true',
            help='Execute the full reinit → restore cycle'
        )
        parser.add_argument(
            '--validation-only',
            action='store_true', 
            help='Only run system validation without reinit/restore'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test data before validation'
        )
        parser.add_argument(
            '--backup-path',
            type=str,
            default='/tmp/pre_reinit_backup.tar.gz',
            help='Path to backup file for restore testing'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 EDMS Data Lifecycle Validation'))
        self.stdout.write('=' * 60)

        # Storage for all validation data
        validation_data = {}
        
        try:
            if options['validation_only']:
                # Just run system validation
                validation_data['current_state'] = self.validate_current_state()
                
            elif options['full_cycle']:
                # Execute complete cycle
                validation_data = self.execute_full_cycle(options['backup_path'])
                
            else:
                # Default: prepare for cycle
                if options['create_test_data']:
                    self.create_test_data()
                validation_data['pre_cycle_state'] = self.validate_current_state()
                self.stdout.write(self.style.WARNING('Use --full-cycle to execute reinit → restore'))

            # Generate comprehensive report
            report_path = generate_validation_report(validation_data)
            self.stdout.write(self.style.SUCCESS(f'📊 Validation report: {report_path}'))
            
            # Display summary
            self.display_validation_summary(validation_data)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Validation failed: {str(e)}'))
            raise

    def execute_full_cycle(self, backup_path):
        """Execute complete reinit → restore cycle with validation"""
        validation_data = {}
        
        self.stdout.write(self.style.WARNING('\n🚀 EXECUTING COMPLETE DATA LIFECYCLE CYCLE'))
        self.stdout.write('=' * 50)
        
        # Phase 1: Pre-Reinit State Capture
        self.stdout.write('\n📊 Phase 1: Capturing Pre-Reinit State')
        validation_data['pre_reinit_state'] = validate_system_state('pre_reinit')
        
        # Validate existing backup
        if os.path.exists(backup_path):
            self.stdout.write(f'✓ Backup file exists: {backup_path}')
            validation_data['backup_integrity'] = validate_backup_integrity(backup_path)
            
            if validation_data['backup_integrity']['archive_valid']:
                self.stdout.write('✓ Backup integrity validated')
            else:
                raise Exception('Backup file is corrupted - cannot proceed')
        else:
            raise Exception(f'Backup file not found: {backup_path}')

        # Phase 2: System Reinit
        self.stdout.write('\n🔄 Phase 2: Executing System Reinit')
        self.stdout.write('⚠️  This will clear all user data!')
        
        # Execute reinit command - need to bypass interactive confirmation
        # We'll create a custom non-interactive version
        self.execute_reinit_non_interactive()
        self.stdout.write('✓ System reinit completed')
        
        # Capture post-reinit state
        validation_data['post_reinit_state'] = validate_system_state('post_reinit')
        
        # Validate reinit results
        expected_reinit_changes = {
            'users_reset_to_admin_only': True,
            'audit_trails_cleared': True,
            'core_infrastructure_preserved': True
        }
        
        validation_data['reinit_validation'] = compare_system_states(
            validation_data['pre_reinit_state'],
            validation_data['post_reinit_state'], 
            expected_reinit_changes
        )

        # Phase 3: System Restore
        self.stdout.write('\n📥 Phase 3: Executing System Restore')
        
        try:
            # Execute restore command
            call_command('restore_backup', 
                        '--from-file', backup_path,
                        '--type', 'full',
                        '--force',
                        verbosity=1)
            self.stdout.write('✓ System restore completed')
            
        except Exception as e:
            self.stdout.write(f'⚠️  Restore command error: {str(e)}')
            # Continue with validation even if restore has issues
        
        # Capture post-restore state
        validation_data['post_restore_state'] = validate_system_state('post_restore')
        
        # Validate restore results
        validation_data['restore_validation'] = compare_system_states(
            validation_data['post_reinit_state'],
            validation_data['post_restore_state']
        )

        # Phase 4: Final Integrity Check
        self.stdout.write('\n🔍 Phase 4: Final Integrity Validation')
        validation_data['final_integrity_check'] = self.comprehensive_integrity_check()
        
        return validation_data

    def execute_reinit_non_interactive(self):
        """Execute system reinit without interactive prompts"""
        from apps.admin_pages.management.commands.system_reinit import Command as ReinitCommand
        
        # Create reinit command instance
        reinit_cmd = ReinitCommand()
        
        # Execute the reset operations directly without prompts
        try:
            reinit_cmd.execute_system_reset(preserve_templates=True, preserve_backups=True)
            self.stdout.write('✓ Non-interactive system reinit completed')
        except Exception as e:
            self.stdout.write(f'⚠️  Reinit error: {str(e)}')
            raise

    def validate_current_state(self):
        """Validate current system state"""
        self.stdout.write('📊 Validating current system state...')
        state = validate_system_state('current')
        
        # Display key metrics
        db_data = state['database']
        self.stdout.write(f'  Users: {db_data.get("users", 0)}')
        self.stdout.write(f'  Documents: {db_data.get("documents", 0)}') 
        self.stdout.write(f'  Workflows: {db_data.get("workflows", 0)}')
        self.stdout.write(f'  Audit Trails: {db_data.get("audit_trails", 0)}')
        self.stdout.write(f'  Backup Jobs: {db_data.get("backup_jobs", 0)}')
        
        # Check core infrastructure
        infra = state.get('integrity', {}).get('core_infrastructure', {})
        self.stdout.write(f'  Core Infrastructure: {sum(infra.values())}/{len(infra)} components present')
        
        return state

    def create_test_data(self):
        """Create test data for validation"""
        self.stdout.write('🧪 Creating test data...')
        success = create_test_data()
        if success:
            self.stdout.write('✓ Test data created')
        else:
            self.stdout.write('⚠️  Test data creation had issues')

    def comprehensive_integrity_check(self):
        """Perform comprehensive integrity validation"""
        self.stdout.write('🔍 Running comprehensive integrity checks...')
        
        integrity_results = {
            'timestamp': datetime.now().isoformat(),
            'database_consistency': {},
            'foreign_key_integrity': {},
            'core_infrastructure': {},
            'file_system': {},
            'overall_status': 'UNKNOWN'
        }
        
        try:
            # Database consistency checks
            from django.core.management import call_command
            from io import StringIO
            
            # Run Django's check command
            check_output = StringIO()
            try:
                call_command('check', stdout=check_output, verbosity=0)
                integrity_results['database_consistency']['django_check'] = 'PASSED'
            except Exception as e:
                integrity_results['database_consistency']['django_check'] = f'FAILED: {str(e)}'

            # Foreign key integrity
            from apps.users.models import User
            from apps.documents.models import DocumentType
            from apps.workflows.models import WorkflowType
            
            # Check that core types have valid created_by references
            orphaned_types = 0
            for model in [DocumentType, WorkflowType]:
                orphaned = model.objects.filter(created_by__isnull=True).count()
                orphaned_types += orphaned
            
            integrity_results['foreign_key_integrity'] = {
                'orphaned_core_types': orphaned_types,
                'status': 'CLEAN' if orphaned_types == 0 else 'ISSUES_FOUND'
            }

            # Core infrastructure presence
            from apps.placeholders.models import DocumentTemplate, PlaceholderDefinition
            
            core_counts = {
                'document_types': DocumentType.objects.count(),
                'workflow_types': WorkflowType.objects.count(), 
                'templates': DocumentTemplate.objects.count(),
                'placeholders': PlaceholderDefinition.objects.count()
            }
            
            integrity_results['core_infrastructure'] = {
                'counts': core_counts,
                'all_present': all(count > 0 for count in core_counts.values())
            }

            # File system checks
            storage_paths = ['/app/storage/documents', '/app/storage/media']
            fs_status = {}
            for path in storage_paths:
                fs_status[path] = {
                    'exists': os.path.exists(path),
                    'writable': os.access(path, os.W_OK) if os.path.exists(path) else False
                }
            
            integrity_results['file_system'] = fs_status

            # Overall status determination
            issues = []
            if integrity_results['database_consistency']['django_check'] != 'PASSED':
                issues.append('Database consistency issues')
            if orphaned_types > 0:
                issues.append('Foreign key integrity issues')
            if not integrity_results['core_infrastructure']['all_present']:
                issues.append('Missing core infrastructure')
            
            if not issues:
                integrity_results['overall_status'] = 'HEALTHY'
                self.stdout.write('✅ All integrity checks passed')
            else:
                integrity_results['overall_status'] = 'ISSUES_FOUND'
                self.stdout.write(f'⚠️  Issues found: {", ".join(issues)}')

        except Exception as e:
            integrity_results['overall_status'] = 'ERROR'
            integrity_results['error'] = str(e)
            self.stdout.write(f'❌ Integrity check failed: {str(e)}')

        return integrity_results

    def display_validation_summary(self, validation_data):
        """Display comprehensive validation summary"""
        self.stdout.write('\n📋 VALIDATION SUMMARY')
        self.stdout.write('=' * 40)
        
        # Count phases and issues
        phases = [k for k in validation_data.keys() if isinstance(validation_data[k], dict) and 'phase' in validation_data[k]]
        total_errors = sum(len(v.get('errors', [])) for v in validation_data.values() if isinstance(v, dict))
        
        self.stdout.write(f'Validation Phases: {len(phases)}')
        self.stdout.write(f'Total Errors: {total_errors}')
        
        # Display key findings
        for phase_key, data in validation_data.items():
            if isinstance(data, dict):
                if 'phase' in data:
                    errors = len(data.get('errors', []))
                    status = '✅' if errors == 0 else f'⚠️  ({errors} errors)'
                    self.stdout.write(f'  {data["phase"]}: {status}')
                
                elif 'validation_passed' in data:
                    status = '✅' if data['validation_passed'] else '❌'
                    self.stdout.write(f'  {phase_key}: {status}')
        
        # Overall assessment
        if total_errors == 0:
            self.stdout.write(self.style.SUCCESS('\n🎉 DATA LIFECYCLE VALIDATION: SUCCESSFUL'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️  DATA LIFECYCLE VALIDATION: {total_errors} issues found'))
            
        self.stdout.write('\n💡 Use validation report for detailed analysis')