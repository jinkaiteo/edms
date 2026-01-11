"""
Management command to create default Document Sources
Based on system_reinit.py canonical sources
"""
from django.core.management.base import BaseCommand
from apps.documents.models import DocumentSource


class Command(BaseCommand):
    help = 'Create default EDMS document sources'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default EDMS document sources...'))
        self.stdout.write('Based on system_reinit.py canonical sources')
        self.stdout.write('')
        
        # Define canonical document sources from system_reinit.py
        # These are the 3 core sources the system actually uses
        canonical_sources = [
            {
                'name': 'Original Digital Draft',
                'source_type': 'original_digital',
                'description': 'Original digital draft uploaded to EDMS',
                'requires_verification': False,
                'requires_signature': False,
                'is_active': True
            },
            {
                'name': 'Scanned Original',
                'source_type': 'scanned_original',
                'description': 'Digital file created directly from the original physical document',
                'requires_verification': True,
                'requires_signature': False,
                'is_active': True
            },
            {
                'name': 'Scanned Copy',
                'source_type': 'scanned_copy',
                'description': 'Digital file created by scanning a photocopy of the original document',
                'requires_verification': True,
                'requires_signature': False,
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for source_data in canonical_sources:
            name = source_data.pop('name')
            
            doc_source, created = DocumentSource.objects.get_or_create(
                name=name,
                defaults=source_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {doc_source.name} ({doc_source.source_type})')
                )
            else:
                # Update if changed
                updated = False
                for field, value in source_data.items():
                    if getattr(doc_source, field) != value:
                        setattr(doc_source, field, value)
                        updated = True
                
                if updated:
                    doc_source.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ↻ Updated: {doc_source.name} ({doc_source.source_type})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  - Exists: {doc_source.name} ({doc_source.source_type})')
                    )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed! Created: {created_count}, Updated: {updated_count}, '
                f'Unchanged: {3 - created_count - updated_count}'
            )
        )
        self.stdout.write('')
        self.stdout.write('Available document sources:')
        
        all_sources = DocumentSource.objects.filter(is_active=True).order_by('name')
        for doc_source in all_sources:
            verification = '✓ Verification required' if doc_source.requires_verification else '- No verification'
            signature = '✓ Signature required' if doc_source.requires_signature else '- No signature'
            self.stdout.write(f'  - {doc_source.name} ({doc_source.source_type})')
            self.stdout.write(f'    {verification}, {signature}')
