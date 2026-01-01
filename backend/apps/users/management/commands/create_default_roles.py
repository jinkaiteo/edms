"""
Management command to create default EDMS roles
"""
from django.core.management.base import BaseCommand
from apps.users.models import Role


class Command(BaseCommand):
    help = 'Create default EDMS roles for the system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default EDMS roles...'))
        
        # Define default roles
        default_roles = [
            # S1 Module - Security/User Management
            {
                'name': 'S1 Admin',
                'module': 'S1',
                'permission_level': 'admin',
                'description': 'Full administrative access to user management and security settings'
            },
            {
                'name': 'S1 User',
                'module': 'S1',
                'permission_level': 'user',
                'description': 'Standard user access to security features'
            },
            
            # S2 Module - Document Management
            {
                'name': 'S2 Admin',
                'module': 'S2',
                'permission_level': 'admin',
                'description': 'Full administrative access to document management'
            },
            {
                'name': 'S2 User',
                'module': 'S2',
                'permission_level': 'user',
                'description': 'Standard user access to document management'
            },
            {
                'name': 'Document Author',
                'module': 'S2',
                'permission_level': 'user',
                'description': 'Can create and edit documents'
            },
            {
                'name': 'Document Reviewer',
                'module': 'S2',
                'permission_level': 'user',
                'description': 'Can review documents in workflow'
            },
            {
                'name': 'Document Approver',
                'module': 'S2',
                'permission_level': 'user',
                'description': 'Can approve documents in workflow'
            },
            
            # S3 Module - Workflow Management
            {
                'name': 'S3 Admin',
                'module': 'S3',
                'permission_level': 'admin',
                'description': 'Full administrative access to workflow management'
            },
            {
                'name': 'S3 User',
                'module': 'S3',
                'permission_level': 'user',
                'description': 'Standard user access to workflow features'
            },
            {
                'name': 'Workflow Manager',
                'module': 'S3',
                'permission_level': 'user',
                'description': 'Can manage workflow configurations'
            },
            
            # S4 Module - Audit & Compliance
            {
                'name': 'S4 Admin',
                'module': 'S4',
                'permission_level': 'admin',
                'description': 'Full administrative access to audit and compliance features'
            },
            {
                'name': 'S4 User',
                'module': 'S4',
                'permission_level': 'user',
                'description': 'Standard user access to audit features'
            },
            {
                'name': 'Auditor',
                'module': 'S4',
                'permission_level': 'user',
                'description': 'Can view audit trails and compliance reports'
            },
            
            # S5 Module - Scheduler & Automation
            {
                'name': 'S5 Admin',
                'module': 'S5',
                'permission_level': 'admin',
                'description': 'Full administrative access to scheduler and automation'
            },
            {
                'name': 'S5 User',
                'module': 'S5',
                'permission_level': 'user',
                'description': 'Standard user access to scheduler features'
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
