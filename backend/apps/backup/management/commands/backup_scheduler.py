"""
Management command to set up and manage backup schedules.

Usage:
    python manage.py backup_scheduler --create-config
    python manage.py backup_scheduler --list-configs
    python manage.py backup_scheduler --enable daily_backup
    python manage.py backup_scheduler --disable daily_backup
    python manage.py backup_scheduler --run-scheduled
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, time, timedelta

from apps.backup.models import BackupConfiguration
from apps.backup.services import backup_service


class Command(BaseCommand):
    help = 'Manage backup schedules and configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-config',
            action='store_true',
            help='Create default backup configurations'
        )
        parser.add_argument(
            '--list-configs',
            action='store_true',
            help='List all backup configurations'
        )
        parser.add_argument(
            '--enable',
            type=str,
            help='Enable backup configuration by name'
        )
        parser.add_argument(
            '--disable',
            type=str,
            help='Disable backup configuration by name'
        )
        parser.add_argument(
            '--run-scheduled',
            action='store_true',
            help='Run all scheduled backups that are due'
        )
        parser.add_argument(
            '--purge-hourly',
            action='store_true',
            help='Permanently delete disabled HOURLY configurations from the database'
        )

    def handle(self, *args, **options):
        if options['create_config']:
            self.create_default_configurations()
        elif options['list_configs']:
            self.list_configurations()
        elif options['enable']:
            self.enable_configuration(options['enable'])
        elif options['disable']:
            self.disable_configuration(options['disable'])
        elif options['run_scheduled']:
            self.run_scheduled_backups()
        elif options['purge_hourly']:
            self.purge_hourly_configurations()
        else:
            self.stdout.write("No action specified. Use --help for options.")

    def create_default_configurations(self):
        """Create default backup configurations."""
        self.stdout.write("Creating default backup configurations...")
        
        configs = [
            {
                'name': 'daily_full_backup',
                'description': 'Daily full system backup',
                'backup_type': 'FULL',
                'frequency': 'DAILY',
                'schedule_time': time(2, 0),  # 2 AM
                'retention_days': 30,
                'max_backups': 10,
                'storage_path': '/opt/edms/backups/daily',
            },
            {
                'name': 'weekly_export',
                'description': 'Weekly export package for migration',
                'backup_type': 'FULL',
                'frequency': 'WEEKLY',
                'schedule_time': time(3, 0),  # 3 AM
                'schedule_days': [6],  # Sunday
                'retention_days': 90,
                'max_backups': 12,
                'storage_path': '/opt/edms/backups/export',
            }
        ]
        
        # Get a system user for created_by field
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Try to get a superuser, or create a system user
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            # Create a system user if no superuser exists
            system_user, created = User.objects.get_or_create(
                username='system_backup',
                defaults={
                    'email': 'system@localhost',
                    'is_active': True,
                    'is_staff': True
                }
            )
        
        for config_data in configs:
            # Add the created_by user to the config data
            config_data['created_by'] = system_user
            
            config, created = BackupConfiguration.objects.get_or_create(
                name=config_data['name'],
                defaults=config_data
            )
            
            if created:
                self.stdout.write(f"✓ Created: {config.name}")
            else:
                # Update schedule/retention for daily_full_backup if needed
                if config.name == 'daily_full_backup':
                    changed = False
                    if config.schedule_time != time(2,0):
                        config.schedule_time = time(2,0)
                        changed = True
                    if config.retention_days != 30:
                        config.retention_days = 30
                        changed = True
                    if config.backup_type != 'FULL':
                        config.backup_type = 'FULL'
                        changed = True
                    if config.frequency != 'DAILY':
                        config.frequency = 'DAILY'
                        changed = True
                    if not config.is_enabled:
                        config.is_enabled = True
                        config.status = 'ACTIVE'
                        changed = True
                    if changed:
                        config.save()
                        self.stdout.write(f"↻ Updated: {config.name}")
                    else:
                        self.stdout.write(f"→ Exists: {config.name}")
                else:
                    self.stdout.write(f"→ Exists: {config.name}")
        
        # Disable any existing HOURLY configurations
        disabled = BackupConfiguration.objects.filter(frequency='HOURLY').update(is_enabled=False, status='INACTIVE')
        if disabled:
            self.stdout.write(self.style.WARNING(f"Disabled {disabled} HOURLY configuration(s)"))
        
        self.stdout.write(
            self.style.SUCCESS("Default backup configurations created/updated")
        )

    def purge_hourly_configurations(self):
        """Permanently delete disabled HOURLY configurations."""
        qs = BackupConfiguration.objects.filter(frequency='HOURLY')
        count = qs.count()
        # Only delete those not enabled to avoid surprises
        disabled_qs = qs.filter(is_enabled=False)
        deleted = disabled_qs.delete()[0]
        self.stdout.write(self.style.WARNING(f"Requested purge of HOURLY: found={count}, deleted_disabled={deleted}"))

    def list_configurations(self):
        """List all backup configurations."""
        configs = BackupConfiguration.objects.all().order_by('name')
        
        if not configs:
            self.stdout.write("No backup configurations found")
            return
        
        self.stdout.write("Backup Configurations:")
        self.stdout.write("=" * 60)
        
        for config in configs:
            status = "✓ ACTIVE" if config.is_enabled else "✗ DISABLED"
            self.stdout.write(f"{config.name:<20} {config.backup_type:<12} {status}")
            self.stdout.write(f"  Description: {config.description}")
            self.stdout.write(f"  Frequency: {config.frequency}")
            if config.schedule_time:
                self.stdout.write(f"  Schedule: {config.schedule_time}")
            self.stdout.write(f"  Storage: {config.storage_path}")
            self.stdout.write("")

    def enable_configuration(self, config_name):
        """Enable a backup configuration."""
        try:
            config = BackupConfiguration.objects.get(name=config_name)
            config.is_enabled = True
            config.status = 'ACTIVE'
            config.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"Enabled backup configuration: {config_name}")
            )
            
        except BackupConfiguration.DoesNotExist:
            raise CommandError(f"Configuration not found: {config_name}")

    def disable_configuration(self, config_name):
        """Disable a backup configuration."""
        try:
            config = BackupConfiguration.objects.get(name=config_name)
            config.is_enabled = False
            config.status = 'INACTIVE'
            config.save()
            
            self.stdout.write(
                self.style.WARNING(f"Disabled backup configuration: {config_name}")
            )
            
        except BackupConfiguration.DoesNotExist:
            raise CommandError(f"Configuration not found: {config_name}")

    def run_scheduled_backups(self):
        """Run all scheduled backups that are due."""
        self.stdout.write("Checking for scheduled backups...")
        
        now = timezone.now()
        current_time = now.time()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        
        # Get active configurations
        configs = BackupConfiguration.objects.filter(
            is_enabled=True,
            status='ACTIVE'
        )
        
        due_configs = []
        
        for config in configs:
            if self._is_backup_due(config, now, current_time, current_day):
                due_configs.append(config)
        
        if not due_configs:
            self.stdout.write("No scheduled backups are due")
            return
        
        self.stdout.write(f"Found {len(due_configs)} scheduled backup(s) due:")
        
        for config in due_configs:
            self.stdout.write(f"Running: {config.name}")
            try:
                job = backup_service.execute_backup(config)
                self.stdout.write(f"✓ Completed: {job.job_name}")
            except Exception as e:
                self.stdout.write(f"✗ Failed: {str(e)}")

    def _is_backup_due(self, config, now, current_time, current_day):
        """Check if a backup is due based on schedule."""
        if config.frequency == 'ON_DEMAND':
            return False
        
        # Get last backup for this configuration
        from apps.backup.models import BackupJob
        last_backup = BackupJob.objects.filter(
            configuration=config,
            status='COMPLETED'
        ).order_by('-created_at').first()
        
        if config.frequency == 'HOURLY':
            # Run every hour
            if last_backup:
                time_since_last = now - last_backup.created_at
                return time_since_last >= timedelta(hours=1)
            return True
        
        elif config.frequency == 'DAILY':
            # Run once per day at scheduled time
            if last_backup and last_backup.created_at.date() == now.date():
                return False  # Already ran today
            
            if config.schedule_time:
                # Check if current time is past scheduled time
                return current_time >= config.schedule_time
            return True
        
        elif config.frequency == 'WEEKLY':
            # Run on specific days at scheduled time
            if last_backup:
                days_since_last = (now.date() - last_backup.created_at.date()).days
                if days_since_last < 7:
                    return False
            
            # Check if today is a scheduled day
            if config.schedule_days and current_day not in config.schedule_days:
                return False
            
            if config.schedule_time:
                return current_time >= config.schedule_time
            return True
        
        elif config.frequency == 'MONTHLY':
            # Run once per month
            if last_backup:
                # Check if already ran this month
                if (last_backup.created_at.year == now.year and 
                    last_backup.created_at.month == now.month):
                    return False
            
            # Run on first day of month or at scheduled time
            if config.schedule_time:
                return current_time >= config.schedule_time
            return now.day == 1
        
        return False