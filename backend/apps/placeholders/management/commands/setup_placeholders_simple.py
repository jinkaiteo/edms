"""
Simplified Django management command to set up S6 Placeholder Management system.

This command creates the essential EDMS placeholders using the actual model structure.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.placeholders.models import PlaceholderDefinition

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up S6 Placeholder Management system with essential EDMS placeholders'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up S6 Placeholder Management System...')
        
        # Create system user if not exists
        system_user = self._get_or_create_system_user()
        
        # Create essential EDMS placeholders
        self.stdout.write('📝 Creating essential EDMS placeholders...')
        created_count = self._create_essential_placeholders(system_user)
        
        # Summary
        self.stdout.write(f'\n📊 Placeholder Setup Summary:')
        self.stdout.write(f'   • Placeholders created: {created_count}')
        self.stdout.write(f'   • Total active placeholders: {PlaceholderDefinition.objects.filter(is_active=True).count()}')
        
        self.stdout.write(f'\n✅ S6 Placeholder Management setup complete!')
        
    def _create_essential_placeholders(self, system_user):
        """Create essential EDMS placeholders."""
        placeholders_data = [
            {
                'name': 'DOCUMENT_NUMBER',
                'display_name': 'Document Number',
                'description': 'Auto-generated unique document number',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'DOCUMENT_MODEL',
                'source_field': 'document_number',
                'default_value': 'TBD-0000-0000',
                'date_format': '%Y-%m-%d'
            },
            {
                'name': 'DOCUMENT_TITLE',
                'display_name': 'Document Title',
                'description': 'Document title or subject',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'DOCUMENT_MODEL',
                'source_field': 'title',
                'default_value': 'Untitled Document',
                'date_format': '%Y-%m-%d'
            },
            {
                'name': 'VERSION_MAJOR',
                'display_name': 'Major Version',
                'description': 'Major version number',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'DOCUMENT_MODEL',
                'source_field': 'version_major',
                'default_value': '1',
                'date_format': '%Y-%m-%d'
            },
            {
                'name': 'VERSION_MINOR',
                'display_name': 'Minor Version',
                'description': 'Minor version number',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'DOCUMENT_MODEL',
                'source_field': 'version_minor',
                'default_value': '0',
                'date_format': '%Y-%m-%d'
            },
            {
                'name': 'AUTHOR',
                'display_name': 'Document Author',
                'description': 'Full name of document author',
                'placeholder_type': 'USER',
                'data_source': 'USER_MODEL',
                'source_field': 'get_full_name',
                'default_value': 'Unknown Author',
                'date_format': '%Y-%m-%d'
            },
            {
                'name': 'EFFECTIVE_DATE',
                'display_name': 'Effective Date',
                'description': 'Date when document becomes effective',
                'placeholder_type': 'DATE',
                'data_source': 'DOCUMENT_MODEL',
                'source_field': 'effective_date',
                'default_value': 'TBD',
                'date_format': '%Y-%m-%d'
            },
            {
                'name': 'ORGANIZATION',
                'display_name': 'Organization Name',
                'description': 'Name of the organization',
                'placeholder_type': 'SYSTEM',
                'data_source': 'SYSTEM_CONFIG',
                'source_field': 'ORGANIZATION_NAME',
                'default_value': 'EDMS Organization',
                'date_format': '%Y-%m-%d'
            }
        ]
        
        created_count = 0
        for placeholder_data in placeholders_data:
            placeholder, created = PlaceholderDefinition.objects.get_or_create(
                name=placeholder_data['name'],
                defaults={
                    'display_name': placeholder_data['display_name'],
                    'description': placeholder_data['description'],
                    'placeholder_type': placeholder_data['placeholder_type'],
                    'data_source': placeholder_data['data_source'],
                    'source_field': placeholder_data['source_field'],
                    'default_value': placeholder_data['default_value'],
                    'date_format': placeholder_data['date_format'],
                    'is_active': True,
                    'created_by': system_user
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'   ✅ Created: {placeholder.display_name}')
            else:
                self.stdout.write(f'   ℹ️  Exists: {placeholder.display_name}')
        
        return created_count
    
    def _get_or_create_system_user(self):
        """Get or create system user for placeholder management."""
        try:
            system_user, created = User.objects.get_or_create(
                username='system_placeholders',
                defaults={
                    'email': 'placeholders@edms.local',
                    'first_name': 'System',
                    'last_name': 'Placeholders',
                    'is_active': True,
                    'is_staff': False,
                    'department': 'System',
                    'position': 'Placeholder Manager'
                }
            )
            
            if created:
                self.stdout.write('✅ Created system placeholder user')
            else:
                self.stdout.write('ℹ️  System placeholder user already exists')
                
            return system_user
            
        except Exception as e:
            self.stdout.write(f'❌ Error creating system user: {str(e)}')
            # Fallback to first superuser
            return User.objects.filter(is_superuser=True).first()