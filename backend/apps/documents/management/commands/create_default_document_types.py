"""
Management command to create default Document Types
Based on system_reinit.py canonical types
"""
from django.core.management.base import BaseCommand
from apps.documents.models import DocumentType


class Command(BaseCommand):
    help = 'Create default EDMS document types'

    def handle(self, *args, **options):
        from apps.users.models import User
        
        self.stdout.write(self.style.SUCCESS('Creating default EDMS document types...'))
        self.stdout.write('Based on system_reinit.py canonical types')
        self.stdout.write('')
        
        # Get or create system user for created_by field
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(self.style.ERROR('No superuser found! Create a superuser first.'))
            return
        
        # Define canonical document types from Dev_Docs and system_reinit.py
        canonical_types = [
            {
                'code': 'POL',
                'name': 'Policy',
                'numbering_prefix': 'POL',
                'description': 'Company policies and governance documents',
                'template_required': False,
                'approval_required': True,
                'review_required': True,
                'retention_years': 7,
                'is_active': True
            },
            {
                'code': 'SOP',
                'name': 'Standard Operating Procedure',
                'numbering_prefix': 'SOP',
                'description': 'Standard operating procedures for business processes',
                'template_required': False,
                'approval_required': True,
                'review_required': True,
                'retention_years': 5,
                'is_active': True
            },
            {
                'code': 'WI',
                'name': 'Work Instruction',
                'numbering_prefix': 'WI',
                'description': 'Detailed work instructions for specific tasks',
                'template_required': False,
                'approval_required': True,
                'review_required': True,
                'retention_years': 5,
                'is_active': True
            },
            {
                'code': 'MAN',
                'name': 'Manual',
                'numbering_prefix': 'MAN',
                'description': 'User manuals and handbooks',
                'template_required': False,
                'approval_required': True,
                'review_required': True,
                'retention_years': 5,
                'is_active': True
            },
            {
                'code': 'FRM',
                'name': 'Form',
                'numbering_prefix': 'FRM',
                'description': 'Forms and templates for data collection',
                'template_required': False,
                'approval_required': True,
                'review_required': True,
                'retention_years': 3,
                'is_active': True
            },
            {
                'code': 'REC',
                'name': 'Record',
                'numbering_prefix': 'REC',
                'description': 'Business records and completed forms',
                'template_required': False,
                'approval_required': False,
                'review_required': False,
                'retention_years': 7,
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for type_data in canonical_types:
            code = type_data.pop('code')
            numbering_prefix = type_data.pop('numbering_prefix')
            name = type_data.pop('name')
            
            doc_type, created = DocumentType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'numbering_prefix': numbering_prefix,
                    'created_by': system_user,
                    **type_data
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {doc_type.code} - {doc_type.name}')
                )
            else:
                # Update if changed
                updated = False
                if doc_type.name != name:
                    doc_type.name = name
                    updated = True
                if doc_type.numbering_prefix != numbering_prefix:
                    doc_type.numbering_prefix = numbering_prefix
                    updated = True
                if not doc_type.is_active:
                    doc_type.is_active = True
                    updated = True
                    
                if updated:
                    doc_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ↻ Updated: {doc_type.code} - {doc_type.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  - Exists: {doc_type.code} - {doc_type.name}')
                    )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed! Created: {created_count}, Updated: {updated_count}, '
                f'Unchanged: {6 - created_count - updated_count}'
            )
        )
        self.stdout.write('')
        self.stdout.write('Available document types:')
        
        all_types = DocumentType.objects.filter(is_active=True).order_by('code')
        for doc_type in all_types:
            self.stdout.write(f'  - {doc_type.code}: {doc_type.name}')
