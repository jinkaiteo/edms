"""
Django management command to clean up workflow tasks.

This command provides manual execution of the workflow task cleanup process
for immediate maintenance or troubleshooting purposes.

Usage:
    python manage.py cleanup_workflow_tasks                    # Actual cleanup
    python manage.py cleanup_workflow_tasks --dry-run          # Preview only
    python manage.py cleanup_workflow_tasks --verbose          # Detailed output
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.scheduler.automated_tasks import DocumentAutomationService
import json


class Command(BaseCommand):
    help = 'Clean up orphaned, irrelevant, and expired workflow tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making actual changes'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed information about cleaned tasks'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation prompts'
        )

    def handle(self, *args, **options):
        """Execute the workflow task cleanup command."""
        
        dry_run = options['dry_run']
        verbose = options['verbose']
        force = options['force']
        
        # Display banner
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        self.stdout.write(
            self.style.SUCCESS('🧹 EDMS Workflow Task Cleanup')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No actual changes will be made')
            )
        
        # Confirmation prompt for actual cleanup
        if not dry_run and not force:
            confirm = input('\nThis will permanently clean up workflow tasks. Continue? (y/N): ')
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write(self.style.ERROR('❌ Operation cancelled'))
                return
        
        self.stdout.write(f'\n⏱️ Starting cleanup at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        try:
            # Execute cleanup
            automation_service = DocumentAutomationService()
            results = automation_service.cleanup_workflow_tasks(dry_run=dry_run)
            
            if results['status'] == 'completed':
                # Display summary
                self._display_summary(results, verbose)
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'\n✅ Cleanup completed successfully in {results["execution_time"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'\n🔍 Dry run completed in {results["execution_time"]}')
                    )
                    self.stdout.write(
                        self.style.WARNING('💡 Run without --dry-run to perform actual cleanup')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Cleanup failed: {results["message"]}')
                )
                return
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Cleanup command failed: {str(e)}')
            )
            raise CommandError(f'Workflow task cleanup failed: {str(e)}')
        
        # Display next scheduled run
        if 'next_run' in results:
            self.stdout.write(
                f'\n📅 Next scheduled cleanup: {results["next_run"].strftime("%Y-%m-%d %H:%M:%S")}'
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n' + '=' * 60)
        )

    def _display_summary(self, results, verbose):
        """Display cleanup results summary."""
        
        cleanup_results = results['results']
        
        self.stdout.write('\n📊 CLEANUP SUMMARY:')
        self.stdout.write('-' * 30)
        
        # Task type counts
        task_types = [
            ('Terminated/Obsolete Document Tasks', cleanup_results['terminated_document_tasks']),
            ('Nonexistent Document Tasks', cleanup_results['nonexistent_document_tasks']),
            ('Orphaned Workflow Tasks', cleanup_results['orphaned_tasks']),
            ('Duplicate Tasks', cleanup_results['duplicate_tasks']),
            ('Expired Tasks', cleanup_results['expired_tasks'])
        ]
        
        total_cleaned = 0
        for task_type, count in task_types:
            total_cleaned += count
            if count > 0:
                self.stdout.write(f'  🔹 {task_type}: {count}')
            else:
                self.stdout.write(f'  ⚪ {task_type}: {count}')
        
        self.stdout.write('-' * 30)
        self.stdout.write(f'  📈 TOTAL TASKS PROCESSED: {total_cleaned}')
        
        if verbose and cleanup_results['details']:
            self.stdout.write('\n📋 DETAILED BREAKDOWN:')
            self.stdout.write('-' * 40)
            
            # Group details by type
            by_type = {}
            for detail in cleanup_results['details']:
                task_type = detail['type']
                if task_type not in by_type:
                    by_type[task_type] = []
                by_type[task_type].append(detail)
            
            for task_type, details in by_type.items():
                self.stdout.write(f'\n  📁 {task_type.upper().replace("_", " ")}:')
                for detail in details:
                    self.stdout.write(f'    • Task #{detail["task_id"]} → {detail.get("assigned_to", "Unassigned")}')
                    if 'document' in detail:
                        self.stdout.write(f'      Document: {detail["document"]} ({detail.get("document_status", "Unknown")})')
                    if 'task_type' in detail:
                        self.stdout.write(f'      Type: {detail["task_type"]}')
        
        # Impact statement
        if total_cleaned > 0:
            self.stdout.write(f'\n💡 IMPACT: {total_cleaned} orphaned tasks removed from user task lists')
        else:
            self.stdout.write('\n✨ RESULT: No orphaned tasks found - system is clean!')

    def _format_task_detail(self, detail):
        """Format a single task detail for display."""
        lines = [f"Task #{detail['task_id']}"]
        
        if 'document' in detail:
            lines.append(f"  Document: {detail['document']}")
        
        if 'assigned_to' in detail:
            lines.append(f"  Assigned to: {detail['assigned_to']}")
        
        if 'task_type' in detail:
            lines.append(f"  Type: {detail['task_type']}")
        
        return '\n'.join(lines)