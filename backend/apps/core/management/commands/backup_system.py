"""
Django management command for hybrid backup system.
Usage: python manage.py backup_system
"""
from django.core.management.base import BaseCommand
import subprocess
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Create a full system backup using hybrid approach (pg_dump + storage files)'

    def handle(self, *args, **options):
        script_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / 'scripts' / 'backup-hybrid.sh'
        
        self.stdout.write('=' * 60)
        self.stdout.write('Starting Hybrid Backup...')
        self.stdout.write('=' * 60)
        
        if not script_path.exists():
            self.stdout.write(self.style.ERROR(f'Backup script not found: {script_path}'))
            return
        
        try:
            result = subprocess.run(
                ['/bin/bash', str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(script_path.parent.parent)
            )
            
            self.stdout.write(result.stdout)
            self.stdout.write(self.style.SUCCESS('\n✅ Backup completed successfully!'))
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Backup failed!'))
            self.stdout.write(e.stderr)
            raise
