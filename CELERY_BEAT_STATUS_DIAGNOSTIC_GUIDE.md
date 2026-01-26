# Celery Beat Task Status Diagnostic Guide

## Issue

Tasks are executing (emails being sent) but the Administration Dashboard shows:
- Status: "Warning"
- Last run: "Never run"

## Diagnostic Steps

### Step 1: Verify Tasks Are Actually Running

```bash
# SSH to staging server
ssh user@staging-server
cd /path/to/edms/

# Check Celery Beat logs
docker compose -f docker-compose.prod.yml logs celery_beat --tail=100 | grep -i "send test email\|sending task"

# Check Celery Worker logs
docker compose -f docker-compose.prod.yml logs celery_worker --tail=100 | grep -i "send test email\|task received"

# Check if email task executed
docker compose -f docker-compose.prod.yml logs celery_worker --tail=200 | grep -i "email sent\|test email"
```

**Expected:** You should see task execution logs

---

### Step 2: Check Task Results in Database

```bash
# Check django_celery_results table
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_results.models import TaskResult

print("=== Recent Task Executions ===")
recent = TaskResult.objects.order_by('-date_done')[:10]
for task in recent:
    print(f"{task.task_name}: {task.status} at {task.date_done}")

print(f"\nTotal task results: {TaskResult.objects.count()}")
PYTHON
```

**Expected:** Should show task execution results

---

### Step 3: Check PeriodicTask Status

```bash
# Check if tasks are enabled and their last run times
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask
from django.utils import timezone

print("=== Periodic Task Status ===\n")
for task in PeriodicTask.objects.all():
    print(f"Task: {task.name}")
    print(f"  Enabled: {task.enabled}")
    print(f"  Last run: {task.last_run_at}")
    print(f"  Total runs: {task.total_run_count}")
    print()
PYTHON
```

**Expected:** 
- `last_run_at` should be None if never run by Beat
- `total_run_count` should be 0 if never run by Beat

---

### Step 4: Check if Beat Scheduler is Working

```bash
# Check Beat scheduler logs for scheduling activity
docker compose -f docker-compose.prod.yml logs celery_beat --tail=50

# Should see lines like:
# "Scheduler: Sending due task..."
# Or periodic scheduling messages
```

**Look for:**
- Beat service is running
- Beat is scheduling tasks
- No error messages

---

### Step 5: Verify Beat Schedule Configuration

```bash
# Check if beat_schedule is loaded
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from edms.celery import app

beat_schedule = app.conf.beat_schedule
print(f"Beat schedule has {len(beat_schedule)} tasks\n")

# Check if "Send Test Email" is in beat_schedule
if 'Send Test Email' in beat_schedule:
    print("✅ 'Send Test Email' is in beat_schedule")
    print(f"   Schedule: {beat_schedule['Send Test Email']}")
else:
    print("❌ 'Send Test Email' is NOT in beat_schedule")
    print("\nTasks in beat_schedule:")
    for name in beat_schedule.keys():
        print(f"  • {name}")
PYTHON
```

**Expected:** "Send Test Email" should be in beat_schedule

---

### Step 6: Check django-celery-beat Integration

```bash
# Check if Beat is using Django database scheduler
docker compose -f docker-compose.prod.yml exec celery_beat env | grep CELERY_BEAT_SCHEDULER

# Should show: celery.beat:PersistentScheduler or django_celery_beat.schedulers:DatabaseScheduler
```

**Check celery.py configuration:**

```bash
docker compose -f docker-compose.prod.yml exec backend grep -A5 "beat_scheduler" /app/edms/celery.py
```

**Expected:** Should use `django_celery_beat.schedulers:DatabaseScheduler`

---

### Step 7: Manual Task Trigger Test

```bash
# Trigger a task manually from shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from apps.scheduler.tasks import send_test_email_to_self

print("Triggering send_test_email_to_self manually...")
result = send_test_email_to_self.apply_async()
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")

# Wait a moment
import time
time.sleep(3)

# Check result
print(f"Final status: {result.status}")
PYTHON
```

**Expected:** Task executes and you receive email

---

### Step 8: Check Beat Service Status Update Permissions

```bash
# Check if Beat can write to PeriodicTask table
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask
from django.utils import timezone

# Try to update a task
task = PeriodicTask.objects.filter(name='Send Test Email').first()
if task:
    print(f"Current last_run_at: {task.last_run_at}")
    print(f"Current total_run_count: {task.total_run_count}")
    
    # Try to update it
    task.last_run_at = timezone.now()
    task.total_run_count = task.total_run_count + 1
    try:
        task.save()
        print("✅ Successfully updated task")
    except Exception as e:
        print(f"❌ Failed to update task: {e}")
else:
    print("Task not found")
PYTHON
```

**Expected:** Should be able to update task

---

### Step 9: Check Beat Scheduler Lock

```bash
# Check if there's a scheduler lock issue
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.db import connection

# Check database connection
print(f"Database: {connection.settings_dict['NAME']}")
print(f"Connected: {connection.ensure_connection() or 'Yes'}")

# Check if Beat can see the tasks
tasks = PeriodicTask.objects.all()
print(f"\nTasks visible from backend: {tasks.count()}")
PYTHON

# Check Beat container can see tasks
docker compose -f docker-compose.prod.yml exec celery_beat python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all()
print(f"Tasks visible from Beat: {tasks.count()}")
for task in tasks:
    print(f"  • {task.name}: enabled={task.enabled}")
PYTHON
```

**Expected:** Both should see same number of tasks

---

## Common Issues and Solutions

### Issue 1: Beat Not Using Database Scheduler

**Symptom:** Tasks execute but last_run_at never updates

**Check:** `edms/celery.py`
```python
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
```

**Fix if missing:** Add to celery.py configuration

---

### Issue 2: Beat Service Using Wrong Database

**Symptom:** Beat shows tasks but doesn't update them

**Check:** Beat container environment
```bash
docker compose -f docker-compose.prod.yml exec celery_beat env | grep DB_
```

**Fix:** Ensure Beat uses same database as backend

---

### Issue 3: Manual Triggers Don't Update Beat Scheduler

**Symptom:** Manually triggered tasks work but don't show in Beat stats

**Explanation:** This is **EXPECTED BEHAVIOR**
- Manual triggers bypass Beat scheduler
- Only Beat-scheduled tasks update `last_run_at` and `total_run_count`
- Manual triggers are recorded in `TaskResult` table only

**Verify:**
```bash
# Check TaskResult for manual triggers
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_results.models import TaskResult

manual_runs = TaskResult.objects.filter(
    task_name='apps.scheduler.tasks.send_test_email_to_self'
).order_by('-date_done')[:5]

print("Manual task executions:")
for result in manual_runs:
    print(f"  {result.date_done}: {result.status}")
PYTHON
```

---

### Issue 4: Tasks Created After Beat Started

**Symptom:** New tasks don't get picked up by Beat

**Cause:** Beat caches schedule on startup

**Fix:** Restart Beat service
```bash
docker compose -f docker-compose.prod.yml restart celery_beat
```

---

### Issue 5: Beat Scheduler Using Cron Schedule vs Database

**Symptom:** Some tasks run but aren't in database

**Check:** If tasks are defined in beat_schedule (edms/celery.py) but not created in database

**Solution:** Tasks must be in **database** (PeriodicTask table) for status tracking

**Create database entries:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask
from edms.celery import app

beat_schedule = app.conf.beat_schedule

for name, config in beat_schedule.items():
    task, created = PeriodicTask.objects.get_or_create(
        name=name,
        defaults={'task': config['task'], 'enabled': True}
    )
    if created:
        print(f"Created: {name}")
    else:
        print(f"Exists: {name}")
PYTHON
```

---

## Most Likely Causes

Based on your description, the most likely causes are:

### 1. Manual Trigger (Most Likely)
You triggered the task manually from the dashboard, which:
- ✅ Executes the task (you got email)
- ❌ Doesn't update Beat scheduler stats (shows "Never run")

**Solution:** Wait for Beat to actually schedule and run the task according to its schedule

**For "Send Test Email":**
- Schedule: Manual trigger only (impossible cron: Feb 31)
- Will NEVER be automatically scheduled
- Will ALWAYS show "Never run" by Beat
- Manual triggers are EXPECTED and don't update Beat stats

### 2. Beat Using Wrong Scheduler
Beat is using `PersistentScheduler` instead of `DatabaseScheduler`

**Check:** Look at celery_beat logs on startup
**Fix:** Update celery.py configuration

### 3. Tasks Not in Database
Tasks exist in beat_schedule but weren't created in PeriodicTask table

**Check:** Step 3 above
**Fix:** Run initialization script again

---

## Expected Behavior for "Send Test Email"

**Important:** "Send Test Email" has an **impossible schedule** (Feb 31st)

This means:
- ✅ It can be triggered manually from dashboard
- ❌ It will NEVER be automatically scheduled by Beat
- ❌ `last_run_at` will ALWAYS be "Never run" by Beat
- ❌ `total_run_count` will ALWAYS be 0 for Beat

**This is CORRECT behavior!**

The task is designed for **manual testing only**, not automatic scheduling.

---

## Verification Command Summary

```bash
# Quick diagnostic
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult
from django.utils import timezone

print("=== Celery Beat Status ===\n")

# Check task
task = PeriodicTask.objects.get(name='Send Test Email')
print(f"Task: {task.name}")
print(f"Enabled: {task.enabled}")
print(f"Last run by Beat: {task.last_run_at or 'Never'}")
print(f"Total runs by Beat: {task.total_run_count}")

# Check results
results = TaskResult.objects.filter(
    task_name='apps.scheduler.tasks.send_test_email_to_self'
).order_by('-date_done')[:5]

print(f"\nManual executions: {results.count()}")
for r in results:
    print(f"  {r.date_done}: {r.status}")
PYTHON
```

---

**Date:** January 26, 2026  
**Purpose:** Diagnose Celery Beat task status display issues  
**Expected Result:** Understand why tasks show "Never run"
