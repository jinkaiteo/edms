# Generated migration to add is_read field to WorkflowNotification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0008_remove_workflow_task_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflownotification',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
