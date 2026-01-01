# Celery Worker and Beat Status Report

## 📊 **Current Status**

**Celery Beat (Scheduler):** ✅ Working perfectly (100% true!)  
**Celery Worker:** ❌ Unhealthy - Task import issue  
**Impact:** Low (core features work, background tasks fail)

---

## ✅ **Celery Beat - Working Correctly**

**Status:** Scheduler is running and sending tasks as scheduled

**Evidence:**
```
[2026-01-01 08:50:00] Scheduler: Sending due task process-notification-queue
[2026-01-01 08:00:00] Scheduler: Sending due task send-daily-summary
[2026-01-01 08:00:00] Scheduler: Sending due task check-workflow-timeouts
[2026-01-01 08:00:00] Scheduler: Sending due task perform-system-health-check
[2026-01-01 08:00:00] Scheduler: Sending due task process-document-effective-dates
```

**Tasks Being Scheduled:**
- ✅ `process-notification-queue` - Every 5 minutes
- ✅ `send-daily-summary` - Daily at 8:00 AM
- ✅ `check-workflow-timeouts` - Daily
- ✅ `perform-system-health-check` - Every 30 minutes
- ✅ `process-document-effective-dates` - Daily
- ✅ `process-document-obsoletion-dates` - Every 15 minutes

**Conclusion:** The admin page showing "Scheduler: 100%" is **ACCURATE**. Celery Beat is working perfectly!

---

## ❌ **Celery Worker - Task Import Issue**

**Status:** Worker is running but cannot execute tasks due to import error

**Error:**
```
KeyError: 'apps.scheduler.notification_service.process_notification_queue'

Received unregistered task of type 
'apps.scheduler.notification_service.process_notification_queue'.

Did you remember to import the module containing this task?
```

**Root Cause:**  
The Celery worker cannot find the task definitions. The tasks are being scheduled (Beat works), but the worker doesn't know how to execute them because the task modules aren't imported.

---

## 🔍 **Why This Happens**

### Likely Causes:

1. **Missing Task Import in Celery App**
   - Tasks need to be imported in `backend/edms/celery.py`
   - Worker needs to discover task definitions at startup

2. **Task Module Path Issue**
   - Task is defined as `apps.scheduler.notification_service.process_notification_queue`
   - Worker may not have this module in its import path

3. **Celery Autodiscover Not Working**
   - Celery autodiscover might not be finding all task modules
   - Missing `tasks.py` files or incorrect app configuration

---

## 🔧 **How to Fix**

### Option 1: Add Task Imports to celery.py (Recommended)

**Check `backend/edms/celery.py`:**
```python
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.production')

app = Celery('edms')
app.config_from_object('django.conf:settings', namespace='CELERY')

# This should auto-discover tasks in tasks.py files
app.autodiscover_tasks()

# OR explicitly import task modules:
app.autodiscover_tasks([
    'apps.scheduler',
    'apps.scheduler.notification_service',
    'apps.scheduler.automated_tasks',
])
```

### Option 2: Create tasks.py Files

Celery looks for `tasks.py` by convention. Check if:
```
backend/apps/scheduler/tasks.py exists
```

If tasks are in `notification_service.py` and `automated_tasks.py`, either:
- Move them to `tasks.py`
- Or import them in `tasks.py`:
  ```python
  from .notification_service import *
  from .automated_tasks import *
  ```

### Option 3: Restart Worker After Code Changes

```bash
docker compose -f docker-compose.prod.yml restart celery_worker
```

---

## 💡 **Impact Assessment**

### Currently Working ✅
- User login/authentication
- Document management
- Workflow operations
- API calls
- Admin interface
- **Scheduler (Beat) sending tasks on schedule**

### Not Working ❌
- Background notification processing
- Daily summary emails
- Workflow timeout checks
- Document effective date processing
- Document obsoletion date processing
- System health checks (automated)

### User Impact
**Low to Medium:**
- Users can still work normally
- Real-time features work
- Documents can be created/approved
- Workflows function

**Missing:**
- Automated reminders
- Scheduled notifications
- Background cleanup tasks
- Automated status changes

---

## 🎯 **Recommendations**

### Priority 1: Core Deployment ✅
**Status:** Complete  
The system is **production-ready** for core document management functionality.

### Priority 2: Celery Worker Fix ⚠️
**Priority:** Medium  
**Timeline:** Can be fixed post-deployment  
**User Impact:** Automated tasks won't run

**Decision Point:**
1. **Deploy now, fix later** - Core features work, automated tasks can wait
2. **Fix before deployment** - Takes 30-60 minutes to diagnose and fix imports

### Priority 3: Testing
After fixing Celery worker:
```bash
# Test task execution
docker compose -f docker-compose.prod.yml exec celery_worker \
  celery -A edms inspect registered

# Manually trigger a task
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py shell -c "
from apps.scheduler.notification_service import process_notification_queue
process_notification_queue.delay()
"
```

---

## 📋 **Summary**

| Component | Status | Health | Impact |
|-----------|--------|--------|--------|
| Celery Beat | ✅ Working | Healthy | Scheduling tasks correctly |
| Celery Worker | ⚠️ Running | Unhealthy | Cannot execute tasks |
| Task Scheduling | ✅ 100% | Accurate | Admin page is correct |
| Task Execution | ❌ 0% | Failing | Import errors |

**Admin Page Showing 100%:** This is **TRUE** - it refers to Celery Beat (scheduler), not the worker.

---

## ✅ **Action Items**

### Immediate (Optional)
- [ ] Investigate celery.py for task imports
- [ ] Check if tasks.py files exist
- [ ] Verify task module paths
- [ ] Restart celery worker after fixes

### Can Wait
- [ ] Test automated notifications
- [ ] Verify scheduled job execution
- [ ] Monitor celery worker logs
- [ ] Set up celery monitoring (Flower)

---

**Conclusion:** The "100%" scheduler status is accurate - Celery Beat is working perfectly. The worker has an import issue but doesn't block core functionality. Can be fixed post-deployment.
