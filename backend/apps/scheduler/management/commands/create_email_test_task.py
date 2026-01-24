"""
Management command to create the "Send Test Email" periodic task.
This task is used for manual testing of email configuration.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Create the "Send Test Email" periodic task for manual email testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating "Send Test Email" task...')
        
        # Check if task already exists
        existing_task = PeriodicTask.objects.filter(name='Send Test Email').first()
        if existing_task:
            self.stdout.write(self.style.WARNING(
                f'✓ Task "{existing_task.name}" already exists'
            ))
            self.stdout.write(f'  Task: {existing_task.task}')
            self.stdout.write(f'  Enabled: {existing_task.enabled}')
            return
        
        # Create a crontab that never runs (manual trigger only)
        # Using impossible date: February 31st
        crontab, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_month='31',
            month_of_year='2',
            day_of_week='*',
        )
        
        if created:
            self.stdout.write('  Created impossible crontab schedule (manual trigger only)')
        
        # Create the periodic task
        task = PeriodicTask.objects.create(
            name='Send Test Email',
            task='apps.scheduler.tasks.send_test_email_to_self',
            crontab=crontab,
            enabled=True,
            description='Sends test email to verify email configuration. Manual trigger only.'
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Successfully created task: {task.name}'
        ))
        self.stdout.write(f'  Task function: {task.task}')
        self.stdout.write(f'  Schedule: Manual trigger only')
        self.stdout.write(f'  Description: {task.description}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            '✓ "Send Test Email" task is now available in Scheduler Dashboard'
        ))
