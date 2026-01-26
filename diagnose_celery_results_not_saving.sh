#!/bin/bash
echo "Diagnosing why Celery results are not being saved..."
echo ""

docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
from celery import current_app

print('=== DJANGO SETTINGS ===')
print(f'CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}')

print('')
print('=== CELERY APP CONFIGURATION ===')
print(f'Celery result_backend: {current_app.conf.result_backend}')
print(f'Celery result_persistent: {current_app.conf.result_persistent}')
print(f'Celery result_expires: {current_app.conf.result_expires}')
print(f'Celery task_track_started: {current_app.conf.task_track_started}')
print(f'Celery task_ignore_result: {current_app.conf.task_ignore_result}')

print('')
print('=== CHECK IF BACKEND SETTING IS LOADED IN CELERY ===')
# The issue might be that celery.py doesn't load the django-db backend properly
if current_app.conf.result_backend == 'django-db':
    print('✅ Celery is configured to use django-db backend')
else:
    print(f'❌ Celery result_backend is: {current_app.conf.result_backend}')
    print(f'   Expected: django-db')
    print(f'   This is why results are not being saved!')
"

echo ""
echo "=== CHECKING CELERY.PY CONFIGURATION ==="
grep -n "result_backend\|CELERY_RESULT" backend/edms/celery.py || echo "No result_backend configuration found in celery.py"

echo ""
echo "=== CHECKING SETTINGS/BASE.PY CONFIGURATION ==="
grep -n "CELERY_RESULT" backend/edms/settings/base.py || echo "No CELERY_RESULT configuration found in base.py"

echo ""
echo "=== CHECKING .env FILE ==="
grep "CELERY_RESULT" .env || echo "No CELERY_RESULT in .env file"
