#!/bin/bash

################################################################################
# Compare Local vs Staging Configuration
################################################################################
# Run this script on BOTH local and staging to collect diagnostic data
# Then compare the outputs to find differences
################################################################################

OUTPUT_FILE="edms_diagnostic_$(hostname)_$(date +%Y%m%d_%H%M%S).txt"

echo "Collecting diagnostic data... Output: $OUTPUT_FILE"
echo ""

{
echo "=========================================="
echo "EDMS Diagnostic Report"
echo "=========================================="
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "User: $(whoami)"
echo ""

echo "=========================================="
echo "1. DOCKER CONTAINERS"
echo "=========================================="
docker compose ps
echo ""

echo "=========================================="
echo "2. ENVIRONMENT VARIABLES (.env)"
echo "=========================================="
echo "--- CELERY Configuration ---"
grep -E "CELERY_" .env | grep -v "PASSWORD"
echo ""
echo "--- Database Configuration ---"
grep -E "DB_|POSTGRES_" .env | grep -v "PASSWORD"
echo ""
echo "--- Redis Configuration ---"
grep -E "REDIS_" .env | grep -v "PASSWORD"
echo ""

echo "=========================================="
echo "3. DJANGO SETTINGS"
echo "=========================================="
docker compose exec -T backend python -c "
from django.conf import settings
import json

config = {
    'DEBUG': settings.DEBUG,
    'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', 'NOT SET'),
    'CELERY_BROKER_URL': settings.CELERY_BROKER_URL,
    'CELERY_RESULT_BACKEND': settings.CELERY_RESULT_BACKEND,
    'CELERY_BEAT_SCHEDULER': getattr(settings, 'CELERY_BEAT_SCHEDULER', 'NOT SET'),
    'INSTALLED_APPS_COUNT': len(settings.INSTALLED_APPS),
    'HAS_DJANGO_CELERY_BEAT': 'django_celery_beat' in settings.INSTALLED_APPS,
    'HAS_DJANGO_CELERY_RESULTS': 'django_celery_results' in settings.INSTALLED_APPS,
}

for key, value in config.items():
    print(f'{key}: {value}')
"
echo ""

echo "=========================================="
echo "4. CELERY APP CONFIGURATION"
echo "=========================================="
docker compose exec -T backend python -c "
from celery import current_app

print(f'Celery app name: {current_app.main}')
print(f'Broker URL: {current_app.conf.broker_url}')
print(f'Result backend: {current_app.conf.result_backend}')
print(f'Task track started: {current_app.conf.task_track_started}')
print(f'Task ignore result: {current_app.conf.task_ignore_result}')
print(f'Result expires: {current_app.conf.result_expires}')
print(f'Result persistent: {current_app.conf.result_persistent}')
print(f'Beat scheduler: {current_app.conf.beat_scheduler}')
"
echo ""

echo "=========================================="
echo "5. BEAT SCHEDULE TASKS"
echo "=========================================="
docker compose exec -T backend python -c "
from celery import current_app

beat_schedule = current_app.conf.beat_schedule or {}
print(f'Total tasks in beat_schedule: {len(beat_schedule)}')
print('')
for name, config in beat_schedule.items():
    print(f'{name}:')
    print(f'  Task: {config[\"task\"]}')
    print(f'  Schedule: {config[\"schedule\"]}')
"
echo ""

echo "=========================================="
echo "6. DATABASE - PERIODIC TASKS"
echo "=========================================="
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all().order_by('name')
print(f'Total PeriodicTask records: {tasks.count()}')
print('')
for task in tasks:
    print(f'{task.name}:')
    print(f'  Task: {task.task}')
    print(f'  Enabled: {task.enabled}')
    print(f'  Last run: {task.last_run_at or \"Never\"}')
    print(f'  Total runs: {task.total_run_count}')
"
echo ""

echo "=========================================="
echo "7. DATABASE - TASK RESULTS"
echo "=========================================="
docker compose exec -T backend python manage.py shell -c "
from django_celery_results.models import TaskResult

total = TaskResult.objects.count()
print(f'Total TaskResult records: {total}')

if total > 0:
    recent = TaskResult.objects.order_by('-date_done')[:10]
    print('')
    print('Recent 10 executions:')
    for r in recent:
        print(f'  {r.task_name}')
        print(f'    Status: {r.status}')
        print(f'    Date: {r.date_done}')
else:
    print('')
    print('❌ No TaskResult records - Tasks not saving results!')
"
echo ""

echo "=========================================="
echo "8. STATUS API OUTPUT"
echo "=========================================="
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.task_monitor import get_task_status

try:
    status = get_task_status()
    print(f'Total tasks in status API: {len(status[\"tasks\"])}')
    print('')
    
    for task in status['tasks'][:5]:
        print(f'{task[\"name\"]}:')
        print(f'  Schedule name: {task[\"schedule_name\"]}')
        print(f'  Task path: {task[\"task_path\"]}')
        print(f'  Last run: {task[\"last_run\"][\"relative_time\"]}')
        print(f'  Status: {task[\"status\"]}')
        print('')
except Exception as e:
    print(f'❌ Error getting status: {e}')
"
echo ""

echo "=========================================="
echo "9. CELERY BEAT LOGS (Last 30 lines)"
echo "=========================================="
docker compose logs celery_beat --tail=30 | grep -i "scheduler\|beat\|database"
echo ""

echo "=========================================="
echo "10. CELERY WORKER LOGS (Last 20 lines)"
echo "=========================================="
docker compose logs celery_worker --tail=20 | grep -E "ready|received|success|failed"
echo ""

echo "=========================================="
echo "11. SETTINGS FILE GREP"
echo "=========================================="
echo "--- CELERY_RESULT_BACKEND in settings ---"
grep -n "CELERY_RESULT_BACKEND" backend/edms/settings/base.py
echo ""
echo "--- CELERY_BEAT_SCHEDULER in settings ---"
grep -n "CELERY_BEAT_SCHEDULER" backend/edms/settings/base.py
echo ""

echo "=========================================="
echo "12. GIT COMMIT INFO"
echo "=========================================="
git log --oneline -5
echo ""
git status | head -20
echo ""

echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="

} > "$OUTPUT_FILE" 2>&1

echo "✓ Diagnostic saved to: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  1. Run this same script on the OTHER environment (local/staging)"
echo "  2. Compare the two output files"
echo "  3. Look for differences in:"
echo "     - CELERY_RESULT_BACKEND (should be 'django-db' in both)"
echo "     - TaskResult count (should be > 0 in both)"
echo "     - Beat schedule tasks (should match)"
echo "     - Status API output (should match)"
echo ""
