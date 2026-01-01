"""
Management command to create default Django Groups for EDMS
These are the groups actually used by the workflow system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create default Django Groups for EDMS workflow system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default EDMS Django Groups...'))
        self.stdout.write('Note: These are different from the Role model - these are Django Groups used by workflows')
        self.stdout.write('')
        
        # Define default groups based on actual usage in workflow code
        default_groups = [
            {
                'name': 'Document Admins',
                'description': 'Administrative access to document management'
            },
            {
                'name': 'Document Reviewers',
                'description': 'Can review documents in workflow'
            },
            {
                'name': 'Document Approvers',
                'description': 'Can approve documents in workflow'
            },
            {
                'name': 'Senior Document Approvers',
                'description': 'Can approve all documents including sensitive ones'
            },
            {
                'name': 'Document_Reviewers',
                'description': 'Alternative name for reviewers (underscore version)'
            },
            {
                'name': 'Document_Approvers',
                'description': 'Alternative name for approvers (underscore version)'
            },
        ]
        
        created_count = 0
        exists_count = 0
        
        for group_data in default_groups:
            group, created = Group.objects.get_or_create(
                name=group_data['name']
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {group.name}')
                )
            else:
                exists_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  - Exists: {group.name}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed! Created: {created_count}, Already existed: {exists_count}'
            )
        )
        self.stdout.write('')
        self.stdout.write('Available Django Groups:')
        
        all_groups = Group.objects.all().order_by('name')
        for group in all_groups:
            user_count = group.user_set.count()
            self.stdout.write(f'  - {group.name} ({user_count} users)')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Groups created successfully!'))
        self.stdout.write('')
        self.stdout.write('To assign users to groups:')
        self.stdout.write('  1. Django Admin: http://your-server/admin/auth/group/')
        self.stdout.write('  2. Python shell:')
        self.stdout.write('     from django.contrib.auth.models import Group')
        self.stdout.write('     from apps.users.models import User')
        self.stdout.write('     user = User.objects.get(username="author01")')
        self.stdout.write('     group = Group.objects.get(name="Document Reviewers")')
        self.stdout.write('     user.groups.add(group)')
