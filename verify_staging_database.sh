#!/bin/bash
echo "Verifying which database staging is using..."
echo ""

docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
from django.db import connection

print('=== DATABASE CONFIGURATION ===')
print(f'Database ENGINE: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'Database NAME: {settings.DATABASES[\"default\"][\"NAME\"]}')
print(f'Database HOST: {settings.DATABASES[\"default\"][\"HOST\"]}')
print(f'Database PORT: {settings.DATABASES[\"default\"][\"PORT\"]}')
print(f'Database USER: {settings.DATABASES[\"default\"][\"USER\"]}')

print('')
print('=== DATABASE CONNECTION ===')
with connection.cursor() as cursor:
    cursor.execute('SELECT current_database()')
    db_name = cursor.fetchone()[0]
    print(f'Connected to database: {db_name}')
    
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    print(f'PostgreSQL version: {version}')

print('')
print('=== CELERY RESULT BACKEND ===')
print(f'CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}')

print('')
print('=== CHECK IF django_celery_results APP IS INSTALLED ===')
print(f'Installed apps: {\"django_celery_results\" in settings.INSTALLED_APPS}')

print('')
print('=== CHECK TASKRESULT TABLE ===')
from django_celery_results.models import TaskResult
try:
    count = TaskResult.objects.count()
    print(f'TaskResult table exists: YES')
    print(f'TaskResult count: {count}')
    
    # Check if table is actually empty or query is wrong
    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM django_celery_results_taskresult')
        raw_count = cursor.fetchone()[0]
        print(f'Raw SQL count: {raw_count}')
        
        if raw_count > 0:
            cursor.execute('SELECT task_name, status, date_done FROM django_celery_results_taskresult ORDER BY date_done DESC LIMIT 5')
            results = cursor.fetchall()
            print(f'Recent results (raw SQL):')
            for r in results:
                print(f'  {r[0]}: {r[1]} at {r[2]}')
except Exception as e:
    print(f'Error accessing TaskResult: {e}')
"
