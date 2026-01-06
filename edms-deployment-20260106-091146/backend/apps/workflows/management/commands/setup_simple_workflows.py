"""
Management command to set up simplified workflow system.
Creates initial workflow types and document states for EDMS.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workflows.models import WorkflowType
from apps.workflows.models import DocumentState


User = get_user_model()


class Command(BaseCommand):
    help = 'Set up simplified workflow system with initial data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up simplified workflow system...'))
        
        # Create initial document states
        self.create_document_states()
        
        # Create workflow types
        self.create_workflow_types()
        
        self.stdout.write(self.style.SUCCESS('Workflow setup completed!'))

    def create_document_states(self):
        """Create initial document workflow states."""
        self.stdout.write('Creating document states...')
        
        states_data = [
            ('DRAFT', 'Draft', 'Initial draft state', True, False),
            ('PENDING_REVIEW', 'Pending Review', 'Waiting for review assignment', False, False),
            ('UNDER_REVIEW', 'Under Review', 'Currently being reviewed', False, False),
            ('REVIEW_COMPLETED', 'Review Completed', 'Review completed, awaiting approval', False, False),
            ('PENDING_APPROVAL', 'Pending Approval', 'Waiting for approval', False, False),
            ('UNDER_APPROVAL', 'Under Approval', 'Currently being approved', False, False),
            ('APPROVED', 'Approved', 'Approved and ready to be effective', False, False),
            ('EFFECTIVE', 'Effective', 'Document is effective and in use', False, True),
            ('SUPERSEDED', 'Superseded', 'Replaced by newer version', False, True),
            ('OBSOLETE', 'Obsolete', 'No longer in use', False, True),
            ('TERMINATED', 'Terminated', 'Workflow terminated early', False, True),
        ]
        
        for code, name, description, is_initial, is_final in states_data:
            state, created = DocumentState.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_initial': is_initial,
                    'is_final': is_final,
                }
            )
            if created:
                self.stdout.write(f'  Created state: {name}')
            else:
                self.stdout.write(f'  State exists: {name}')

    def create_workflow_types(self):
        """Create initial workflow types."""
        self.stdout.write('Creating workflow types...')
        
        # Get or create a system user for workflow creation
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                'admin', 'admin@edms.local', 'admin123'
            )
            self.stdout.write('  Created admin user for workflows')
        
        workflow_types_data = [
            {
                'name': 'Document Review Workflow',
                'workflow_type': 'REVIEW',
                'description': 'Standard document review and approval workflow',
                'requires_approval': True,
                'timeout_days': 30,
                'reminder_days': 7,
            },
            {
                'name': 'Document Up-versioning Workflow',
                'workflow_type': 'UP_VERSION',
                'description': 'Workflow for creating new versions of documents',
                'requires_approval': True,
                'timeout_days': 14,
                'reminder_days': 3,
            },
            {
                'name': 'Document Obsolescence Workflow',
                'workflow_type': 'OBSOLETE',
                'description': 'Workflow for marking documents as obsolete',
                'requires_approval': True,
                'timeout_days': 7,
                'reminder_days': 2,
            },
            {
                'name': 'Emergency Approval Workflow',
                'workflow_type': 'APPROVAL',
                'description': 'Fast-track approval for emergency documents',
                'requires_approval': True,
                'timeout_days': 3,
                'reminder_days': 1,
            },
        ]
        
        for workflow_data in workflow_types_data:
            workflow_type, created = WorkflowType.objects.get_or_create(
                name=workflow_data['name'],
                defaults={
                    **workflow_data,
                    'created_by': admin_user,
                }
            )
            if created:
                self.stdout.write(f'  Created workflow type: {workflow_data["name"]}')
            else:
                self.stdout.write(f'  Workflow type exists: {workflow_data["name"]}')