from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('scheduler', '0002_initial'),
    ]
    
    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS scheduler_notificationqueue CASCADE;",
            reverse_sql="SELECT 1;"  # Irreversible
        ),
    ]
