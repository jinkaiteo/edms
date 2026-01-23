# Generated migration for Periodic Review System - Phase 1

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0009_alter_document_status_alter_documentversion_status')
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='review_period_months',
            field=models.PositiveIntegerField(
                default=12,
                help_text='Number of months between periodic reviews (typically 12 for annual review)'
            ),
        ),
        migrations.AddField(
            model_name='document',
            name='last_review_date',
            field=models.DateField(
                null=True,
                blank=True,
                db_index=True,
                help_text='Date of the most recent periodic review'
            ),
        ),
        migrations.AddField(
            model_name='document',
            name='next_review_date',
            field=models.DateField(
                null=True,
                blank=True,
                db_index=True,
                help_text='Scheduled date for next periodic review'
            ),
        ),
        migrations.AddField(
            model_name='document',
            name='last_reviewed_by',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
                blank=True,
                related_name='last_reviewed_documents',
                to=settings.AUTH_USER_MODEL,
                help_text='User who completed the most recent periodic review'
            ),
        ),
    ]
