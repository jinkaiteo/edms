# Generated manually for session_id null constraint fix

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0007_fix_document_versioning_consistency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentaccesslog',
            name='session_id',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]
