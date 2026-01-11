# Generated migration to add read_at field to WorkflowNotification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0009_add_is_read_to_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflownotification',
            name='read_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
