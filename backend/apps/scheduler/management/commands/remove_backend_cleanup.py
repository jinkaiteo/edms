"""
Management command to remove celery.backend_cleanup task.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask


class Command(BaseCommand):
    help = 'Remove celery.backend_cleanup task (we use our own cleanup-celery-results task)'

    def handle(self, *args, **options):
        deleted_count, _ = PeriodicTask.objects.filter(name='celery.backend_cleanup').delete()
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Removed celery.backend_cleanup task')
            )
        else:
            self.stdout.write('Task not found (already removed)')
        
        # Show remaining tasks
        total = PeriodicTask.objects.count()
        self.stdout.write(f'Total periodic tasks: {total}')
