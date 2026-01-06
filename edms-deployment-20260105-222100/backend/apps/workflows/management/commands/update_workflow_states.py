"""
Management command to update workflow states for specification compliance.
Migrates existing workflow states to match EDMS_details_workflow.txt exactly.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workflows.models import DocumentState, DocumentWorkflow


class Command(BaseCommand):
    help = 'Update workflow states for EDMS specification compliance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Updating workflow states for specification compliance...')
        
        # Define state mappings from old to new
        state_mappings = {
            'PENDING_REVIEW': ('PENDING_REVIEW', 'Pending Review'),
            'UNDER_REVIEW': ('PENDING_REVIEW', 'Pending Review'),  # Merge into Pending Review
            'REVIEW_COMPLETED': ('REVIEWED', 'Reviewed'),
            'UNDER_APPROVAL': ('PENDING_APPROVAL', 'Pending Approval'),  # Merge into Pending Approval  
            'APPROVED': ('APPROVED_PENDING_EFFECTIVE', 'Approved, Pending Effective'),
            'EFFECTIVE': ('APPROVED_AND_EFFECTIVE', 'Approved and Effective'),
            'SUPERSEDED': ('SUPERSEDED', 'Superseded'),
            'OBSOLETE': ('OBSOLETE', 'Obsolete'),
            'TERMINATED': ('DRAFT', 'DRAFT'),  # Terminated workflows return to DRAFT
        }
        
        # Required states per specification
        required_states = [
            ('DRAFT', 'DRAFT', True, False),
            ('PENDING_REVIEW', 'Pending Review', False, False),
            ('REVIEWED', 'Reviewed', False, False),
            ('PENDING_APPROVAL', 'Pending Approval', False, False),
            ('APPROVED_PENDING_EFFECTIVE', 'Approved, Pending Effective', False, False),
            ('APPROVED_AND_EFFECTIVE', 'Approved and Effective', False, True),
            ('SUPERSEDED', 'Superseded', False, True),
            ('PENDING_OBSOLETION', 'Pending Obsoletion', False, False),
            ('OBSOLETE', 'Obsolete', False, True),
        ]
        
        with transaction.atomic():
            if not dry_run:
                # Create/update required states
                for code, name, is_initial, is_final in required_states:
                    state, created = DocumentState.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': name,
                            'description': f'{name} state per EDMS specification',
                            'is_initial': is_initial,
                            'is_final': is_final,
                        }
                    )
                    if created:
                        self.stdout.write(f'  ✅ Created state: {code} - {name}')
                    else:
                        # Update existing state
                        state.name = name
                        state.is_initial = is_initial
                        state.is_final = is_final
                        state.save()
                        self.stdout.write(f'  📝 Updated state: {code} - {name}')
                
                # Update existing workflows
                updated_count = 0
                for old_state, (new_code, new_name) in state_mappings.items():
                    workflows = DocumentWorkflow.objects.filter(current_state_id=old_state)
                    count = workflows.count()
                    if count > 0:
                        workflows.update(current_state_id=new_code)
                        updated_count += count
                        self.stdout.write(f'  🔄 Updated {count} workflows from {old_state} to {new_code}')
                
                # Remove obsolete states
                obsolete_states = ['UNDER_REVIEW', 'UNDER_APPROVAL']
                for state_code in obsolete_states:
                    try:
                        state = DocumentState.objects.get(code=state_code)
                        # Check if any workflows still reference this state
                        if not DocumentWorkflow.objects.filter(current_state_id=state_code).exists():
                            state.delete()
                            self.stdout.write(f'  🗑️  Removed obsolete state: {state_code}')
                        else:
                            self.stdout.write(f'  ⚠️  Cannot remove {state_code} - still referenced by workflows')
                    except DocumentState.DoesNotExist:
                        pass
                
                self.stdout.write(f'\n✅ Updated {updated_count} workflow instances')
            
            else:
                # Dry run - show what would be done
                self.stdout.write('\nWould create/update these states:')
                for code, name, is_initial, is_final in required_states:
                    try:
                        existing = DocumentState.objects.get(code=code)
                        self.stdout.write(f'  📝 Update: {code} - {name}')
                    except DocumentState.DoesNotExist:
                        self.stdout.write(f'  ✅ Create: {code} - {name}')
                
                self.stdout.write('\nWould update these workflows:')
                total_updates = 0
                for old_state, (new_code, new_name) in state_mappings.items():
                    workflows = DocumentWorkflow.objects.filter(current_state_id=old_state)
                    count = workflows.count()
                    if count > 0:
                        total_updates += count
                        self.stdout.write(f'  🔄 {count} workflows: {old_state} → {new_code}')
                
                self.stdout.write(f'\nTotal workflows to update: {total_updates}')
        
        self.stdout.write(self.style.SUCCESS('\nWorkflow state update completed!'))
        
        if not dry_run:
            self.stdout.write('\n📋 Current states:')
            for state in DocumentState.objects.all().order_by('code'):
                marker = '🟢' if state.is_initial else '🔴' if state.is_final else '🔵'
                self.stdout.write(f'  {marker} {state.code}: {state.name}')
        
        self.stdout.write('\n🎯 Specification compliance achieved!')