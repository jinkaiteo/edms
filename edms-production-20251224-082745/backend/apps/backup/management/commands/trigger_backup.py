"""
Management command to trigger a backup manually.

Usage:
    python manage.py trigger_backup --config <config_name>
    python manage.py trigger_backup --type <backup_type>
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.backup.models import BackupConfiguration
from apps.backup.services import BackupService
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Trigger a backup manually'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            help='Name of backup configuration to use',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['FULL', 'INCREMENTAL', 'DIFFERENTIAL', 'DATABASE', 'FILES', 'EXPORT'],
            help='Type of backup to create (creates ad-hoc config)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output path for backup file (optional)',
        )

    def handle(self, *args, **options):
        if not options['config'] and not options['type']:
            raise CommandError('Must specify either --config or --type')
        
        backup_service = BackupService()
        
        if options['config']:
            # Use existing configuration
            self.trigger_from_config(options['config'], options.get('output'))
        else:
            # Create ad-hoc backup
            self.trigger_adhoc(options['type'], options.get('output'))

    def trigger_from_config(self, config_name, output_path=None):
        """Trigger backup using existing configuration."""
        try:
            config = BackupConfiguration.objects.get(name=config_name)
        except BackupConfiguration.DoesNotExist:
            raise CommandError(f'Configuration not found: {config_name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n🚀 Triggering backup: {config.name}\n'))
        self.stdout.write(f'   Type: {config.backup_type}')
        self.stdout.write(f'   Compression: {config.compression_enabled}')
        self.stdout.write(f'   Encryption: {config.encryption_enabled}')
        
        backup_service = BackupService()
        
        try:
            result = backup_service.create_backup(
                backup_type=config.backup_type,
                output_path=output_path,
                configuration=config,
            )
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Backup completed!'))
            self.stdout.write(f'   File: {result.get("backup_path")}')
            self.stdout.write(f'   Size: {result.get("backup_size")} bytes')
            self.stdout.write(f'   Checksum: {result.get("checksum", "N/A")[:16]}...')
            
        except Exception as e:
            raise CommandError(f'Backup failed: {str(e)}')

    def trigger_adhoc(self, backup_type, output_path=None):
        """Trigger ad-hoc backup."""
        self.stdout.write(self.style.SUCCESS(f'\n🚀 Creating {backup_type} backup\n'))
        
        backup_service = BackupService()
        
        try:
            result = backup_service.create_backup(
                backup_type=backup_type,
                output_path=output_path,
            )
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Backup completed!'))
            self.stdout.write(f'   File: {result.get("backup_path")}')
            self.stdout.write(f'   Size: {result.get("backup_size")} bytes')
            self.stdout.write(f'   Checksum: {result.get("checksum", "N/A")[:16]}...')
            
        except Exception as e:
            raise CommandError(f'Backup failed: {str(e)}')
