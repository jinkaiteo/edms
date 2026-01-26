#!/bin/bash
echo "Checking what staging status API returns..."
echo ""

# This should be run ON staging server
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.task_monitor import get_task_status
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult

print('=== PERIODIC TASKS IN DATABASE ===')
pt_tasks = PeriodicTask.objects.filter(enabled=True)
print(f'Total enabled PeriodicTask: {pt_tasks.count()}')
for pt in pt_tasks:
    print(f'  - {pt.name}: {pt.task}')

print('')
print('=== TASK RESULTS (Recent 5) ===')
results = TaskResult.objects.order_by('-date_done')[:5]
print(f'Total TaskResult: {TaskResult.objects.count()}')
for r in results:
    print(f'  - {r.task_name}: {r.status} at {r.date_done}')

print('')
print('=== STATUS API OUTPUT ===')
status = get_task_status()
print(f'Total tasks in API: {len(status[\"tasks\"])}')

# Check if Send Test Email is in the list
test_email_tasks = [t for t in status['tasks'] if 'email' in t['name'].lower()]
print(f'Tasks with \"email\": {len(test_email_tasks)}')

if test_email_tasks:
    for t in test_email_tasks:
        print(f'  Task: {t[\"name\"]}')
        print(f'    Schedule name: {t[\"schedule_name\"]}')
        print(f'    Task path: {t[\"task_path\"]}')
        print(f'    Last run: {t[\"last_run\"][\"relative_time\"]}')
        print(f'    Last run timestamp: {t[\"last_run\"][\"timestamp\"]}')
        print(f'    Status: {t[\"status\"]}')
else:
    print('  ❌ No tasks with \"email\" found in status API!')
    print('')
    print('=== DEBUGGING: Check beat_schedule ===')
    from celery import current_app
    beat_schedule = current_app.conf.beat_schedule or {}
    print(f'Tasks in beat_schedule: {len(beat_schedule)}')
    for name in beat_schedule.keys():
        print(f'  - {name}')
"
