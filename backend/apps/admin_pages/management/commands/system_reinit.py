"""
Management command to reinitialize the system with default data.
Bypasses web authentication for easier testing.
"""
from django.core.management.base import BaseCommand
from apps.admin_pages.services import SystemReinitService

class Command(BaseCommand):
    help = 'Reinitialize system with default users, roles, and workflow configurations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting system reinitialization...'))
        
        try:
            service = SystemReinitService()
            result = service.reinitialize_system()
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f'✅ System reinitialized successfully!'))
                self.stdout.write(f"   Users created: {result.get('users_created', 0)}")
                self.stdout.write(f"   Roles created: {result.get('roles_created', 0)}")
            else:
                self.stdout.write(self.style.ERROR(f'❌ Reinitialization failed: {result.get("error")}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise
