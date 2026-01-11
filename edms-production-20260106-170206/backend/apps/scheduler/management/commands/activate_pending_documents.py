"""
Django management command to activate pending effective documents.

This command should be run daily at midnight via cron job to check for
documents in APPROVED_PENDING_EFFECTIVE status that are due to become
effective today.

Example cron entry:
0 0 * * * /path/to/manage.py activate_pending_documents
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.workflows.services import get_simple_workflow_service


class Command(BaseCommand):
    help = 'Activate documents that are APPROVED_PENDING_EFFECTIVE and due today'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be activated without making changes',
        )

    def handle(self, *args, **options):
        """Execute the daily activation check."""
        service = get_simple_workflow_service()
        today = timezone.now().date()
        
        self.stdout.write(f'Checking for documents to activate on {today}...')
        
        if options['dry_run']:
            self.stdout.write('DRY RUN MODE - No changes will be made')
            
            # Show what would be activated
            from apps.documents.models import Document
            pending_docs = Document.objects.filter(
                status='APPROVED_PENDING_EFFECTIVE',
                effective_date__lte=today
            )
            
            if pending_docs:
                self.stdout.write(f'Found {pending_docs.count()} documents to activate:')
                for doc in pending_docs:
                    self.stdout.write(f'  - {doc.document_number}: {doc.title} (effective: {doc.effective_date})')
            else:
                self.stdout.write('No documents found to activate')
        else:
            # Actually activate documents
            try:
                activated_count = service.lifecycle_service.activate_pending_effective_documents()
                
                if activated_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully activated {activated_count} document(s)'
                        )
                    )
                else:
                    self.stdout.write('No documents were due for activation today')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error during activation: {e}')
                )
                raise