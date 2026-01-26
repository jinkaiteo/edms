# Celery Cleanup Task Decision

## Problem
The `celery.backend_cleanup` task was auto-created by `django-celery-results` package and kept recreating itself even after deletion/disable attempts.

## Root Cause
When `CELERY_RESULT_BACKEND = "django-db"` is set, the `django-celery-results` package automatically registers a cleanup task that runs daily at 04:00 to delete expired task results based on `CELERY_RESULT_EXPIRES` setting.

## Solution: Disable Built-in, Keep Our Custom Task

### Decision: Set `CELERY_RESULT_EXPIRES = None`

**Commit:** Latest (fix: Disable built-in celery.backend_cleanup)

**Changes:**
```python
# Old
CELERY_RESULT_EXPIRES = 86400  # 24 hours

# New  
CELERY_RESULT_EXPIRES = None  # Disable built-in cleanup
```

---

## Comparison: Our Task vs Built-in

| Feature | Our `cleanup-celery-results` | Built-in `celery.backend_cleanup` |
|---------|------------------------------|-----------------------------------|
| **Retention** | 7 days | 24 hours (was hardcoded) |
| **REVOKED cleanup** | ✅ Explicitly removes | ❌ Only time-based |
| **Statistics** | ✅ Detailed (before/after counts) | ❌ Minimal |
| **Logging** | ✅ Comprehensive | ❌ Basic |
| **Schedule** | Daily 03:00 | Daily 04:00 |
| **Configurable** | ✅ Yes (days_to_keep param) | ⚠️ Via global setting only |
| **Auto-creates** | ❌ No | ✅ Yes (problematic) |

---

## Our Custom Task Details

**File:** `backend/apps/scheduler/services/cleanup.py`

**Function:** `cleanup_celery_results(days_to_keep=7, remove_revoked=True)`

**What it does:**
1. Deletes TaskResult records older than 7 days
2. Deletes ALL REVOKED status tasks (failed/cancelled noise)
3. Returns detailed statistics
4. Logs comprehensive cleanup info

**Example Output:**
```
Celery results cleanup completed: Deleted 245 records (1,043 → 798)
  - Deleted old: 198 records older than 7 days
  - Deleted revoked: 47 REVOKED tasks
```

---

## Why Our Task is Better

### 1. **Longer Retention (7 days vs 24 hours)**
- Better for debugging issues that happened days ago
- Can track task patterns over a week
- Aligns with common log retention practices

### 2. **REVOKED Task Cleanup**
- Removes failed/cancelled tasks that clutter logs
- These are usually not useful for analysis
- Keeps database cleaner

### 3. **Better Observability**
- Detailed before/after statistics
- Breakdown by deletion type (old vs revoked)
- Comprehensive logging for monitoring

### 4. **Flexibility**
- Can adjust retention via parameter
- Can disable REVOKED cleanup if needed
- Easy to modify behavior without package updates

---

## Effect of CELERY_RESULT_EXPIRES = None

**What happens:**
- ✅ `celery.backend_cleanup` task will NOT be auto-created
- ✅ Task results are stored indefinitely by Celery (until our task cleans them)
- ✅ Our cleanup task handles all cleanup logic
- ✅ No more task recreation issues
- ✅ Cleaner task list (10 tasks, not 11)

**What doesn't change:**
- ✅ Task results still saved to database
- ✅ Dashboard still shows execution history
- ✅ Manual triggers still work
- ✅ All other Celery functionality unchanged

---

## Testing After Deployment

### 1. Verify built-in task NOT created
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print(f'Total tasks: {PeriodicTask.objects.count()}')
print(f'backend_cleanup exists: {PeriodicTask.objects.filter(name=\"celery.backend_cleanup\").exists()}')
"
```
**Expected:** Total: 10, exists: False

### 2. Verify our task exists and works
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
cleanup = PeriodicTask.objects.filter(name='cleanup-celery-results').first()
print(f'Our task: {cleanup.name}')
print(f'Schedule: {cleanup.crontab}')
print(f'Enabled: {cleanup.enabled}')
"
```
**Expected:** Shows our task enabled at 03:00

### 3. Manually test cleanup
```bash
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.tasks import cleanup_celery_results
result = cleanup_celery_results()
print('Result:', result)
"
```
**Expected:** Statistics showing cleanup results

---

## Migration Path for Existing Deployments

### Fresh Deployment
✅ Automatic - new deployments use `CELERY_RESULT_EXPIRES = None`

### Existing Deployment
```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild backend
docker compose stop backend
docker compose build backend
docker compose up -d backend

# 3. Remove existing celery.backend_cleanup task
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
deleted = PeriodicTask.objects.filter(name='celery.backend_cleanup').delete()
print(f'Deleted: {deleted[0]} tasks')
"

# 4. Restart celery_beat
docker compose restart celery_beat

# 5. Verify
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print(f'Total tasks: {PeriodicTask.objects.count()}')
print(f'celery.backend_cleanup: {PeriodicTask.objects.filter(name=\"celery.backend_cleanup\").exists()}')
"
```

**Expected:** 10 tasks, no celery.backend_cleanup

---

## Future Considerations

### If We Ever Want Built-in Cleanup Back
```python
# Change to desired retention period
CELERY_RESULT_EXPIRES = 7 * 24 * 3600  # 7 days

# Then remove our custom task
```

### If We Want Both
```python
# Keep shorter retention for built-in
CELERY_RESULT_EXPIRES = 86400  # 24 hours

# Our task runs first (03:00) with 7-day retention + REVOKED cleanup
# Built-in runs second (04:00) as backup/failsafe
```

---

## Related Files

- **Settings:** `backend/edms/settings/base.py` (line 361)
- **Our Task:** `backend/apps/scheduler/tasks.py` (`cleanup_celery_results`)
- **Service:** `backend/apps/scheduler/services/cleanup.py`
- **Schedule:** `backend/edms/celery.py` (beat_schedule)
- **Deployment:** `deploy-interactive.sh` (no longer needs disable step)

---

## Summary

**Decision:** Keep our superior custom cleanup task, disable built-in auto-creation

**Implementation:** `CELERY_RESULT_EXPIRES = None`

**Result:** 
- ✅ 10 tasks (clean list)
- ✅ 7-day retention
- ✅ REVOKED cleanup
- ✅ Better logging
- ✅ No more auto-creation issues

**Status:** ✅ Complete and deployed
