"""
Management command to create default EDMS roles
"""
from django.core.management.base import BaseCommand
from apps.users.models import Role


class Command(BaseCommand):
    help = 'Create default EDMS roles for the system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default EDMS roles...'))
        
        # Define default roles based on actual MODULE_CHOICES
        # O1: Electronic Document Management
        # S1: User Management
        # S2: Audit Trail  
        # S3: Scheduler
        # S4: Backup and Health Check
        # S5: Workflow Settings
        # S6: Placeholder Management
        # S7: App Settings
        
        default_roles = [
            # O1 Module - Electronic Document Management
            {
                'name': 'Document Admin',
                'module': 'O1',
                'permission_level': 'admin',
                'description': 'Full administrative access to document management'
            },
            {
                'name': 'Document Author',
                'module': 'O1',
                'permission_level': 'write',
                'description': 'Can create and edit documents'
            },
            {
                'name': 'Document Reviewer',
                'module': 'O1',
                'permission_level': 'review',
                'description': 'Can review documents in workflow'
            },
            {
                'name': 'Document Approver',
                'module': 'O1',
                'permission_level': 'approve',
                'description': 'Can approve documents in workflow'
            },
            {
                'name': 'Document Reader',
                'module': 'O1',
                'permission_level': 'read',
                'description': 'Can view documents'
            },
            
            # S1 Module - User Management
            {
                'name': 'User Management Admin',
                'module': 'S1',
                'permission_level': 'admin',
                'description': 'Full administrative access to user management and security'
            },
            {
                'name': 'User Manager',
                'module': 'S1',
                'permission_level': 'write',
                'description': 'Can create and manage users'
            },
            
            # S2 Module - Audit Trail
            {
                'name': 'Audit Admin',
                'module': 'S2',
                'permission_level': 'admin',
                'description': 'Full administrative access to audit trails'
            },
            {
                'name': 'Auditor',
                'module': 'S2',
                'permission_level': 'read',
                'description': 'Can view audit trails and compliance reports'
            },
            
            # S3 Module - Scheduler
            {
                'name': 'Scheduler Admin',
                'module': 'S3',
                'permission_level': 'admin',
                'description': 'Full administrative access to scheduler'
            },
            
            # S4 Module - Backup and Health Check
            {
                'name': 'Backup Admin',
                'module': 'S4',
                'permission_level': 'admin',
                'description': 'Full administrative access to backup and health check'
            },
            
            # S5 Module - Workflow Settings
            {
                'name': 'Workflow Admin',
                'module': 'S5',
                'permission_level': 'admin',
                'description': 'Full administrative access to workflow settings'
            },
            {
                'name': 'Workflow Manager',
                'module': 'S5',
                'permission_level': 'write',
                'description': 'Can manage workflow configurations'
            },
            
            # S6 Module - Placeholder Management
            {
                'name': 'Placeholder Admin',
                'module': 'S6',
                'permission_level': 'admin',
                'description': 'Full administrative access to placeholder management'
            },
            
            # S7 Module - App Settings
            {
                'name': 'Settings Admin',
                'module': 'S7',
                'permission_level': 'admin',
                'description': 'Full administrative access to application settings'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'module': role_data['module'],
                    'permission_level': role_data['permission_level'],
                    'description': role_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {role.name} ({role.module})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  - Exists: {role.name} ({role.module})')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed! Created: {created_count}, Already existed: {updated_count}'
            )
        )
        self.stdout.write('')
        self.stdout.write('Available roles:')
        
        all_roles = Role.objects.all().order_by('module', 'name')
        for role in all_roles:
            self.stdout.write(f'  - {role.name} ({role.module}/{role.permission_level})')
