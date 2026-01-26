# Post-Deployment Setup Checklist

## After Fresh Deployment, Run These Commands

### 1. Remove celery.backend_cleanup Task
```bash
docker compose exec -T backend python manage.py remove_backend_cleanup
```

**Why:** `django-celery-results` automatically creates this task, but we have our own `cleanup-celery-results` task.

**Expected output:**
```
✓ Removed celery.backend_cleanup task
Total periodic tasks: 10
```

---

### 2. Create "Send Test Email" Task (Manual Trigger Only)
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# Create a crontab that never runs (Feb 31)
crontab, _ = CrontabSchedule.objects.get_or_create(
    minute='0',
    hour='0',
    day_of_month='31',
    month_of_year='2',
    day_of_week='*',
)

# Create task
task, created = PeriodicTask.objects.get_or_create(
    name='Send Test Email',
    defaults={
        'task': 'apps.scheduler.tasks.send_test_email_to_self',
        'crontab': crontab,
        'enabled': True,
    }
)

print(f'✓ Send Test Email task: {\"created\" if created else \"exists\"}')
"
```

**Why:** This task should only be triggered manually from the dashboard, not on a schedule.

---

### 3. Verify Configuration
```bash
# Check Celery is using django-db backend
docker compose exec -T backend python -c "
from celery import current_app
from django.conf import settings
print('Django CELERY_RESULT_BACKEND:', settings.CELERY_RESULT_BACKEND)
print('Celery result_backend:', current_app.conf.result_backend)
print('Beat scheduler:', current_app.conf.beat_scheduler)
"
```

**Expected output:**
```
Django CELERY_RESULT_BACKEND: django-db
Celery result_backend: django-db
Beat scheduler: django_celery_beat.schedulers:DatabaseScheduler
```

---

### 4. Test Task Execution
```bash
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.tasks import perform_system_health_check
import time

result = perform_system_health_check.delay()
print(f'Task ID: {result.id}')
time.sleep(5)

from django_celery_results.models import TaskResult
task_result = TaskResult.objects.filter(task_id=result.id).first()
if task_result:
    print(f'✓ Task result saved: {task_result.status}')
else:
    print('✗ Task result NOT saved')
"
```

**Expected output:**
```
Task ID: <uuid>
✓ Task result saved: SUCCESS
```

---

### 5. Verify Dashboard Shows Correct Tasks
```bash
docker compose exec -T backend python -c "
from django_celery_beat.models import PeriodicTask
print(f'Total tasks: {PeriodicTask.objects.count()}')
print('\nTasks:')
for t in PeriodicTask.objects.all().order_by('name'):
    print(f'  - {t.name}')
"
```

**Expected output (11 tasks):**
```
Total tasks: 11

Tasks:
  - check-workflow-timeouts
  - cleanup-celery-results
  - perform-system-health-check
  - process-document-effective-dates
  - process-document-obsoletion-dates
  - process-periodic-reviews
  - run-daily-integrity-check
  - send-daily-health-report
  - Send Test Email
  - verify-audit-trail-checksums
```

**Note:** Should NOT include `celery.backend_cleanup`

---

## Summary

After running these steps:
- ✅ Celery uses `django-db` result backend
- ✅ Task results save to PostgreSQL
- ✅ Dashboard shows execution status
- ✅ 11 tasks total (no celery.backend_cleanup)
- ✅ Send Test Email available for manual trigger
- ✅ All scheduled tasks run on their schedules

---

## Quick One-Liner for All Steps

```bash
docker compose exec -T backend python manage.py remove_backend_cleanup && \
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule
crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='0', day_of_month='31', month_of_year='2', day_of_week='*')
task, created = PeriodicTask.objects.get_or_create(name='Send Test Email', defaults={'task': 'apps.scheduler.tasks.send_test_email_to_self', 'crontab': crontab, 'enabled': True})
print(f'✓ Complete. Total tasks: {PeriodicTask.objects.count()}')
"
```
