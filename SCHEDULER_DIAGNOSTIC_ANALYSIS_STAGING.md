# Scheduler Task Status Diagnostic Analysis - Staging Server

## 📊 Diagnostic Results Summary

**Date:** 2026-01-26  
**Server:** staging-server-ubuntu-20  
**Issue:** Tasks show "Never run" despite being configured and containers running

---

## 🔍 Key Findings from Diagnostic

### ✅ What's Working

1. **All Containers Running**
   - Backend: Up 42 minutes (healthy)
   - Celery Beat: Up 43 minutes
   - Celery Worker: Up 43 minutes (healthy)
   - All 4 worker processes active

2. **Tasks ARE in Database**
   - ✅ 10 PeriodicTask entries exist
   - ✅ All tasks enabled
   - ✅ All have crontab schedules configured

3. **Celery Beat IS Using DatabaseScheduler**
   - Found in `backend/apps/scheduler/celery_schedule.py` line 83:
     ```python
     CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
     ```

### ❌ What's NOT Working

1. **CELERY_BEAT_SCHEDULE Shows as False**
   ```
   Schedule configured: False
   ERROR: CELERY_BEAT_SCHEDULE not configured!
   ```
   **Why:** The schedule is defined in `celery.py` as `app.conf.beat_schedule`, not `settings.CELERY_BEAT_SCHEDULE`

2. **Celery Beat Using WRONG Scheduler**
   ```
   . scheduler -> celery.beat.PersistentScheduler  ❌
   . db -> /tmp/celerybeat-schedule
   ```
   **Should be:** `django_celery_beat.schedulers:DatabaseScheduler`

3. **No Task Execution History**
   ```
   Total task results in database: 0
   ⚠ No task execution history found!
   ```

4. **All Tasks Show "Never run"**
   ```
   Last Run: Never
   Total Runs: 0
   ```

---

## 🎯 Root Cause Analysis

### Problem #1: Scheduler Configuration Mismatch

**Expected Flow:**
```
Settings CELERY_BEAT_SCHEDULER → DatabaseScheduler → Updates PeriodicTask table
```

**Actual Flow:**
```
celery.py defines CELERY_BEAT_SCHEDULER → But Celery Beat ignores it
Celery Beat uses default PersistentScheduler → No database updates
```

**Why This Happens:**

The `CELERY_BEAT_SCHEDULER` setting is defined in TWO places:
1. ✅ `backend/apps/scheduler/celery_schedule.py` line 83
2. ❌ NOT in `backend/edms/settings/base.py`

**Celery Beat loads from:**
- Django settings (via `CELERY_` namespace)
- NOT from `app.conf` in celery.py

**The Fix:** Add `CELERY_BEAT_SCHEDULER` to `settings/base.py`

---

### Problem #2: Schedule Definition Location

**Current Setup:**
```python
# backend/edms/celery.py line 27
app.conf.beat_schedule = {
    'process-document-effective-dates': {...},
    'process-document-obsoletion-dates': {...},
    # ... 9 total tasks
}
```

**Issue:** This defines schedule in code, but:
- Tasks already exist in database (10 PeriodicTask entries)
- Database tasks were created manually or via django-celery-beat admin
- Celery Beat reads from database (when using DatabaseScheduler)
- Code schedule is ignored when DatabaseScheduler is active

**Result:** Dual configuration - tasks in both code AND database

---

### Problem #3: Task Name Mismatch

**Database has:**
- `Send Test Email` → task: `apps.scheduler.tasks.send_test_email_to_self`

**Diagnostic script tried:**
- `send_test_email` (doesn't exist)

**Actual task name in code:**
- `send_test_email_to_self` (line 187 of tasks.py)

---

## 🔧 Solution Strategy

### Option 1: Use DatabaseScheduler (Recommended for Production)

**Advantages:**
- Dynamic scheduling via Django admin
- Can enable/disable tasks without code changes
- Change schedules without redeployment
- Perfect for production where schedules may need adjustment

**Implementation:**

1. **Add to `settings/base.py`:**
   ```python
   # Celery Beat Scheduler - Use database for dynamic scheduling
   CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
   ```

2. **Keep database tasks (already exists)**
   - 10 tasks already configured
   - All have crontab schedules
   - All enabled

3. **Restart Celery Beat:**
   ```bash
   docker compose restart celery_beat
   ```

4. **Wait and verify:**
   - Tasks will execute on their schedules
   - `last_run_at` will update after execution
   - Dashboard will show timestamps

**Why this works:**
- Celery Beat will use DatabaseScheduler
- Read schedules from PeriodicTask table
- Update `last_run_at` and `total_run_count` after execution
- Dashboard will see the updates

---

### Option 2: Use PersistentScheduler (Code-Based)

**Advantages:**
- Simpler configuration
- Schedule defined in code (version controlled)
- No database dependency for scheduling

**Disadvantages:**
- Tasks won't show execution status in dashboard
- Can't change schedules without redeployment
- Dashboard shows "Never run" (expected behavior)

**Implementation:**

1. **Remove from `settings/base.py`:**
   - Don't add `CELERY_BEAT_SCHEDULER` (uses default PersistentScheduler)

2. **Delete database tasks (optional):**
   ```bash
   docker compose exec -T backend python manage.py shell -c "
   from django_celery_beat.models import PeriodicTask
   PeriodicTask.objects.all().delete()
   print('Database tasks cleared')
   "
   ```

3. **Restart Celery Beat:**
   ```bash
   docker compose restart celery_beat
   ```

**Why this works:**
- Celery Beat uses code-based schedule
- Tasks execute but don't update database
- Dashboard shows "Never run" (no database tracking)

---

## ✅ Recommended Solution: Option 1 (DatabaseScheduler)

This is the best choice for your setup because:

1. **You already have database tasks configured** - 10 tasks with proper schedules
2. **Dashboard monitoring is important** - You want to see task status
3. **Production flexibility** - Can adjust schedules without redeployment
4. **21 CFR Part 11 compliance** - Need audit trail of task execution

---

## 🚀 Implementation Steps

### Step 1: Add DatabaseScheduler Setting

```bash
# On staging server
cd ~/edms

# Add the setting
docker compose exec -T backend python manage.py shell -c "
import os
settings_file = '/app/edms/settings/base.py'
with open(settings_file, 'r') as f:
    content = f.read()

# Check if already exists
if 'CELERY_BEAT_SCHEDULER' not in content:
    # Add after CELERY_BEAT_SCHEDULE_FILENAME line
    new_content = content.replace(
        \"CELERY_BEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule'\",
        \"CELERY_BEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule'\\n\"
        \"CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'  # Use database for task tracking\"
    )
    with open(settings_file, 'w') as f:
        f.write(new_content)
    print('✓ Added CELERY_BEAT_SCHEDULER setting')
else:
    print('Setting already exists')
"
```

### Step 2: Restart Celery Beat

```bash
docker compose restart celery_beat
```

### Step 3: Verify Configuration

```bash
# Check Celery Beat logs for DatabaseScheduler
docker compose logs celery_beat --tail=20 | grep -i "scheduler"

# Should show:
# beat: Using DatabaseScheduler
```

### Step 4: Wait for Tasks to Execute

```bash
# Check task status every 2 minutes
watch -n 120 'docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
from datetime import datetime
now = datetime.now()
print(\"\\nTask Status:\")
for task in PeriodicTask.objects.all()[:5]:
    if task.last_run_at:
        mins = int((now - task.last_run_at.replace(tzinfo=None)).total_seconds() / 60)
        print(f\"{task.name}: {mins}m ago (runs: {task.total_run_count})\")
    else:
        print(f\"{task.name}: Never\")
"'
```

### Step 5: Verify Dashboard

After 30-60 minutes (depending on task schedules), visit:
```
http://staging-server:8001/admin/scheduler/monitoring/
```

**Expected Results:**
- ✅ Status: Success (green)
- ✅ Last Run: Timestamps (not "Never")
- ✅ Total Runs: > 0

---

## 📋 Task Schedule Reference

Based on database configuration:

| Task Name | Schedule | Next Run (from 7:43 AM UTC) |
|-----------|----------|------------------------------|
| process-document-effective-dates | Every hour at :00 | 8:00 AM |
| process-document-obsoletion-dates | Every hour at :15 | 8:15 AM |
| perform-system-health-check | Every 30 minutes | 8:00 AM, 8:30 AM |
| check-workflow-timeouts | Every 4 hours (0,4,8,12,16,20) | 8:00 AM |
| process-periodic-reviews | Daily at 9:00 AM | 9:00 AM |
| send-daily-health-report | Daily at 7:00 AM | Tomorrow 7:00 AM |
| cleanup-celery-results | Daily at 3:00 AM | Tomorrow 3:00 AM |
| run-daily-integrity-check | Daily at 2:00 AM | Tomorrow 2:00 AM |
| verify-audit-trail-checksums | Weekly Sunday at 1:00 AM | Next Sunday |
| Send Test Email | Feb 31 (never) | Never (manual only) |

**Fastest to verify:** `perform-system-health-check` (every 30 minutes)

---

## 🔍 Verification Commands

### Check Scheduler Type
```bash
docker compose logs celery_beat --tail=50 | grep -i "scheduler"
```

### Check Task Execution
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_results.models import TaskResult
recent = TaskResult.objects.order_by('-date_done')[:10]
print(f'Total task results: {TaskResult.objects.count()}')
for r in recent:
    print(f'{r.task_name}: {r.status} at {r.date_done}')
"
```

### Check PeriodicTask Updates
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
for task in PeriodicTask.objects.all():
    print(f'{task.name}:')
    print(f'  Last Run: {task.last_run_at or \"Never\"}')
    print(f'  Total Runs: {task.total_run_count}')
    print()
"
```

---

## 🎯 Expected Timeline

**Immediate (0 minutes):**
- Setting added to base.py
- Celery Beat restarted

**After 30 minutes:**
- `perform-system-health-check` should have run 1 time
- `last_run_at` should show timestamp
- `total_run_count` should be 1

**After 1 hour:**
- `process-document-effective-dates` should have run
- `process-document-obsoletion-dates` should have run
- Multiple tasks showing timestamps

**After 2 hours:**
- All frequently-scheduled tasks should have run
- Dashboard should show "Success" status
- No more "Never run" messages

---

## 🚨 Troubleshooting

### If Tasks Still Show "Never" After 1 Hour

**Check 1: Verify Scheduler**
```bash
docker compose logs celery_beat | grep "scheduler"
```
Should show: `beat: Using DatabaseScheduler`
If shows `PersistentScheduler` → Setting not loaded, rebuild container

**Check 2: Verify Setting Loaded**
```bash
docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
scheduler = getattr(settings, 'CELERY_BEAT_SCHEDULER', 'NOT SET')
print(f'CELERY_BEAT_SCHEDULER: {scheduler}')
"
```
Should show: `django_celery_beat.schedulers:DatabaseScheduler`

**Check 3: Rebuild Container**
```bash
# If setting not loaded, rebuild to pick up new code
docker compose stop celery_beat
docker compose build celery_beat
docker compose up -d celery_beat
```

### If Tasks Execute But Don't Update Database

**Check:** Results backend configuration
```bash
docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
print(f'CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}')
"
```
Should show: `django-db` or database URL

---

## 📝 Summary

**Root Cause:**
- Celery Beat using `PersistentScheduler` instead of `DatabaseScheduler`
- Missing `CELERY_BEAT_SCHEDULER` setting in `settings/base.py`
- Database tasks exist but not being updated after execution

**Solution:**
- Add `CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'` to settings
- Restart Celery Beat
- Wait 30-60 minutes for tasks to execute
- Verify dashboard shows timestamps

**Expected Result:**
- Tasks execute on schedule
- `last_run_at` updates after each execution
- `total_run_count` increments
- Dashboard shows "Success" with timestamps
- No more "Never run" messages

---

**Next Steps:** Follow Implementation Steps above to apply the fix.
