# Generated migration for fixing document versioning consistency
# This migration:
# 1. Updates document numbers to use zero-padded version format
# 2. Updates database constraints for version limits
# 3. Ensures all documents have consistent versioning format

from django.db import migrations, models
import django.core.validators


def update_document_numbers_to_zero_padded(apps, schema_editor):
    """Update existing document numbers to use zero-padded version format."""
    Document = apps.get_model('documents', 'Document')
    
    updated_count = 0
    for document in Document.objects.all():
        # Extract base number and rebuild with zero-padded version
        base_number = document.document_number
        
        # If document already has version suffix, extract base
        if '-v' in base_number:
            base_number = base_number.split('-v')[0]
        
        # Rebuild with zero-padded version
        new_document_number = f"{base_number}-v{document.version_major:02d}.{document.version_minor:02d}"
        
        if new_document_number != document.document_number:
            document.document_number = new_document_number
            document.save()
            updated_count += 1
    
    print(f"Updated {updated_count} document numbers to zero-padded format")


def reverse_document_numbers_to_old_format(apps, schema_editor):
    """Reverse zero-padded format back to original (for migration rollback)."""
    Document = apps.get_model('documents', 'Document')
    
    reverted_count = 0
    for document in Document.objects.all():
        # Convert back to old format
        base_number = document.document_number
        
        # If document has zero-padded version, convert back
        if '-v' in base_number:
            base_part, version_part = base_number.split('-v', 1)
            # Remove zero padding (e.g., "01.00" -> "1.0")
            major_str, minor_str = version_part.split('.')
            major = int(major_str)
            minor = int(minor_str)
            
            if major == 1 and minor == 0:
                # v1.0 documents had no version suffix in old format
                new_document_number = base_part
            else:
                # Other versions keep suffix but without padding
                new_document_number = f"{base_part}-v{major}.{minor}"
            
            if new_document_number != document.document_number:
                document.document_number = new_document_number
                document.save()
                reverted_count += 1
    
    print(f"Reverted {reverted_count} document numbers to old format")


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_add_obsolescence_fields'),
    ]

    operations = [
        # Update version field validators
        migrations.AlterField(
            model_name='document',
            name='version_major',
            field=models.PositiveIntegerField(
                default=1, 
                help_text='Major version number (1-99)', 
                validators=[
                    django.core.validators.MinValueValidator(1), 
                    django.core.validators.MaxValueValidator(99)
                ]
            ),
        ),
        migrations.AlterField(
            model_name='document',
            name='version_minor',
            field=models.PositiveIntegerField(
                default=0, 
                help_text='Minor version number (0-99)', 
                validators=[
                    django.core.validators.MinValueValidator(0), 
                    django.core.validators.MaxValueValidator(99)
                ]
            ),
        ),
        
        # Remove old constraints
        migrations.RemoveConstraint(
            model_name='document',
            name='version_major_positive',
        ),
        migrations.RemoveConstraint(
            model_name='document',
            name='version_minor_non_negative',
        ),
        
        # Add new range constraints
        migrations.AddConstraint(
            model_name='document',
            constraint=models.CheckConstraint(
                check=models.Q(version_major__gte=1, version_major__lte=99), 
                name='version_major_range'
            ),
        ),
        migrations.AddConstraint(
            model_name='document',
            constraint=models.CheckConstraint(
                check=models.Q(version_minor__gte=0, version_minor__lte=99), 
                name='version_minor_range'
            ),
        ),
        
        # Update document numbers to zero-padded format
        migrations.RunPython(
            update_document_numbers_to_zero_padded,
            reverse_document_numbers_to_old_format
        ),
    ]