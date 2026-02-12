# Generated migration for adding sensitivity label fields to Document model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0001_initial'),  # Adjust to your latest migration
    ]

    operations = [
        # Add sensitivity label field
        migrations.AddField(
            model_name='document',
            name='sensitivity_label',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('PUBLIC', 'Public'),
                    ('INTERNAL', 'Internal Use Only'),
                    ('CONFIDENTIAL', 'Confidential'),
                    ('RESTRICTED', 'Restricted - Regulatory/Compliance'),
                    ('PROPRIETARY', 'Proprietary / Trade Secret'),
                ],
                default='INTERNAL',
                db_index=True,
                help_text='Sensitivity classification (set by approver)',
            ),
        ),
        
        # Add field to track who set the sensitivity label
        migrations.AddField(
            model_name='document',
            name='sensitivity_set_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sensitivity_labeled_documents',
                to=settings.AUTH_USER_MODEL,
                help_text='User who set the sensitivity label (typically approver)',
            ),
        ),
        
        # Add timestamp for when sensitivity was set
        migrations.AddField(
            model_name='document',
            name='sensitivity_set_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When sensitivity label was set',
            ),
        ),
        
        # Add field to track parent document for sensitivity inheritance
        migrations.AddField(
            model_name='document',
            name='sensitivity_inherited_from',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sensitivity_inherited_by',
                to='documents.document',
                help_text='Parent document this sensitivity was inherited from',
            ),
        ),
        
        # Add field to document reason for sensitivity changes
        migrations.AddField(
            model_name='document',
            name='sensitivity_change_reason',
            field=models.TextField(
                blank=True,
                help_text='Reason for sensitivity label change (required if changed from parent)',
            ),
        ),
        
        # Add index for sensitivity_label queries
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['sensitivity_label'], name='documents_sens_label_idx'),
        ),
        
        # Add composite index for sensitivity + status queries
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['sensitivity_label', 'status'], name='documents_sens_status_idx'),
        ),
    ]
