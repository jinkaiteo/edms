# Scheduler Tasks Showing "Never Run" - Diagnostic & Fix Guide

## Problem Description

**Symptom:** Scheduler tasks execute successfully (emails are sent, actions complete), but the Administration Dashboard shows:
- Status: "Warning" 
- Last Run: "Never run"
- This happens for ALL tasks including the "Send Test Email" task

## Root Cause Analysis

There are **two different scheduling systems** in Celery, and they need to be properly synchronized:

### 1. **Settings-Based Schedule** (`CELERY_BEAT_SCHEDULE`)
- Location: `backend/edms/settings/base.py`
- Tasks defined in Python settings
- Celery Beat reads this and executes tasks
- ✅ Tasks EXECUTE from here

### 2. **Database-Based Schedule** (`django-celery-beat`)
- Location: PostgreSQL database (`django_celery_beat_periodictask` table)
- Tasks stored in `PeriodicTask` model
- Dashboard reads from here for status display
- ❌ Dashboard shows "Never run" if tasks NOT in database

## Why Both Systems?

```
CELERY_BEAT_SCHEDULE (settings)  →  Celery Beat  →  Task Execution ✓
                                          ↓
                                   (no database update)
                                          ↓
PeriodicTask (database)  →  Dashboard  →  Shows "Never run" ✗
```

**The Fix:** Sync settings tasks to database so dashboard can track them.

---

## Quick Diagnosis (30 seconds)

**On your staging server:**

```bash
# Check if tasks are in database
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print(f'PeriodicTask count: {PeriodicTask.objects.count()}')
"
```

**Expected Results:**
- ❌ **If output is `0`** → This is your problem! Tasks not in database.
- ✅ **If output is `7+`** → Tasks are in database, different issue.

---

## Solutions (Pick One)

### Solution 1: Automated Fix (Recommended)

**Pull and run the diagnostic script:**

```bash
cd ~/edms  # or wherever your repo is

# Pull latest scripts
git pull origin main

# Make scripts executable
chmod +x diagnose_scheduler_task_status.sh fix_scheduler_task_status.sh

# Run diagnostic (optional - see what's wrong)
./diagnose_scheduler_task_status.sh

# Run automated fix
./fix_scheduler_task_status.sh
```

**What the fix script does:**
1. Creates `setup_periodic_tasks` management command if missing
2. Syncs tasks from settings to database
3. Restarts Celery Beat
4. Verifies tasks are now tracked
5. Triggers test task to confirm

**Time:** 2-3 minutes

---

### Solution 2: Manual Fix (If scripts fail)

#### Step 1: Check Current State

```bash
docker compose exec backend python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.conf import settings

# Check tasks in settings
print("Tasks in settings:", len(settings.CELERY_BEAT_SCHEDULE))

# Check tasks in database  
print("Tasks in database:", PeriodicTask.objects.count())
```

#### Step 2: Create Management Command

```bash
docker compose exec backend sh -c "mkdir -p apps/scheduler/management/commands"
```

Create file: `backend/apps/scheduler/management/commands/setup_periodic_tasks.py`

```python
"""Management command to sync CELERY_BEAT_SCHEDULE to database"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.conf import settings
from datetime import timedelta


class Command(BaseCommand):
    help = "Setup periodic tasks from CELERY_BEAT_SCHEDULE in database"

    def handle(self, *args, **options):
        self.stdout.write("Setting up periodic tasks...")
        
        if not hasattr(settings, "CELERY_BEAT_SCHEDULE"):
            self.stdout.write(self.style.ERROR("No CELERY_BEAT_SCHEDULE found"))
            return
        
        created_count = 0
        
        for task_name, task_config in settings.CELERY_BEAT_SCHEDULE.items():
            task_path = task_config["task"]
            schedule_seconds = task_config["schedule"]
            
            if isinstance(schedule_seconds, timedelta):
                schedule_seconds = int(schedule_seconds.total_seconds())
            
            # Get or create interval schedule
            interval, _ = IntervalSchedule.objects.get_or_create(
                every=schedule_seconds,
                period=IntervalSchedule.SECONDS,
            )
            
            # Create PeriodicTask
            task_obj, created = PeriodicTask.objects.get_or_create(
                name=task_name,
                defaults={
                    "task": task_path,
                    "interval": interval,
                    "enabled": True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {task_name}"))
            else:
                self.stdout.write(f"  Exists: {task_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\nCompleted: {created_count} tasks created")
        )
```

#### Step 3: Run the Command

```bash
docker compose exec backend python manage.py setup_periodic_tasks
```

#### Step 4: Verify Tasks in Database

```bash
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
tasks = PeriodicTask.objects.all()
print(f'Total tasks: {tasks.count()}')
for task in tasks:
    print(f'  - {task.name}: {task.task}')
"
```

#### Step 5: Configure Celery Beat to Use Database Scheduler

Add to `backend/edms/settings/base.py`:

```python
# Celery Beat Scheduler - Use database for dynamic scheduling
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

#### Step 6: Restart Celery Beat

```bash
docker compose restart celery_beat
```

#### Step 7: Wait and Verify

Wait 5-10 minutes, then check:
```bash
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
for task in PeriodicTask.objects.all():
    print(f'{task.name}: Last run = {task.last_run_at or \"Never\"}, Total runs = {task.total_run_count}')
"
```

---

## Verification Steps

### 1. Check Database Has Tasks

```bash
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print('Tasks in database:', PeriodicTask.objects.count())
"
```

**Expected:** `7` or more tasks

### 2. Check Task Execution History

```bash
docker compose exec backend python manage.py shell -c "
from django_celery_results.models import TaskResult
print('Task executions:', TaskResult.objects.count())
recent = TaskResult.objects.order_by('-date_done')[:5]
for r in recent:
    print(f'  {r.task_name}: {r.status} at {r.date_done}')
"
```

### 3. Check Celery Beat Scheduler Setting

```bash
docker compose exec backend python manage.py shell -c "
from django.conf import settings
scheduler = getattr(settings, 'CELERY_BEAT_SCHEDULER', 'NOT SET')
print(f'CELERY_BEAT_SCHEDULER: {scheduler}')
if 'DatabaseScheduler' in scheduler:
    print('✓ Correct - using DatabaseScheduler')
else:
    print('✗ Wrong - should be django_celery_beat.schedulers:DatabaseScheduler')
"
```

### 4. Manual Task Trigger Test

```bash
docker compose exec backend python manage.py shell -c "
from apps.scheduler.tasks import send_test_email
result = send_test_email.delay()
print(f'Task triggered: {result.id}')
import time
time.sleep(3)
print(f'Status: {result.state}')
"
```

### 5. Check Dashboard (Final Test)

Visit: `http://your-server:8000/admin/scheduler/monitoring/`

**Expected after 5-10 minutes:**
- All tasks should show "Last Run" with timestamp (not "Never")
- Status should be "Success" or "Running" (not "Warning")
- Run count should be > 0

---

## Common Issues & Fixes

### Issue 1: Tasks Still Show "Never Run" After Fix

**Diagnosis:**
```bash
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print([t.last_run_at for t in PeriodicTask.objects.all()])
"
```

**If all show `None`:**
- Celery Beat not updating database after execution
- Check CELERY_BEAT_SCHEDULER setting

**Fix:**
```bash
# Add to settings if missing
echo "CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'" >> backend/edms/settings/base.py

# Restart
docker compose restart celery_beat
```

### Issue 2: `setup_periodic_tasks` Command Not Found

**Fix:** Create the management command using Solution 2, Step 2 above.

### Issue 3: Tasks Execute But Database Not Updated

**Possible causes:**
1. Using wrong scheduler (not DatabaseScheduler)
2. Celery Beat not connected to database
3. Transaction not committing

**Fix:**
```bash
# Check Celery Beat logs
docker compose logs celery_beat --tail=100 | grep -i database

# Verify database connection
docker compose exec backend python manage.py shell -c "
from django.db import connection
connection.ensure_connection()
print('Database connected:', connection.is_usable())
"
```

### Issue 4: PeriodicTask Table Doesn't Exist

**Fix:**
```bash
# Run migrations
docker compose exec backend python manage.py migrate django_celery_beat

# Verify table exists
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print('Table exists:', True)
"
```

---

## Understanding the Dashboard Logic

The scheduler dashboard reads from **three sources**:

### 1. PeriodicTask Model
- Shows if task is enabled
- Shows last run timestamp
- Shows total run count

### 2. TaskResult Model  
- Shows recent execution history
- Shows success/failure status
- Shows execution time

### 3. Celery Inspect API
- Shows if worker is alive
- Shows active tasks
- Shows worker configuration

**For "Never run" issue:** Focus on PeriodicTask model

---

## Monitoring After Fix

### Check Task Status Every 5 Minutes

```bash
watch -n 300 'docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
from datetime import datetime, timedelta
now = datetime.now()
for task in PeriodicTask.objects.all():
    last_run = task.last_run_at or \"Never\"
    if task.last_run_at:
        minutes_ago = int((now - task.last_run_at.replace(tzinfo=None)).total_seconds() / 60)
        last_run = f\"{minutes_ago}m ago\"
    print(f\"{task.name}: {last_run} (total: {task.total_run_count})\")
"'
```

### Watch Celery Beat Logs

```bash
docker compose logs -f celery_beat | grep -E "Scheduler:|Sending|DatabaseScheduler"
```

---

## Expected Behavior After Fix

**Immediately after fix:**
- `PeriodicTask.objects.count()` = 7+
- All tasks have `enabled=True`
- `last_run_at` = `None` (normal)

**After 5 minutes:**
- Tasks with short intervals (1-5 min) should show `last_run_at` timestamp
- Dashboard shows timestamps instead of "Never"

**After 10 minutes:**
- All tasks should have executed at least once
- Status should be "Success" (green)
- No more "Warning" status

---

## Prevention for Future Deployments

### Add to Deployment Script

Add this to `deploy-interactive.sh` or your deployment process:

```bash
# Sync periodic tasks after database initialization
print_step "Syncing scheduled tasks to database..."
docker compose exec backend python manage.py setup_periodic_tasks
```

### Add to README

Document that new deployments need:
1. Database migrations
2. Periodic task sync
3. Celery Beat restart

---

## Quick Reference Commands

```bash
# Diagnostic
./diagnose_scheduler_task_status.sh

# Automated Fix
./fix_scheduler_task_status.sh

# Manual Check
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print(f'Tasks: {PeriodicTask.objects.count()}')
for t in PeriodicTask.objects.all():
    print(f'{t.name}: {t.last_run_at or \"Never\"}')
"

# Sync Tasks
docker compose exec backend python manage.py setup_periodic_tasks

# Restart Beat
docker compose restart celery_beat

# Check Logs
docker compose logs celery_beat --tail=50
```

---

## Support

If issues persist after following this guide:

1. Run full diagnostic: `./diagnose_scheduler_task_status.sh > diagnostic_output.txt`
2. Check Celery Beat logs: `docker compose logs celery_beat > celery_beat_logs.txt`
3. Check database state: `docker compose exec backend python manage.py shell` (run queries from verification section)
4. Share output for further analysis

---

**Last Updated:** 2026-01-26  
**Related Files:**
- `diagnose_scheduler_task_status.sh` - Comprehensive diagnostic script
- `fix_scheduler_task_status.sh` - Automated fix script
- `backend/apps/scheduler/monitoring_dashboard.py` - Dashboard code
- `backend/edms/settings/base.py` - Celery configuration
