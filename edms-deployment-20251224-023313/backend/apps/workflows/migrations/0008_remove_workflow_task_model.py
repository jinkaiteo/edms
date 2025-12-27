# Generated migration for removing WorkflowTask model
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('workflows', '0005_alter_documentstate_code'),
    ]

    operations = [
        # WorkflowTask model removal - table never existed in this migration chain
        # Document filtering approach is now implemented
        migrations.RunSQL(
            "SELECT 1;",  # No-op operation since WorkflowTask table was never created
            reverse_sql="SELECT 1;"
        ),
    ]