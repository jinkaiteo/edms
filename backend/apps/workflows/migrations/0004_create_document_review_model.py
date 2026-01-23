# Generated migration for DocumentReview model

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0003_add_periodic_review_fields'),
        ('workflows', '0011_delete_workflowtask'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('review_date', models.DateField(auto_now_add=True, db_index=True, help_text='Date when review was completed')),
                ('outcome', models.CharField(
                    choices=[
                        ('CONFIRMED', 'Confirmed - No changes needed'),
                        ('UPDATED', 'Updated - Minor changes applied'),
                        ('UPVERSIONED', 'Up-versioned - Major changes required')
                    ],
                    help_text='Result of the periodic review',
                    max_length=20
                )),
                ('comments', models.TextField(blank=True, help_text='Reviewer comments and observations')),
                ('next_review_date', models.DateField(help_text='Scheduled date for next periodic review')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional review metadata (checklist results, etc.)')),
                ('document', models.ForeignKey(
                    help_text='Document that was reviewed',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='periodic_reviews',
                    to='documents.document'
                )),
                ('new_version', models.ForeignKey(
                    blank=True,
                    help_text='New document version created from this review (if outcome was UPVERSIONED)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_from_review',
                    to='documents.document'
                )),
                ('reviewed_by', models.ForeignKey(
                    help_text='User who completed the review',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='completed_reviews',
                    to=settings.AUTH_USER_MODEL
                )),
                ('workflow', models.ForeignKey(
                    blank=True,
                    help_text='Associated workflow if periodic review triggered a workflow',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='periodic_review',
                    to='workflows.documentworkflow'
                )),
            ],
            options={
                'verbose_name': 'Document Review',
                'verbose_name_plural': 'Document Reviews',
                'db_table': 'document_reviews',
                'ordering': ['-review_date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='documentreview',
            index=models.Index(fields=['document', 'review_date'], name='document_re_documen_idx'),
        ),
        migrations.AddIndex(
            model_name='documentreview',
            index=models.Index(fields=['reviewed_by', 'review_date'], name='document_re_reviewe_idx'),
        ),
        migrations.AddIndex(
            model_name='documentreview',
            index=models.Index(fields=['outcome'], name='document_re_outcome_idx'),
        ),
        migrations.AddIndex(
            model_name='documentreview',
            index=models.Index(fields=['next_review_date'], name='document_re_next_re_idx'),
        ),
    ]
