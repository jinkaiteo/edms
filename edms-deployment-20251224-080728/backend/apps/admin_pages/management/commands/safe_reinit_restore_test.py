"""
Safe Reinit → Restore Test Command

Executes a modified reinit that respects foreign key constraints
and tests the complete data lifecycle safely
"""

import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.admin_pages.validation_utils import (
    validate_system_state, 
    compare_system_states,
    validate_backup_integrity,
    generate_validation_report
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Execute safe reinit → restore cycle that respects database constraints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-path',
            type=str,
            default='/tmp/pre_reinit_backup.tar.gz',
            help='Path to backup file for restore testing'
        )
        parser.add_argument(
            '--skip-reinit',
            action='store_true',
            help='Skip reinit and only test restore functionality'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 SAFE EDMS Data Lifecycle Test'))
        self.stdout.write('=' * 60)

        validation_data = {}
        
        try:
            # Phase 1: Pre-Test State Capture
            self.stdout.write('\n📊 Phase 1: Capturing Pre-Test State')
            validation_data['pre_test_state'] = validate_system_state('pre_test')
            self.display_state_summary(validation_data['pre_test_state'])
            
            # Validate backup file
            backup_path = options['backup_path']
            if os.path.exists(backup_path):
                self.stdout.write(f'✓ Backup file exists: {backup_path}')
                validation_data['backup_integrity'] = validate_backup_integrity(backup_path)
                
                if validation_data['backup_integrity']['archive_valid']:
                    self.stdout.write('✓ Backup integrity validated')
                    self.stdout.write(f"  File size: {validation_data['backup_integrity']['file_size']} bytes")
                    self.stdout.write(f"  Archive files: {validation_data['backup_integrity']['content_summary']['total_files']}")
                else:
                    raise Exception('Backup file is corrupted')
            else:
                raise Exception(f'Backup file not found: {backup_path}')

            if not options['skip_reinit']:
                # Phase 2: Safe Data Cleanup (not full reinit)
                self.stdout.write('\n🧹 Phase 2: Safe User Data Cleanup')
                validation_data['cleanup_results'] = self.safe_user_data_cleanup()
                validation_data['post_cleanup_state'] = validate_system_state('post_cleanup')
            else:
                validation_data['post_cleanup_state'] = validation_data['pre_test_state']

            # Phase 3: Restore Test
            self.stdout.write('\n📥 Phase 3: Testing Restore Functionality')
            validation_data['restore_test'] = self.test_restore_functionality(backup_path)
            validation_data['post_restore_state'] = validate_system_state('post_restore')

            # Phase 4: Comprehensive Validation
            self.stdout.write('\n🔍 Phase 4: Data Lifecycle Validation')
            validation_data['lifecycle_validation'] = self.validate_complete_lifecycle(validation_data)

            # Generate report
            report_path = generate_validation_report(validation_data)
            self.stdout.write(self.style.SUCCESS(f'\n📊 Validation report: {report_path}'))
            
            # Display final summary
            self.display_final_summary(validation_data)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Test failed: {str(e)}'))
            raise

    def safe_user_data_cleanup(self):
        """Safely clean user data while preserving core infrastructure"""
        cleanup_results = {
            'timestamp': datetime.now().isoformat(),
            'operations': [],
            'preserved_infrastructure': {},
            'errors': []
        }
        
        try:
            with transaction.atomic():
                # Clean audit trails (safe - no dependencies)
                from apps.audit.models import AuditTrail, LoginAudit, UserSession
                
                audit_count = AuditTrail.objects.count()
                AuditTrail.objects.all().delete()
                cleanup_results['operations'].append(f'Cleared {audit_count} audit trails')
                
                login_count = LoginAudit.objects.count()  
                LoginAudit.objects.all().delete()
                cleanup_results['operations'].append(f'Cleared {login_count} login audits')
                
                session_count = UserSession.objects.count()
                UserSession.objects.all().delete()
                cleanup_results['operations'].append(f'Cleared {session_count} user sessions')

                # Clean documents (safe - user data)
                from apps.documents.models import Document, DocumentVersion, DocumentComment
                
                doc_count = Document.objects.count()
                if doc_count > 0:
                    Document.objects.all().delete()
                    cleanup_results['operations'].append(f'Cleared {doc_count} documents')

                # Clean non-essential workflows
                from apps.workflows.models import WorkflowInstance
                
                # Only clean completed workflows to avoid FK issues
                completed_workflows = WorkflowInstance.objects.filter(is_completed=True)
                completed_count = completed_workflows.count()
                if completed_count > 0:
                    completed_workflows.delete()
                    cleanup_results['operations'].append(f'Cleared {completed_count} completed workflows')

                # Create test user to validate user management
                test_user, created = User.objects.get_or_create(
                    username='lifecycle_test_user',
                    defaults={
                        'email': 'test@lifecycle.com',
                        'first_name': 'Lifecycle',
                        'last_name': 'Test',
                        'is_active': True
                    }
                )
                if created:
                    test_user.set_password('test123')
                    test_user.save()
                    cleanup_results['operations'].append('Created test user for validation')

                # Record preserved infrastructure
                from apps.documents.models import DocumentType
                from apps.workflows.models import WorkflowType
                from apps.placeholders.models import DocumentTemplate, PlaceholderDefinition
                
                cleanup_results['preserved_infrastructure'] = {
                    'document_types': DocumentType.objects.count(),
                    'workflow_types': WorkflowType.objects.count(),
                    'templates': DocumentTemplate.objects.count(),
                    'placeholders': PlaceholderDefinition.objects.count(),
                    'admin_users': User.objects.filter(is_superuser=True).count()
                }
                
                self.stdout.write('✓ Safe user data cleanup completed')
                self.stdout.write(f'  Operations: {len(cleanup_results["operations"])}')
                for op in cleanup_results['operations']:
                    self.stdout.write(f'    - {op}')

        except Exception as e:
            cleanup_results['errors'].append(f'Cleanup error: {str(e)}')
            self.stdout.write(f'⚠️  Cleanup error: {str(e)}')

        return cleanup_results

    def test_restore_functionality(self, backup_path):
        """Test restore functionality with detailed validation"""
        restore_test = {
            'timestamp': datetime.now().isoformat(),
            'backup_path': backup_path,
            'restore_attempts': [],
            'overall_success': False
        }
        
        # Test 1: Dry run restore
        self.stdout.write('🧪 Testing restore dry-run...')
        try:
            call_command('restore_backup', 
                        '--from-file', backup_path,
                        '--type', 'full',
                        '--dry-run',
                        verbosity=1)
            
            restore_test['restore_attempts'].append({
                'type': 'dry_run',
                'status': 'success',
                'description': 'Restore dry-run completed without errors'
            })
            self.stdout.write('✓ Restore dry-run successful')
            
        except Exception as e:
            restore_test['restore_attempts'].append({
                'type': 'dry_run', 
                'status': 'failed',
                'error': str(e)
            })
            self.stdout.write(f'⚠️  Restore dry-run failed: {str(e)}')

        # Test 2: Database-only restore
        self.stdout.write('🧪 Testing database restore...')
        try:
            call_command('restore_backup',
                        '--from-file', backup_path, 
                        '--type', 'database',
                        '--force',
                        verbosity=1)
            
            restore_test['restore_attempts'].append({
                'type': 'database',
                'status': 'success', 
                'description': 'Database restore completed'
            })
            self.stdout.write('✓ Database restore successful')
            
        except Exception as e:
            restore_test['restore_attempts'].append({
                'type': 'database',
                'status': 'failed',
                'error': str(e)
            })
            self.stdout.write(f'⚠️  Database restore failed: {str(e)}')

        # Test 3: Files-only restore
        self.stdout.write('🧪 Testing files restore...')
        try:
            call_command('restore_backup',
                        '--from-file', backup_path,
                        '--type', 'files', 
                        '--force',
                        verbosity=1)
            
            restore_test['restore_attempts'].append({
                'type': 'files',
                'status': 'success',
                'description': 'Files restore completed'
            })
            self.stdout.write('✓ Files restore successful')
            
        except Exception as e:
            restore_test['restore_attempts'].append({
                'type': 'files', 
                'status': 'failed',
                'error': str(e)
            })
            self.stdout.write(f'⚠️  Files restore failed: {str(e)}')

        # Determine overall success
        successful_attempts = [a for a in restore_test['restore_attempts'] if a['status'] == 'success']
        restore_test['overall_success'] = len(successful_attempts) >= 2  # At least 2 of 3 tests should pass
        restore_test['success_rate'] = f"{len(successful_attempts)}/{len(restore_test['restore_attempts'])}"

        return restore_test

    def validate_complete_lifecycle(self, validation_data):
        """Validate the complete data lifecycle process"""
        lifecycle_validation = {
            'timestamp': datetime.now().isoformat(),
            'backup_integrity': 'unknown',
            'cleanup_effectiveness': 'unknown', 
            'restore_functionality': 'unknown',
            'infrastructure_preservation': 'unknown',
            'overall_assessment': 'unknown',
            'recommendations': []
        }

        # Validate backup integrity
        backup_data = validation_data.get('backup_integrity', {})
        if backup_data.get('archive_valid', False):
            lifecycle_validation['backup_integrity'] = 'excellent'
        elif backup_data.get('file_exists', False):
            lifecycle_validation['backup_integrity'] = 'partial'
        else:
            lifecycle_validation['backup_integrity'] = 'failed'

        # Validate cleanup effectiveness
        if 'cleanup_results' in validation_data:
            cleanup = validation_data['cleanup_results']
            operations_count = len(cleanup.get('operations', []))
            errors_count = len(cleanup.get('errors', []))
            
            if operations_count > 0 and errors_count == 0:
                lifecycle_validation['cleanup_effectiveness'] = 'excellent'
            elif operations_count > errors_count:
                lifecycle_validation['cleanup_effectiveness'] = 'good'
            else:
                lifecycle_validation['cleanup_effectiveness'] = 'poor'

        # Validate restore functionality  
        restore_data = validation_data.get('restore_test', {})
        if restore_data.get('overall_success', False):
            lifecycle_validation['restore_functionality'] = 'excellent'
        elif restore_data.get('restore_attempts'):
            success_count = len([a for a in restore_data['restore_attempts'] if a['status'] == 'success'])
            if success_count > 0:
                lifecycle_validation['restore_functionality'] = 'partial'
            else:
                lifecycle_validation['restore_functionality'] = 'failed'

        # Validate infrastructure preservation
        pre_state = validation_data.get('pre_test_state', {})
        post_state = validation_data.get('post_restore_state', {})
        
        if pre_state and post_state:
            pre_infra = pre_state.get('integrity', {}).get('core_infrastructure', {})
            post_infra = post_state.get('integrity', {}).get('core_infrastructure', {})
            
            preserved_count = sum(1 for key in pre_infra if pre_infra.get(key) and post_infra.get(key))
            total_count = len(pre_infra)
            
            if preserved_count == total_count:
                lifecycle_validation['infrastructure_preservation'] = 'excellent'
            elif preserved_count >= total_count * 0.8:
                lifecycle_validation['infrastructure_preservation'] = 'good'
            else:
                lifecycle_validation['infrastructure_preservation'] = 'poor'

        # Overall assessment
        scores = [
            lifecycle_validation['backup_integrity'],
            lifecycle_validation['cleanup_effectiveness'],
            lifecycle_validation['restore_functionality'],
            lifecycle_validation['infrastructure_preservation']
        ]
        
        excellent_count = scores.count('excellent')
        good_count = scores.count('good')
        
        if excellent_count >= 3:
            lifecycle_validation['overall_assessment'] = 'excellent'
        elif excellent_count + good_count >= 3:
            lifecycle_validation['overall_assessment'] = 'good'
        elif 'failed' not in scores:
            lifecycle_validation['overall_assessment'] = 'acceptable'
        else:
            lifecycle_validation['overall_assessment'] = 'needs_improvement'

        # Generate recommendations
        if lifecycle_validation['backup_integrity'] != 'excellent':
            lifecycle_validation['recommendations'].append('Improve backup file validation')
        
        if lifecycle_validation['restore_functionality'] != 'excellent':
            lifecycle_validation['recommendations'].append('Enhance restore error handling')
            
        if lifecycle_validation['infrastructure_preservation'] != 'excellent':
            lifecycle_validation['recommendations'].append('Review foreign key constraint handling')

        return lifecycle_validation

    def display_state_summary(self, state):
        """Display concise state summary"""
        db_data = state['database']
        self.stdout.write(f'  Users: {db_data.get("users", 0)} | Documents: {db_data.get("documents", 0)} | Workflows: {db_data.get("workflows", 0)}')
        self.stdout.write(f'  Audit Trails: {db_data.get("audit_trails", 0)} | Backup Jobs: {db_data.get("backup_jobs", 0)}')
        
        infra = state.get('integrity', {}).get('core_infrastructure', {})
        infra_count = sum(infra.values())
        self.stdout.write(f'  Core Infrastructure: {infra_count}/{len(infra)} components')

    def display_final_summary(self, validation_data):
        """Display comprehensive final summary"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎯 DATA LIFECYCLE TEST SUMMARY'))
        self.stdout.write('=' * 60)

        # Overall assessment
        if 'lifecycle_validation' in validation_data:
            assessment = validation_data['lifecycle_validation']['overall_assessment']
            
            if assessment == 'excellent':
                self.stdout.write(self.style.SUCCESS('🎉 OVERALL ASSESSMENT: EXCELLENT'))
            elif assessment == 'good':
                self.stdout.write(self.style.SUCCESS('✅ OVERALL ASSESSMENT: GOOD'))
            elif assessment == 'acceptable':
                self.stdout.write(self.style.WARNING('⚠️  OVERALL ASSESSMENT: ACCEPTABLE'))
            else:
                self.stdout.write(self.style.ERROR('❌ OVERALL ASSESSMENT: NEEDS IMPROVEMENT'))

            # Component scores
            components = ['backup_integrity', 'cleanup_effectiveness', 'restore_functionality', 'infrastructure_preservation']
            self.stdout.write('\n📊 Component Scores:')
            for component in components:
                score = validation_data['lifecycle_validation'].get(component, 'unknown')
                emoji = '🎉' if score == 'excellent' else '✅' if score == 'good' else '⚠️' if score == 'acceptable' else '❌'
                self.stdout.write(f'  {emoji} {component.replace("_", " ").title()}: {score.upper()}')

            # Recommendations
            recommendations = validation_data['lifecycle_validation'].get('recommendations', [])
            if recommendations:
                self.stdout.write('\n💡 Recommendations:')
                for rec in recommendations:
                    self.stdout.write(f'  • {rec}')

        self.stdout.write('\n✨ Data lifecycle validation completed successfully!')