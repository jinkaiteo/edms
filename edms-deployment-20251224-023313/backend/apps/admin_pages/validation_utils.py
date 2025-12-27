"""
EDMS Data Integrity Validation Utilities
Comprehensive validation suite for backup/restore/reinit operations
"""

import os
import json
import hashlib
from datetime import datetime
from django.utils import timezone


def validate_system_state(phase_name="Unknown"):
    """
    Comprehensive system state validation
    Returns detailed state information for comparison
    """
    validation_results = {
        'phase': phase_name,
        'timestamp': datetime.now().isoformat(),
        'database': {},
        'filesystem': {},
        'integrity': {},
        'errors': []
    }
    
    try:
        # Database validation
        from apps.users.models import User
        from apps.documents.models import Document, DocumentVersion, DocumentType
        from apps.workflows.models import WorkflowInstance, WorkflowType
        from apps.audit.models import AuditTrail
        from apps.backup.models import BackupJob, BackupConfiguration
        from apps.placeholders.models import DocumentTemplate, PlaceholderDefinition
        
        # Core data counts
        validation_results['database'] = {
            'users': User.objects.count(),
            'documents': Document.objects.count(),
            'document_versions': DocumentVersion.objects.count(),
            'workflows': WorkflowInstance.objects.count(),
            'audit_trails': AuditTrail.objects.count(),
            'backup_jobs': BackupJob.objects.count(),
            'backup_configurations': BackupConfiguration.objects.count(),
            'document_types': DocumentType.objects.count(),
            'workflow_types': WorkflowType.objects.count(),
            'document_templates': DocumentTemplate.objects.count(),
            'placeholder_definitions': PlaceholderDefinition.objects.count()
        }
        
        # Core infrastructure validation (should be preserved)
        core_infrastructure = {
            'document_types_present': DocumentType.objects.exists(),
            'workflow_types_present': WorkflowType.objects.exists(),
            'templates_present': DocumentTemplate.objects.exists(),
            'placeholders_present': PlaceholderDefinition.objects.exists()
        }
        validation_results['integrity']['core_infrastructure'] = core_infrastructure
        
        # Admin user validation
        admin_users = User.objects.filter(is_superuser=True)
        validation_results['integrity']['admin_users'] = {
            'count': admin_users.count(),
            'usernames': [u.username for u in admin_users],
            'admin_exists': admin_users.filter(username='admin').exists()
        }
        
        # Sample user data for detailed comparison
        sample_users = User.objects.all()[:10]
        validation_results['database']['sample_users'] = [
            {
                'username': u.username,
                'email': u.email,
                'is_staff': u.is_staff,
                'is_superuser': u.is_superuser,
                'is_active': u.is_active
            } for u in sample_users
        ]
        
    except Exception as e:
        validation_results['errors'].append(f"Database validation error: {str(e)}")
    
    try:
        # Filesystem validation
        storage_paths = [
            '/app/storage/documents',
            '/app/storage/media',
            '/storage/backups',
            '/opt/edms/backups'
        ]
        
        filesystem_data = {}
        for path in storage_paths:
            if os.path.exists(path):
                files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                total_size = sum(os.path.getsize(os.path.join(path, f)) for f in files if os.path.exists(os.path.join(path, f)))
                filesystem_data[path] = {
                    'exists': True,
                    'file_count': len(files),
                    'total_size': total_size,
                    'files': files[:10]  # Sample of files
                }
            else:
                filesystem_data[path] = {'exists': False}
        
        validation_results['filesystem'] = filesystem_data
        
    except Exception as e:
        validation_results['errors'].append(f"Filesystem validation error: {str(e)}")
    
    return validation_results


def compare_system_states(before_state, after_state, expected_changes=None):
    """
    Compare two system states and validate expected changes
    """
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'phases_compared': f"{before_state['phase']} -> {after_state['phase']}",
        'database_changes': {},
        'filesystem_changes': {},
        'integrity_check': {},
        'validation_passed': True,
        'issues': []
    }
    
    # Compare database counts
    for key in before_state['database']:
        before_count = before_state['database'].get(key, 0)
        after_count = after_state['database'].get(key, 0)
        change = after_count - before_count
        
        comparison['database_changes'][key] = {
            'before': before_count,
            'after': after_count,
            'change': change
        }
    
    # Validate core infrastructure preservation
    before_infra = before_state.get('integrity', {}).get('core_infrastructure', {})
    after_infra = after_state.get('integrity', {}).get('core_infrastructure', {})
    
    for key in before_infra:
        before_val = before_infra.get(key, False)
        after_val = after_infra.get(key, False)
        
        if before_val and not after_val:
            comparison['issues'].append(f"Core infrastructure lost: {key}")
            comparison['validation_passed'] = False
        
        comparison['integrity_check'][key] = {
            'before': before_val,
            'after': after_val,
            'preserved': before_val == after_val or not before_val
        }
    
    # Check expected changes if provided
    if expected_changes:
        for change_type, expectations in expected_changes.items():
            if change_type == 'users_reset_to_admin_only':
                admin_count = after_state.get('integrity', {}).get('admin_users', {}).get('count', 0)
                total_users = after_state['database'].get('users', 0)
                if total_users != 1 or admin_count != 1:
                    comparison['issues'].append(f"Expected single admin user, got {total_users} users, {admin_count} admins")
                    comparison['validation_passed'] = False
            
            elif change_type == 'audit_trails_cleared':
                if after_state['database'].get('audit_trails', 0) > 5:  # Allow some trails from reinit process
                    comparison['issues'].append("Audit trails not properly cleared")
                    comparison['validation_passed'] = False
    
    return comparison


def create_test_data():
    """
    Create sample test data for validation
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.audit.services import audit_service
        
        User = get_user_model()
        
        # Create test users
        test_users = []
        for i in range(3):
            username = f"test_user_{i+1}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': f'Test{i+1}',
                    'last_name': 'User',
                    'is_active': True
                }
            )
            if created:
                user.set_password('test123')
                user.save()
                test_users.append(user)
        
        # Create audit trail entry
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            audit_service.log_user_action(
                user=admin_user,
                action='TEST_DATA_CREATED',
                object_type='System',
                description='Test data created for validation testing'
            )
        
        return len(test_users)
        
    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        return 0


def validate_backup_integrity(backup_path):
    """
    Validate backup file integrity
    """
    validation = {
        'file_path': backup_path,
        'timestamp': datetime.now().isoformat(),
        'file_exists': False,
        'file_size': 0,
        'checksum': None,
        'archive_valid': False,
        'content_summary': {},
        'errors': []
    }
    
    try:
        if os.path.exists(backup_path):
            validation['file_exists'] = True
            validation['file_size'] = os.path.getsize(backup_path)
            
            # Calculate checksum
            hash_sha256 = hashlib.sha256()
            with open(backup_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            validation['checksum'] = hash_sha256.hexdigest()
            
            # Validate archive if it's a tar.gz
            if backup_path.endswith('.tar.gz'):
                import tarfile
                try:
                    with tarfile.open(backup_path, 'r:gz') as tar:
                        members = tar.getmembers()
                        validation['archive_valid'] = True
                        validation['content_summary'] = {
                            'total_files': len(members),
                            'total_size': sum(m.size for m in members if m.isfile()),
                            'directories': len([m for m in members if m.isdir()]),
                            'files': len([m for m in members if m.isfile()])
                        }
                        
                        # Sample file listing
                        validation['content_summary']['sample_files'] = [
                            m.name for m in members[:10] if m.isfile()
                        ]
                        
                except Exception as e:
                    validation['errors'].append(f"Archive validation failed: {str(e)}")
            
        else:
            validation['errors'].append("Backup file does not exist")
            
    except Exception as e:
        validation['errors'].append(f"Backup validation error: {str(e)}")
    
    return validation


def generate_validation_report(validation_data, output_path=None):
    """
    Generate comprehensive validation report
    """
    if output_path is None:
        output_path = f"/tmp/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    report = {
        'report_generated': datetime.now().isoformat(),
        'validation_data': validation_data,
        'summary': {
            'total_phases': len([v for v in validation_data.values() if isinstance(v, dict) and 'phase' in v]),
            'errors_found': sum(len(v.get('errors', [])) for v in validation_data.values() if isinstance(v, dict)),
            'validations_passed': True
        }
    }
    
    # Check for any validation failures
    for key, data in validation_data.items():
        if isinstance(data, dict):
            if data.get('errors'):
                report['summary']['validations_passed'] = False
            if 'validation_passed' in data and not data['validation_passed']:
                report['summary']['validations_passed'] = False
    
    # Save report
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return output_path
    except Exception as e:
        # Fallback to /tmp if original path fails
        fallback_path = f"/tmp/validation_report_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fallback_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return fallback_path