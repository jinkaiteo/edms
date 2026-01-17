#!/bin/bash
# Task Execution Diagnostic Script
# Checks why "Last Run" shows "Never run" after manual trigger

echo "=============================================="
echo "  Task Execution Diagnostic"
echo "  $(date)"
echo "=============================================="
echo ""

echo "📋 1. PERIODIC TASK RECORDS (Celery Beat Schedule)"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all().order_by('name')
print(f'Total scheduled tasks: {tasks.count()}')
print('')

for task in tasks:
    status = '✅' if task.enabled else '❌'
    print(f'{status} {task.name}')
    print(f'   Task: {task.task}')
    print(f'   Enabled: {task.enabled}')
    print(f'   Last run: {task.last_run_at or \"Never\"}')
    print(f'   Total runs: {task.total_run_count}')
    if task.last_run_at:
        from django.utils import timezone
        ago = timezone.now() - task.last_run_at
        hours = ago.total_seconds() / 3600
        print(f'   (ran {hours:.1f} hours ago)')
    print('')
"
echo ""

echo "📊 2. TASK EXECUTION HISTORY (Last 10 minutes)"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta

recent = timezone.now() - timedelta(minutes=10)
results = TaskResult.objects.filter(date_done__gte=recent).order_by('-date_done')

print(f'Tasks executed in last 10 minutes: {results.count()}')
print('')

if results.exists():
    for result in results:
        status_symbol = '✅' if result.status == 'SUCCESS' else '❌' if result.status == 'FAILURE' else '⏳'
        print(f'{status_symbol} {result.task_name}')
        print(f'   Task ID: {result.task_id}')
        print(f'   Status: {result.status}')
        print(f'   Date done: {result.date_done}')
        if result.result:
            import json
            try:
                res = json.loads(result.result)
                if isinstance(res, dict):
                    if 'processed_count' in res:
                        print(f'   Processed: {res.get(\"processed_count\", 0)} items')
                    if 'success_count' in res:
                        print(f'   Success: {res.get(\"success_count\", 0)}')
            except:
                pass
        print('')
else:
    print('❌ No tasks executed in last 10 minutes')
    print('')
    print('Checking last hour...')
    hour_ago = timezone.now() - timedelta(hours=1)
    results_hour = TaskResult.objects.filter(date_done__gte=hour_ago).order_by('-date_done')
    print(f'Tasks executed in last hour: {results_hour.count()}')
    for result in results_hour[:5]:
        print(f'  {result.task_name} - {result.status} at {result.date_done}')
"
echo ""

echo "🔧 3. CELERY WORKER STATUS"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from celery import current_app

inspect = current_app.control.inspect()

# Check active tasks
active = inspect.active()
if active:
    print('Currently running tasks:')
    for worker, tasks in active.items():
        print(f'  Worker {worker}: {len(tasks)} active tasks')
        for task in tasks:
            print(f'    - {task[\"name\"]} (ID: {task[\"id\"]})')
else:
    print('No tasks currently running')

print('')

# Check registered tasks
registered = inspect.registered()
if registered:
    print('Registered tasks:')
    for worker, tasks in registered.items():
        scheduler_tasks = [t for t in tasks if 'scheduler' in t]
        print(f'  Worker {worker}: {len(scheduler_tasks)} scheduler tasks')
        for task in scheduler_tasks[:10]:
            print(f'    - {task}')
"
echo ""

echo "🎯 4. MANUAL TRIGGER TEST"
echo "----------------------------------------------"
echo "Manually triggering 'perform_system_health_check'..."

TRIGGER_TIME=$(date -u +"%Y-%m-%d %H:%M:%S")
echo "Trigger time: $TRIGGER_TIME UTC"
echo ""

# Trigger the task
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}' 2>&1)

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Wait for task to execute
echo "Waiting 5 seconds for task to execute..."
sleep 5

# Check if it appears in TaskResult
echo ""
echo "Checking if task appears in TaskResult..."
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta

recent = timezone.now() - timedelta(seconds=30)
results = TaskResult.objects.filter(
    task_name='apps.scheduler.tasks.perform_system_health_check',
    date_done__gte=recent
).order_by('-date_done')

if results.exists():
    print('✅ Task found in TaskResult:')
    for result in results[:3]:
        print(f'  Task ID: {result.task_id}')
        print(f'  Status: {result.status}')
        print(f'  Done: {result.date_done}')
else:
    print('❌ Task NOT found in TaskResult (last 30 seconds)')
    print('')
    print('Checking all recent tasks...')
    all_recent = TaskResult.objects.filter(date_done__gte=recent).order_by('-date_done')
    print(f'Total tasks in last 30 seconds: {all_recent.count()}')
    for r in all_recent:
        print(f'  {r.task_name} - {r.status}')
"
echo ""

echo "🔍 5. CHECK IF PERIODIC TASK WAS UPDATED"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask

# Find tasks related to health check
health_tasks = PeriodicTask.objects.filter(task__icontains='health')

if health_tasks.exists():
    print('Health check periodic tasks:')
    for task in health_tasks:
        print(f'  {task.name}')
        print(f'    Last run: {task.last_run_at or \"Never\"}')
        print(f'    Total runs: {task.total_run_count}')
else:
    print('No health check tasks found in PeriodicTask')

print('')
print('All periodic tasks:')
for task in PeriodicTask.objects.all():
    print(f'  {task.name}: Last run = {task.last_run_at or \"Never\"}, Runs = {task.total_run_count}')
"
echo ""

echo "=============================================="
echo "  Diagnostic Complete"
echo "=============================================="
echo ""
echo "📝 Key Findings:"
echo ""
echo "If PeriodicTask.last_run_at is 'Never' but TaskResult shows executions:"
echo "  → Manual trigger bypasses PeriodicTask tracking"
echo "  → This is expected with fire-and-forget pattern"
echo "  → Frontend 'Last Run' field is reading from PeriodicTask"
echo "  → Need to update frontend to read from TaskResult instead"
echo ""
echo "If TaskResult shows no executions:"
echo "  → Task is being queued but not executing"
echo "  → Check Celery worker logs for errors"
echo ""
