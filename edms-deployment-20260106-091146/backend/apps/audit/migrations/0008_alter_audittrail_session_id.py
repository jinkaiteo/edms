# Generated manually for session_id null constraint fix

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0007_databasechangelog_integrity_hash'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audittrail',
            name='session_id',
            field=models.CharField(blank=True, db_index=True, max_length=40, null=True),
        ),
    ]
