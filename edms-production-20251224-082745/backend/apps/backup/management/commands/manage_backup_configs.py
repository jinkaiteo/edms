"""
Management command for backup configuration operations.

Usage:
    python manage.py manage_backup_configs --list
    python manage.py manage_backup_configs --create
    python manage.py manage_backup_configs --enable <name>
    python manage.py manage_backup_configs --disable <name>
    python manage.py manage_backup_configs --delete <name>
    python manage.py manage_backup_configs --cleanup
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.backup.models import BackupConfiguration, BackupJob
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Manage backup configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all backup configurations',
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create a new backup configuration interactively',
        )
        parser.add_argument(
            '--enable',
            type=str,
            help='Enable a backup configuration by name',
        )
        parser.add_argument(
            '--disable',
            type=str,
            help='Disable a backup configuration by name',
        )
        parser.add_argument(
            '--delete',
            type=str,
            help='Delete a backup configuration by name',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old ad-hoc configurations',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show backup statistics',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_configurations()
        elif options['create']:
            self.create_configuration()
        elif options['enable']:
            self.enable_configuration(options['enable'])
        elif options['disable']:
            self.disable_configuration(options['disable'])
        elif options['delete']:
            self.delete_configuration(options['delete'])
        elif options['cleanup']:
            self.cleanup_adhoc()
        elif options['stats']:
            self.show_statistics()
        else:
            self.stdout.write(self.style.WARNING('Please specify an action. Use --help for options.'))

    def list_configurations(self):
        """List all backup configurations."""
        self.stdout.write(self.style.SUCCESS('\n📋 Backup Configurations:\n'))
        self.stdout.write('=' * 80)
        
        configs = BackupConfiguration.objects.all().order_by('name')
        
        if not configs.exists():
            self.stdout.write(self.style.WARNING('\nNo configurations found.'))
            return
        
        for config in configs:
            status_icon = '✅' if config.is_enabled else '⏸️'
            self.stdout.write(f'\n{status_icon} {config.name}')
            self.stdout.write(f'   Type: {config.backup_type} | Frequency: {config.frequency}')
            self.stdout.write(f'   Retention: {config.retention_days} days / {config.max_backups} max')
            self.stdout.write(f'   Schedule: {config.schedule_time}')
            self.stdout.write(f'   Status: {config.status}')
            self.stdout.write(f'   Compression: {config.compression_enabled} | Encryption: {config.encryption_enabled}')
            
            # Show job count
            job_count = BackupJob.objects.filter(configuration=config).count()
            completed = BackupJob.objects.filter(configuration=config, status='COMPLETED').count()
            self.stdout.write(f'   Jobs: {job_count} total ({completed} completed)')
        
        self.stdout.write('\n' + '=' * 80)

    def create_configuration(self):
        """Create a new backup configuration interactively."""
        self.stdout.write(self.style.SUCCESS('\n🏗️  Create New Backup Configuration\n'))
        
        # Get user input
        name = input('Configuration name: ')
        description = input('Description: ')
        
        backup_types = ['FULL', 'INCREMENTAL', 'DIFFERENTIAL', 'DATABASE', 'FILES', 'EXPORT']
        self.stdout.write(f'Backup types: {", ".join(backup_types)}')
        backup_type = input('Backup type: ').upper()
        
        frequencies = ['HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'ON_DEMAND']
        self.stdout.write(f'Frequencies: {", ".join(frequencies)}')
        frequency = input('Frequency: ').upper()
        
        schedule_time = input('Schedule time (HH:MM:SS, e.g., 02:00:00): ') or '00:00:00'
        retention_days = int(input('Retention days: ') or 30)
        max_backups = int(input('Max backups to keep: ') or 10)
        
        compression = input('Enable compression? (y/n): ').lower() == 'y'
        encryption = input('Enable encryption? (y/n): ').lower() == 'y'
        
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        
        # Create configuration
        config = BackupConfiguration.objects.create(
            name=name,
            description=description,
            backup_type=backup_type,
            frequency=frequency,
            schedule_time=schedule_time,
            retention_days=retention_days,
            max_backups=max_backups,
            compression_enabled=compression,
            encryption_enabled=encryption,
            is_enabled=True,
            status='ACTIVE',
            created_by=admin_user,
        )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Created configuration: {config.name}'))

    def enable_configuration(self, name):
        """Enable a backup configuration."""
        try:
            config = BackupConfiguration.objects.get(name=name)
            config.is_enabled = True
            config.status = 'ACTIVE'
            config.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Enabled: {name}'))
        except BackupConfiguration.DoesNotExist:
            raise CommandError(f'Configuration not found: {name}')

    def disable_configuration(self, name):
        """Disable a backup configuration."""
        try:
            config = BackupConfiguration.objects.get(name=name)
            config.is_enabled = False
            config.status = 'INACTIVE'
            config.save()
            self.stdout.write(self.style.SUCCESS(f'⏸️  Disabled: {name}'))
        except BackupConfiguration.DoesNotExist:
            raise CommandError(f'Configuration not found: {name}')

    def delete_configuration(self, name):
        """Delete a backup configuration."""
        try:
            config = BackupConfiguration.objects.get(name=name)
            
            # Check for associated jobs
            job_count = BackupJob.objects.filter(configuration=config).count()
            if job_count > 0:
                confirm = input(f'This configuration has {job_count} associated jobs. Delete anyway? (yes/no): ')
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.WARNING('Deletion cancelled.'))
                    return
            
            config.delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Deleted: {name}'))
        except BackupConfiguration.DoesNotExist:
            raise CommandError(f'Configuration not found: {name}')

    def cleanup_adhoc(self):
        """Clean up old ad-hoc configurations."""
        self.stdout.write(self.style.SUCCESS('\n🗑️  Cleaning Up Ad-Hoc Configurations\n'))
        
        cutoff_date = timezone.now() - timedelta(days=7)
        old_adhoc = BackupConfiguration.objects.filter(
            name__startswith='adhoc_',
            created_at__lt=cutoff_date
        )
        
        self.stdout.write(f'Found {old_adhoc.count()} old ad-hoc configurations (>7 days)\n')
        
        deleted_count = 0
        for config in old_adhoc:
            job_count = BackupJob.objects.filter(configuration=config).count()
            if job_count == 0:
                self.stdout.write(f'   Deleting: {config.name}')
                config.delete()
                deleted_count += 1
            else:
                self.stdout.write(f'   Keeping: {config.name} (has {job_count} jobs)')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Deleted {deleted_count} configurations'))

    def show_statistics(self):
        """Show backup statistics."""
        self.stdout.write(self.style.SUCCESS('\n📊 Backup Statistics\n'))
        self.stdout.write('=' * 80)
        
        # Configuration stats
        total_configs = BackupConfiguration.objects.count()
        active_configs = BackupConfiguration.objects.filter(is_enabled=True).count()
        
        self.stdout.write(f'\n📋 Configurations:')
        self.stdout.write(f'   Total: {total_configs}')
        self.stdout.write(f'   Active: {active_configs}')
        self.stdout.write(f'   Inactive: {total_configs - active_configs}')
        
        # Job stats
        from django.db.models import Count, Q
        
        job_stats = BackupJob.objects.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='COMPLETED')),
            failed=Count('id', filter=Q(status='FAILED')),
            running=Count('id', filter=Q(status='RUNNING')),
        )
        
        self.stdout.write(f'\n📦 Jobs:')
        self.stdout.write(f'   Total: {job_stats["total"]}')
        self.stdout.write(f'   ✅ Completed: {job_stats["completed"]}')
        self.stdout.write(f'   ❌ Failed: {job_stats["failed"]}')
        self.stdout.write(f'   🔄 Running: {job_stats["running"]}')
        
        # Recent jobs
        recent_jobs = BackupJob.objects.order_by('-created_at')[:5]
        if recent_jobs.exists():
            self.stdout.write(f'\n🕐 Recent Jobs:')
            for job in recent_jobs:
                status_icon = '✅' if job.status == 'COMPLETED' else '❌' if job.status == 'FAILED' else '🔄'
                self.stdout.write(f'   {status_icon} {job.backup_type} - {job.created_at.strftime("%Y-%m-%d %H:%M")}')
        
        self.stdout.write('\n' + '=' * 80)
