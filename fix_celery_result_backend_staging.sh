#!/bin/bash

echo "=========================================="
echo "Fixing Celery Result Backend on Staging"
echo "=========================================="
echo ""

echo "Step 1: Verifying current configuration..."
docker compose exec -T backend python -c "
from celery import current_app
print('Current result_backend:', current_app.conf.result_backend)
"

echo ""
echo "Step 2: Stopping containers..."
docker compose stop backend celery_worker celery_beat

echo ""
echo "Step 3: Rebuilding containers with new settings..."
docker compose build backend celery_worker celery_beat

echo ""
echo "Step 4: Starting containers..."
docker compose up -d backend celery_worker celery_beat

echo ""
echo "Step 5: Waiting 30 seconds for containers to start..."
sleep 30

echo ""
echo "Step 6: Verifying new configuration..."
docker compose exec -T backend python -c "
from celery import current_app
from django.conf import settings
print('Django settings CELERY_RESULT_BACKEND:', settings.CELERY_RESULT_BACKEND)
print('Celery result_backend:', current_app.conf.result_backend)

if current_app.conf.result_backend == 'django-db':
    print('✅ SUCCESS! Celery is now using django-db backend')
else:
    print('❌ FAILED! Celery still using:', current_app.conf.result_backend)
    print('   May need to check .env file')
"

echo ""
echo "Step 7: Triggering a test task to verify results are saved..."
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.tasks import send_test_email_to_self
import time

print('Triggering test email task...')
result = send_test_email_to_self.delay()
print(f'Task ID: {result.id}')

print('Waiting 5 seconds for execution...')
time.sleep(5)

print(f'Task state: {result.state}')

# Check if result was saved to database
from django_celery_results.models import TaskResult
task_result = TaskResult.objects.filter(task_id=result.id).first()

if task_result:
    print('✅ SUCCESS! Task result saved to database')
    print(f'   Status: {task_result.status}')
    print(f'   Date: {task_result.date_done}')
else:
    print('❌ FAILED! Task result NOT saved to database')
    print('   Task executed but result not persisted')
"

echo ""
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo ""
echo "Next: Refresh frontend dashboard and click 'Run Now' on any task"
echo "      Status should update within 2-5 seconds"
echo ""
