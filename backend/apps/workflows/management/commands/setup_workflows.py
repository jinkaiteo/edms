"""
Django management command to set up Django-River workflows for EDMS.

This command initializes the workflow states, transitions, and permissions
required for document lifecycle management.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

# from river.models import State, Transition, TransitionApproval
# River workflow engine removed - using custom workflow implementation
from apps.documents.models import Document
from apps.workflows.models import WorkflowType, WorkflowTemplate, DOCUMENT_STATES
from apps.users.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up Django-River workflows for EDMS document management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing workflow configuration',
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test workflow data',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting workflow setup...')
        )

        if options['reset']:
            self._reset_workflows()

        with transaction.atomic():
            self._create_workflow_states()
            self._create_workflow_types()
            self._create_workflow_templates()
            self._setup_review_workflow()
            self._setup_approval_workflow()
            self._setup_obsolete_workflow()
            
            if options['create_test_data']:
                self._create_test_data()

        self.stdout.write(
            self.style.SUCCESS('Workflow setup completed successfully!')
        )

    def _reset_workflows(self):
        """Reset existing workflow configuration."""
        self.stdout.write('Resetting existing workflows...')
        
        # Delete workflow-related data
        TransitionApproval.objects.all().delete()
        Transition.objects.all().delete()
        WorkflowTemplate.objects.all().delete()
        WorkflowType.objects.all().delete()
        
        # Keep states as they might be referenced elsewhere
        self.stdout.write('Reset complete.')

    def _create_workflow_states(self):
        """Create workflow states for document lifecycle."""
        self.stdout.write('Creating workflow states...')
        
        for state_code, state_label in DOCUMENT_STATES:
            state, created = State.objects.get_or_create(
                slug=state_code,
                defaults={'label': state_label}
            )
            if created:
                self.stdout.write(f'  Created state: {state_label}')

    def _create_workflow_types(self):
        """Create workflow type configurations."""
        self.stdout.write('Creating workflow types...')
        
        workflow_configs = [
            {
                'name': 'Document Review Workflow',
                'workflow_type': 'REVIEW',
                'description': 'Standard document review process',
                'requires_approval': True,
                'timeout_days': 7,
                'reminder_days': 2
            },
            {
                'name': 'Document Approval Workflow',
                'workflow_type': 'APPROVAL',
                'description': 'Document approval process',
                'requires_approval': True,
                'timeout_days': 5,
                'reminder_days': 1
            },
            {
                'name': 'Document Up-versioning',
                'workflow_type': 'UP_VERSION',
                'description': 'Document version update workflow',
                'requires_approval': True,
                'timeout_days': 10,
                'reminder_days': 3
            },
            {
                'name': 'Document Obsolescence',
                'workflow_type': 'OBSOLETE',
                'description': 'Document obsolescence workflow',
                'requires_approval': True,
                'timeout_days': 14,
                'reminder_days': 7
            },
            {
                'name': 'Document Termination',
                'workflow_type': 'TERMINATE',
                'description': 'Emergency document termination',
                'requires_approval': False,
                'timeout_days': 1,
                'reminder_days': 0
            }
        ]
        
        for config in workflow_configs:
            wf_type, created = WorkflowType.objects.get_or_create(
                workflow_type=config['workflow_type'],
                defaults=config
            )
            if created:
                self.stdout.write(f'  Created workflow type: {config["name"]}')

    def _create_workflow_templates(self):
        """Create reusable workflow templates."""
        self.stdout.write('Creating workflow templates...')
        
        # Standard Review Template
        review_template = {
            'name': 'Standard Review Template',
            'workflow_type': 'REVIEW',
            'states_config': {
                'initial': 'draft',
                'transitions': [
                    'draft -> pending_review',
                    'pending_review -> under_review',
                    'under_review -> review_completed',
                    'review_completed -> pending_approval',
                    'pending_approval -> approved',
                    'approved -> effective'
                ]
            },
            'transitions_config': {
                'submit_for_review': {
                    'from_state': 'draft',
                    'to_state': 'pending_review',
                    'required_role': 'author'
                },
                'start_review': {
                    'from_state': 'pending_review',
                    'to_state': 'under_review',
                    'required_role': 'reviewer'
                },
                'complete_review': {
                    'from_state': 'under_review',
                    'to_state': 'review_completed',
                    'required_role': 'reviewer'
                },
                'submit_for_approval': {
                    'from_state': 'review_completed',
                    'to_state': 'pending_approval',
                    'required_role': 'reviewer'
                },
                'approve': {
                    'from_state': 'pending_approval',
                    'to_state': 'approved',
                    'required_role': 'approver'
                },
                'make_effective': {
                    'from_state': 'approved',
                    'to_state': 'effective',
                    'required_role': 'system'
                }
            },
            'is_active': True,
            'is_default': True
        }
        
        template, created = WorkflowTemplate.objects.get_or_create(
            name=review_template['name'],
            workflow_type=review_template['workflow_type'],
            defaults=review_template
        )
        if created:
            self.stdout.write(f'  Created template: {review_template["name"]}')

    def _setup_review_workflow(self):
        """Set up the document review workflow using Django-River."""
        self.stdout.write('Setting up review workflow...')
        
        document_ct = ContentType.objects.get_for_model(Document)
        
        # Get states
        draft = State.objects.get(slug='draft')
        pending_review = State.objects.get(slug='pending_review')
        under_review = State.objects.get(slug='under_review')
        review_completed = State.objects.get(slug='review_completed')
        
        # Get roles for permissions
        try:
            reviewer_role = Role.objects.get(name='Document Reviewer')
            author_role = Role.objects.get(name='Document Author')
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Required roles not found. Please create roles first.')
            )
            return
        
        # Create transitions
        transitions = [
            {
                'source': draft,
                'destination': pending_review,
                'field': 'state',
                'content_type': document_ct
            },
            {
                'source': pending_review,
                'destination': under_review,
                'field': 'state',
                'content_type': document_ct
            },
            {
                'source': under_review,
                'destination': review_completed,
                'field': 'state',
                'content_type': document_ct
            }
        ]
        
        for transition_config in transitions:
            transition, created = Transition.objects.get_or_create(
                **transition_config
            )
            if created:
                self.stdout.write(
                    f'  Created transition: {transition.source.label} -> {transition.destination.label}'
                )

    def _setup_approval_workflow(self):
        """Set up the document approval workflow."""
        self.stdout.write('Setting up approval workflow...')
        
        document_ct = ContentType.objects.get_for_model(Document)
        
        # Get states
        pending_approval = State.objects.get(slug='pending_approval')
        approved = State.objects.get(slug='approved')
        effective = State.objects.get(slug='effective')
        
        # Create approval transitions
        transitions = [
            {
                'source': pending_approval,
                'destination': approved,
                'field': 'state',
                'content_type': document_ct
            },
            {
                'source': approved,
                'destination': effective,
                'field': 'state',
                'content_type': document_ct
            }
        ]
        
        for transition_config in transitions:
            transition, created = Transition.objects.get_or_create(
                **transition_config
            )
            if created:
                self.stdout.write(
                    f'  Created transition: {transition.source.label} -> {transition.destination.label}'
                )

    def _setup_obsolete_workflow(self):
        """Set up the document obsolescence workflow."""
        self.stdout.write('Setting up obsolescence workflow...')
        
        document_ct = ContentType.objects.get_for_model(Document)
        
        # Get states
        effective = State.objects.get(slug='effective')
        obsolete = State.objects.get(slug='obsolete')
        
        # Create obsolescence transition
        transition, created = Transition.objects.get_or_create(
            source=effective,
            destination=obsolete,
            field='state',
            content_type=document_ct
        )
        if created:
            self.stdout.write(
                f'  Created transition: {transition.source.label} -> {transition.destination.label}'
            )

    def _create_test_data(self):
        """Create test workflow data."""
        self.stdout.write('Creating test workflow data...')
        
        # This would create sample workflow instances for testing
        # Implementation depends on having test documents and users
        self.stdout.write('  Test data creation skipped (requires test documents)')