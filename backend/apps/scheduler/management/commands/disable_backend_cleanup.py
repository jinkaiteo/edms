"""
Management command to disable celery.backend_cleanup task.
This task is auto-created by django-celery-results and recreates itself if deleted.
Instead, we disable it since we have our own cleanup-celery-results task.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask


class Command(BaseCommand):
    help = 'Disable celery.backend_cleanup task (auto-created by django-celery-results)'

    def handle(self, *args, **options):
        # Don't delete, just disable
        updated = PeriodicTask.objects.filter(name='celery.backend_cleanup').update(enabled=False)
        
        if updated > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Disabled celery.backend_cleanup task')
            )
        else:
            self.stdout.write('Task not found (will be disabled when created)')
        
        # Show status
        task = PeriodicTask.objects.filter(name='celery.backend_cleanup').first()
        if task:
            self.stdout.write(f'Status: enabled={task.enabled}')
        
        total = PeriodicTask.objects.count()
        enabled = PeriodicTask.objects.filter(enabled=True).count()
        self.stdout.write(f'Total tasks: {total} ({enabled} enabled, {total-enabled} disabled)')
