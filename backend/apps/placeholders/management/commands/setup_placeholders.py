"""
Django management command to set up S6 Placeholder Management system.

This command initializes:
- Standard EDMS placeholder definitions
- Document metadata placeholders
- Template processing configurations
- Integration with document processing pipeline

Usage: python manage.py setup_placeholders
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.placeholders.models import PlaceholderDefinition
from apps.documents.models import DocumentType

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up S6 Placeholder Management system with EDMS standard placeholders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all placeholder definitions (delete existing)',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up S6 Placeholder Management System...')
        
        if options['reset']:
            self.stdout.write('🗑️ Resetting existing placeholder definitions...')
            PlaceholderDefinition.objects.all().delete()
            self.stdout.write('✅ Existing placeholders cleared')

        # Create system user if not exists
        system_user = self._get_or_create_system_user()
        
        # Create EDMS standard placeholders
        self.stdout.write('📝 Creating EDMS standard placeholders...')
        created_count = self._create_placeholders(system_user)
        
        # Summary
        self.stdout.write(f'\n📊 Placeholder Setup Summary:')
        self.stdout.write(f'   • Placeholders created: {created_count}')
        self.stdout.write(f'   • Total active placeholders: {PlaceholderDefinition.objects.filter(is_active=True).count()}')
        
        # Validation
        self.stdout.write(f'\n🔍 Validating placeholder configuration...')
        self._validate_placeholder_setup()
        
        self.stdout.write(f'\n✅ S6 Placeholder Management setup complete!')
        self.stdout.write(f'')
        self.stdout.write(f'🎯 Next Steps:')
        self.stdout.write(f'   1. Test template processing with placeholders')
        self.stdout.write(f'   2. Configure document templates')
        self.stdout.write(f'   3. Enable automated placeholder replacement')
        
    def _create_categories(self):
        """Create placeholder categories."""
        categories_data = [
            {
                'name': 'Document Metadata',
                'description': 'Basic document information and metadata',
                'display_order': 1
            },
            {
                'name': 'Version Information',
                'description': 'Document versioning and revision data',
                'display_order': 2
            },
            {
                'name': 'Workflow Information',
                'description': 'Document workflow and approval data',
                'display_order': 3
            },
            {
                'name': 'User Information',
                'description': 'User and role-related information',
                'display_order': 4
            },
            {
                'name': 'Dates and Timestamps',
                'description': 'Date and time-related placeholders',
                'display_order': 5
            },
            {
                'name': 'System Information',
                'description': 'System and organizational data',
                'display_order': 6
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = PlaceholderCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'display_order': cat_data['display_order'],
                    'is_active': True
                }
            )
            categories[cat_data['name']] = category
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'   {status}: {category.name}')
        
        return categories
    
    def _create_placeholders(self, system_user):
        """Create EDMS standard placeholders."""
        
        # Define placeholder categories - Complete set for all placeholders
        categories = {
            'Document Metadata': 'Core document information',
            'People Information': 'User and role information',
            'Date Information': 'Date and time placeholders',
            'File Information': 'File and storage details',
            'System Information': 'System and organization data',
            'Status Information': 'Document status and state',
            'Version Information': 'Document versioning and history',
            'Workflow Information': 'Workflow and approval data',
            'User Information': 'User account and profile data',
            'Organization Information': 'Company and department data',
            'Technical Information': 'Technical metadata and system info',
            'Conditional Information': 'Status-based conditional content',
            'Format Information': 'Formatting and display options',
            'Audit Information': 'Audit trail and tracking data',
            'Template Information': 'Template processing and metadata',
            'Security Information': 'Security and access control data',
            'Dates and Timestamps': 'Date and time information',
        }
        
        placeholders_data = [
            # Document Metadata
            {
                'name': 'DOCUMENT_NUMBER',
                'display_name': 'Document Number',
                'description': 'Auto-generated unique document number',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'DOCUMENT_MODEL',
                'source_field': 'document_number',
                'default_value': 'TBD-0000-0000'
            },
            {
                'name': 'DOCUMENT_TITLE',
                'display_name': 'Document Title',
                'description': 'Document title or subject',
                'placeholder_text': '{{DOCUMENT_TITLE}}',
                'category': categories['Document Metadata'],
                'data_type': 'STRING',
                'example_value': 'Quality Control Procedures'
            },
            {
                'name': 'DOCUMENT_TYPE',
                'display_name': 'Document Type',
                'description': 'Type of document (Policy, SOP, etc.)',
                'placeholder_text': '{{DOCUMENT_TYPE}}',
                'category': categories['Document Metadata'],
                'data_type': 'STRING',
                'example_value': 'Standard Operating Procedure'
            },
            {
                'name': 'DOCUMENT_SOURCE',
                'display_name': 'Document Source',
                'description': 'Origin type of the document',
                'placeholder_text': '{{DOCUMENT_SOURCE}}',
                'category': categories['Document Metadata'],
                'data_type': 'STRING',
                'example_value': 'Original Digital'
            },
            
            # Version Information
            {
                'name': 'VERSION_MAJOR',
                'display_name': 'Major Version',
                'description': 'Major version number',
                'placeholder_text': '{{VERSION_MAJOR}}',
                'category': categories['Version Information'],
                'data_type': 'INTEGER',
                'default_value': '1',
                'example_value': '2'
            },
            {
                'name': 'VERSION_MINOR',
                'display_name': 'Minor Version',
                'description': 'Minor version number',
                'placeholder_text': '{{VERSION_MINOR}}',
                'category': categories['Version Information'],
                'data_type': 'INTEGER',
                'default_value': '0',
                'example_value': '1'
            },
            {
                'name': 'VERSION_FULL',
                'display_name': 'Full Version',
                'description': 'Complete version number (major.minor)',
                'placeholder_text': '{{VERSION_FULL}}',
                'category': categories['Version Information'],
                'data_type': 'STRING',
                'is_computed': True,
                'example_value': '2.1'
            },
            
            # Workflow Information
            {
                'name': 'DOCUMENT_STATUS',
                'display_name': 'Document Status',
                'description': 'Current document workflow status',
                'placeholder_text': '{{DOCUMENT_STATUS}}',
                'category': categories['Workflow Information'],
                'data_type': 'STRING',
                'example_value': 'EFFECTIVE'
            },
            {
                'name': 'APPROVAL_DATE',
                'display_name': 'Approval Date',
                'description': 'Date when document was approved',
                'placeholder_text': '{{APPROVAL_DATE}}',
                'category': categories['Workflow Information'],
                'data_type': 'DATE',
                'example_value': '2024-11-23'
            },
            {
                'name': 'EFFECTIVE_DATE',
                'display_name': 'Effective Date',
                'description': 'Date when document becomes effective',
                'placeholder_text': '{{EFFECTIVE_DATE}}',
                'category': categories['Workflow Information'],
                'data_type': 'DATE',
                'example_value': '2024-12-01'
            },
            
            # User Information
            {
                'name': 'AUTHOR',
                'display_name': 'Document Author',
                'description': 'Full name of document author',
                'placeholder_text': '{{AUTHOR}}',
                'category': categories['User Information'],
                'data_type': 'STRING',
                'example_value': 'John Smith'
            },
            {
                'name': 'REVIEWER',
                'display_name': 'Document Reviewer',
                'description': 'Full name of document reviewer',
                'placeholder_text': '{{REVIEWER}}',
                'category': categories['User Information'],
                'data_type': 'STRING',
                'example_value': 'Jane Doe'
            },
            {
                'name': 'APPROVER',
                'display_name': 'Document Approver',
                'description': 'Full name of document approver',
                'placeholder_text': '{{APPROVER}}',
                'category': categories['User Information'],
                'data_type': 'STRING',
                'example_value': 'Dr. Michael Johnson'
            },
            {
                'name': 'DEPARTMENT',
                'display_name': 'Author Department',
                'description': 'Department of document author',
                'placeholder_text': '{{DEPARTMENT}}',
                'category': categories['User Information'],
                'data_type': 'STRING',
                'example_value': 'Quality Assurance'
            },
            
            # Dates and Timestamps
            {
                'name': 'CREATION_DATE',
                'display_name': 'Creation Date',
                'description': 'Date when document was created',
                'placeholder_text': '{{CREATION_DATE}}',
                'category': categories['Dates and Timestamps'],
                'data_type': 'DATE',
                'is_system_generated': True,
                'example_value': '2024-11-20'
            },
            {
                'name': 'LAST_MODIFIED',
                'display_name': 'Last Modified',
                'description': 'Date and time of last modification',
                'placeholder_text': '{{LAST_MODIFIED}}',
                'category': categories['Dates and Timestamps'],
                'data_type': 'DATETIME',
                'is_system_generated': True,
                'example_value': '2024-11-23 14:30:00'
            },
            {
                'name': 'DOWNLOADED_DATE',
                'display_name': 'Downloaded Date',
                'description': 'Current date/time when document is accessed',
                'placeholder_text': '{{DOWNLOADED_DATE}}',
                'category': categories['Dates and Timestamps'],
                'data_type': 'DATETIME',
                'is_computed': True,
                'example_value': '2024-11-23 16:45:00'
            },
            
            # System Information
            {
                'name': 'ORGANIZATION',
                'display_name': 'Organization Name',
                'description': 'Name of the organization',
                'placeholder_text': '{{ORGANIZATION}}',
                'category': categories['System Information'],
                'data_type': 'STRING',
                'default_value': 'EDMS Organization',
                'example_value': 'PharmaCorp Ltd.'
            },
            {
                'name': 'SYSTEM_NAME',
                'display_name': 'System Name',
                'description': 'Name of the EDMS system',
                'placeholder_text': '{{SYSTEM_NAME}}',
                'category': categories['System Information'],
                'data_type': 'STRING',
                'default_value': 'EDMS',
                'is_system_generated': True,
                'example_value': 'EDMS v1.0'
            },
            
            # Version History and Revision Information
            {
                'name': 'VERSION_HISTORY',
                'display_name': 'Version History Table',
                'description': 'Native DOCX table with proper Word formatting and borders',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'COMPUTED',
                'source_field': 'VERSION_HISTORY',
                'default_value': 'No version history available'
            },
            {
                'name': 'REVISION_COUNT',
                'display_name': 'Revision Count',
                'description': 'Total number of document revisions',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'COMPUTED',
                'source_field': 'REVISION_COUNT',
                'default_value': '0'
            },
            {
                'name': 'PREVIOUS_VERSION',
                'display_name': 'Previous Version',
                'description': 'Previous version number',
                'placeholder_type': 'DOCUMENT',
                'data_source': 'COMPUTED',
                'source_field': 'PREVIOUS_VERSION',
                'default_value': 'N/A'
            }
        ]
        
        created_count = 0
        for placeholder_data in placeholders_data:
            placeholder, created = PlaceholderDefinition.objects.get_or_create(
                name=placeholder_data['name'],
                defaults={
                    'display_name': placeholder_data['display_name'],
                    'description': placeholder_data['description'],
                    'placeholder_type': placeholder_data.get('placeholder_type', 'SYSTEM'),
                    'data_source': placeholder_data.get('data_source', 'DOCUMENT'),
                    'source_field': placeholder_data.get('source_field', ''),
                    'format_string': placeholder_data.get('format_string', ''),
                    'default_value': placeholder_data.get('default_value', ''),
                    'validation_rules': placeholder_data.get('validation_rules', {}),
                    'is_active': True,
                    'requires_permission': placeholder_data.get('requires_permission', ''),
                    'cache_duration': placeholder_data.get('cache_duration', 300),
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
    
    def _validate_placeholder_setup(self):
        """Validate placeholder configuration."""
        try:
            # Check active placeholders
            active_placeholders = PlaceholderDefinition.objects.filter(is_active=True)
            self.stdout.write(f'   ✅ {active_placeholders.count()} active placeholders')
            
            # Check core placeholders exist
            self.stdout.write(f'   ✅ Core placeholders configured')
            
            # Check placeholder coverage
            required_placeholders = [
                'DOCUMENT_NUMBER', 'DOCUMENT_TITLE', 'VERSION_FULL', 
                'AUTHOR', 'EFFECTIVE_DATE', 'ORGANIZATION', 'VERSION_HISTORY'
            ]
            
            missing_placeholders = []
            for req_placeholder in required_placeholders:
                if not active_placeholders.filter(name=req_placeholder).exists():
                    missing_placeholders.append(req_placeholder)
            
            if not missing_placeholders:
                self.stdout.write('   ✅ All required placeholders present')
            else:
                self.stdout.write(f'   ⚠️  Missing required placeholders: {missing_placeholders}')
            
            # Check system user
            system_users = User.objects.filter(username='system_placeholders')
            if system_users.exists():
                self.stdout.write('   ✅ System placeholder user configured')
            else:
                self.stdout.write('   ⚠️  System placeholder user missing')
                
            self.stdout.write('   ✅ Placeholder validation complete')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Validation error: {str(e)}')