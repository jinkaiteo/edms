"""
Management command to create default EDMS roles
"""
from django.core.management.base import BaseCommand
from apps.users.models import Role


class Command(BaseCommand):
    help = 'Create default EDMS roles for the system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default EDMS roles...'))
        self.stdout.write('Based on actual system usage and seed_test_users.py')
        self.stdout.write('')
        
        # Define default roles based on actual system implementation
        # These 7 core roles are the essential roles used in the system
        
        default_roles = [
            # Document Management Roles (O1 Module)
            {
                'name': 'Document Admin',
                'module': 'O1',
                'permission_level': 'admin',
                'description': 'Full administrative access to document management system',
                'is_system_role': True
            },
            {
                'name': 'Document Approver',
                'module': 'O1',
                'permission_level': 'approve',
                'description': 'Can give final approval to documents and set effective dates',
                'is_system_role': True
            },
            {
                'name': 'Document Reviewer',
                'module': 'O1',
                'permission_level': 'review',
                'description': 'Can review and approve/reject documents during review process',
                'is_system_role': True
            },
            {
                'name': 'Document Author',
                'module': 'O1',
                'permission_level': 'write',
                'description': 'Can create, edit, and submit documents for review',
                'is_system_role': True
            },
            {
                'name': 'Document Viewer',
                'module': 'O1',
                'permission_level': 'read',
                'description': 'Can view approved/effective documents only',
                'is_system_role': True
            },
            
            # User Management Role (S1 Module)
            {
                'name': 'User Admin',
                'module': 'S1',
                'permission_level': 'admin',
                'description': 'Full administrative access to user management and security',
                'is_system_role': True
            },
            
            # Placeholder Management Role (S6 Module)
            {
                'name': 'Placeholder Admin',
                'module': 'S6',
                'permission_level': 'admin',
                'description': 'Full administrative access to placeholder management',
                'is_system_role': True
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
                    'description': role_data['description'],
                    'is_system_role': role_data.get('is_system_role', True)
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
