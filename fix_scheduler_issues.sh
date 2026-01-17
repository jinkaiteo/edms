#!/bin/bash
# Fix Scheduler Issues - Initialize Beat Schedule and Check Queue Config

echo "=============================================="
echo "  Fixing Scheduler Issues"
echo "  $(date)"
echo "=============================================="
echo ""

echo "🔧 1. INITIALIZING CELERY BEAT SCHEDULE"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.utils import timezone

print('Creating scheduled tasks from celery.py beat_schedule...')
print('')

# Import the Celery app to get beat_schedule
from edms.celery import app

beat_schedule = app.conf.beat_schedule

created_count = 0
for name, config in beat_schedule.items():
    task_path = config['task']
    schedule_config = config['schedule']
    
    # Create or get crontab schedule
    if hasattr(schedule_config, 'minute'):
        # It's a crontab
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=str(schedule_config.minute),
            hour=str(schedule_config.hour),
            day_of_week=str(schedule_config.day_of_week),
            day_of_month=str(schedule_config.day_of_month),
            month_of_year=str(schedule_config.month_of_year),
        )
        
        # Create or update periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name=name,
            defaults={
                'task': task_path,
                'crontab': crontab,
                'enabled': True
            }
        )
        
        if created:
            print(f'✅ Created: {name}')
            print(f'   Task: {task_path}')
            print(f'   Schedule: {crontab}')
            created_count += 1
        else:
            print(f'ℹ️  Exists: {name}')

print('')
print(f'Summary: {created_count} new tasks created')
print(f'Total scheduled tasks: {PeriodicTask.objects.count()}')
"
echo ""

echo "🔍 2. CHECKING CELERY CONFIGURATION"
echo "----------------------------------------------"
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from celery import current_app

print('Celery Configuration:')
print(f'  Broker URL: {current_app.conf.broker_url}')
print(f'  Result backend: {current_app.conf.result_backend}')
print(f'  Task default queue: {current_app.conf.task_default_queue}')
print(f'  Task routes: {current_app.conf.task_routes}')
print('')

# Check task routing
print('Task Routing:')
task_routes = current_app.conf.task_routes or {}
for pattern, config in task_routes.items():
    print(f'  {pattern} → {config}')
"
echo ""

echo "🎯 3. TESTING TASK EXECUTION"
echo "----------------------------------------------"
echo "Triggering test task directly..."

docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.scheduler.tasks import perform_system_health_check
from celery import current_app

print('Triggering task with apply_async...')
result = perform_system_health_check.apply_async()
print(f'Task ID: {result.id}')
print(f'Task state: {result.state}')
print('')

import time
print('Waiting 3 seconds...')
time.sleep(3)

print(f'Task state after 3s: {result.state}')

if result.ready():
    print(f'Task completed!')
    print(f'Result: {result.get()}')
else:
    print(f'Task still pending/running')
    print('')
    print('Checking if task is in queue...')
    
    # Check queue
    inspect = current_app.control.inspect()
    
    reserved = inspect.reserved()
    if reserved:
        print('Reserved tasks:')
        for worker, tasks in reserved.items():
            print(f'  {worker}: {len(tasks)} tasks')
            for task in tasks:
                if task['id'] == result.id:
                    print(f'    ✅ Found our task: {task[\"name\"]}')
    
    active = inspect.active()
    if active:
        print('Active tasks:')
        for worker, tasks in active.items():
            print(f'  {worker}: {len(tasks)} tasks')
"
echo ""

echo "🚦 4. CHECKING CELERY WORKER QUEUES"
echo "----------------------------------------------"
echo "Celery worker should be listening to these queues:"
docker logs edms_prod_celery_worker 2>&1 | grep -i "celery.*ready" | tail -5
echo ""

echo "Checking worker configuration..."
docker compose -f docker-compose.prod.yml exec celery_worker bash -c "ps aux | grep celery" 2>/dev/null || echo "Could not check worker process"
echo ""

echo "=============================================="
echo "  Fix Complete - Diagnosis"
echo "=============================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Check if PeriodicTask records were created above"
echo "2. Check if test task executed successfully"
echo "3. If task still doesn't execute, check worker is consuming from correct queue"
echo ""
echo "If tasks still don't execute, the issue is likely:"
echo "  - Worker not listening to 'scheduler' queue"
echo "  - Redis connection issue"
echo "  - Task routing configuration mismatch"
echo ""
