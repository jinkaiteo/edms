# Complete Analysis: Staging Scheduler "Never Run" Issue

## 🎯 **Root Cause Identified**

Based on comprehensive diagnostic analysis, I've identified the complete picture:

---

## 📊 **Key Findings from Staging**

### ✅ What's Working Perfectly:

```
=== DATABASE STATUS ===
PeriodicTask count: 10
TaskResult count: 30  ← TASKS ARE EXECUTING!

Recent task executions:
  apps.scheduler.tasks.perform_system_health_check: SUCCESS at 2026-01-26 08:00:02
  apps.scheduler.tasks.process_document_effective_dates: SUCCESS at 2026-01-26 08:00:00
  apps.scheduler.tasks.check_workflow_timeouts: SUCCESS at 2026-01-26 08:00:00
  apps.scheduler.tasks.perform_system_health_check: SUCCESS at 2026-01-26 07:30:02
  apps.scheduler.tasks.process_document_obsoletion_dates: SUCCESS at 2026-01-26 07:15:00

Tasks with last_run_at set: 0  ← This is the problem, but NOT what dashboard uses!
```

### 🔍 Critical Discovery:

**The dashboard does NOT use `PeriodicTask.last_run_at` at all!**

Looking at `monitoring_dashboard.py` line 366-407, the `_get_task_statistics()` method:
- ✅ Uses `TaskResult` for task execution history
- ✅ Uses `AuditTrail` for processing events
- ✅ Uses `Document` and `DocumentWorkflow` models for stats
- ❌ **NEVER reads `PeriodicTask.last_run_at`**

---

## 🤔 **Why Does Dashboard Show "Never Run"?**

The dashboard gets its data from:

### 1. **Recent Executions** (Line 436-459)
```python
def _get_recent_executions(self, limit=10):
    recent_executions = AuditTrail.objects.filter(
        action__in=[
            'MANUAL_TASK_EXECUTION_COMPLETED',  ← Manual triggers only!
            'DOCUMENT_EFFECTIVE_DATE_PROCESSED',  
            'DOCUMENT_OBSOLETED',
            'WORKFLOW_HEALTH_WARNING',
            'SYSTEM_HEALTH_CHECK'
        ]
    ).order_by('-timestamp')[:limit]
```

**Issue:** `MANUAL_TASK_EXECUTION_COMPLETED` is for manually triggered tasks only.
Scheduled tasks don't create this audit entry!

### 2. **Task Statistics** (Line 366-407)
```python
def _get_task_statistics(self):
    stats = {
        'documents_processed_today': AuditTrail.objects.filter(
            action__in=[
                'DOCUMENT_EFFECTIVE_DATE_PROCESSED',  ← From actual document processing
                'DOCUMENT_OBSOLETED'
            ],
            timestamp__date=today
        ).count()
    }
```

**This shows:** Document processing audit entries, not task execution status

---

## 🎭 **The Real Problem: Dashboard Design vs User Expectation**

### **What Users See:**
- Task list in dashboard
- "Last Run: Never" for all tasks
- Status: Warning ⚠️

### **What's Actually Happening:**
- Tasks **ARE executing** (30 TaskResult records prove this)
- Tasks **ARE processing documents** (audit trail shows success)
- Dashboard shows "Never" because it's looking for the wrong data

### **Why the Mismatch:**

The dashboard has **two different views**:

**View 1: Available Tasks** (Line 50-131)
- Lists all scheduleable tasks
- Shows task metadata (name, description, icon)
- **Does NOT show execution status**

**View 2: Recent Executions** (Line 436-459)
- Shows recent audit trail entries
- Only shows **manually triggered** tasks or document processing events
- **Does NOT show scheduled task executions**

---

## 🔧 **Root Cause Summary**

| Component | Status | Details |
|-----------|--------|---------|
| **Celery Beat** | ✅ Running | Using PersistentScheduler |
| **Celery Worker** | ✅ Running | 4 workers active |
| **Tasks Executing** | ✅ Yes | 30 TaskResult records |
| **Documents Processing** | ✅ Yes | Audit trail confirms |
| **PeriodicTask.last_run_at** | ❌ NULL | Because using PersistentScheduler |
| **Dashboard Data Source** | ⚠️ Wrong | Looks for manual triggers, not scheduled |
| **CELERY_BEAT_SCHEDULER** | ❌ NOT SET | Missing from settings |

---

## ✅ **The Complete Solution**

There are **TWO separate issues** to fix:

### Issue #1: PeriodicTask Not Updating ← Your Original Question
**Fix:** Add `CELERY_BEAT_SCHEDULER` to settings

### Issue #2: Dashboard Doesn't Show Scheduled Task Status ← The Real UX Problem  
**Fix:** Dashboard needs to query `TaskResult` or `PeriodicTask` for task execution status

---

## 🚀 **Solution 1: Fix PeriodicTask Tracking**

This makes `PeriodicTask.last_run_at` update after execution.

```bash
# On staging server
cd ~/edms
git pull origin main
./apply_scheduler_fix_now.sh
```

**What it does:**
- Adds `CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'`
- Restarts Celery Beat
- After 30min, `PeriodicTask.last_run_at` will show timestamps

**Result:**
- ✅ `PeriodicTask.last_run_at` updates
- ❌ Dashboard still shows "Never" (doesn't use this field!)

---

## 🎨 **Solution 2: Fix Dashboard to Show Actual Status**

The dashboard needs code changes to display scheduled task execution status.

### **Option A: Use TaskResult** (Recommended - Already Working!)

Modify dashboard to show TaskResult data:

```python
# In monitoring_dashboard.py, add new method:
def _get_scheduled_task_executions(self):
    """Get execution history for scheduled tasks from TaskResult."""
    from django_celery_results.models import TaskResult
    
    task_executions = {}
    for task_name, task_info in self.available_tasks.items():
        # Get celery task path
        celery_path = task_info['celery_task'].__module__ + '.' + task_info['celery_task'].__name__
        
        # Get most recent execution
        recent = TaskResult.objects.filter(
            task_name=celery_path
        ).order_by('-date_done').first()
        
        if recent:
            task_executions[task_name] = {
                'last_run': recent.date_done,
                'status': recent.status,
                'total_runs': TaskResult.objects.filter(task_name=celery_path).count()
            }
        else:
            task_executions[task_name] = {
                'last_run': None,
                'status': 'NEVER_RUN',
                'total_runs': 0
            }
    
    return task_executions
```

**Why This Works:**
- ✅ TaskResult already has 30 records
- ✅ Shows actual execution history
- ✅ Works with ANY scheduler (Persistent or Database)
- ✅ No need for CELERY_BEAT_SCHEDULER change

### **Option B: Use PeriodicTask** (After Fix #1)

```python
def _get_scheduled_task_status(self):
    """Get execution status from PeriodicTask."""
    from django_celery_beat.models import PeriodicTask
    
    task_status = {}
    for pt in PeriodicTask.objects.all():
        task_status[pt.name] = {
            'last_run': pt.last_run_at,
            'total_runs': pt.total_run_count,
            'enabled': pt.enabled
        }
    
    return task_status
```

**Requires:**
- ❌ CELERY_BEAT_SCHEDULER = DatabaseScheduler (not currently set)
- ❌ 30 minutes wait for first execution
- ⚠️ More complex setup

---

## 📋 **Recommended Action Plan**

### **Immediate Fix (5 minutes):**

1. **Add `CELERY_BEAT_SCHEDULER` setting:**
   ```bash
   cd ~/edms
   git pull origin main
   ./apply_scheduler_fix_now.sh
   ```

2. **Verify it worked after 30 minutes:**
   ```bash
   docker compose exec -T backend python manage.py shell -c "
   from django_celery_beat.models import PeriodicTask
   for t in PeriodicTask.objects.all()[:3]:
       print(f'{t.name}: {t.last_run_at}')
   "
   ```
   Should show timestamps, not "None"

### **Frontend Not Updating Issue:**

**Separate problem!** The frontend showing "Never run" is because:

**Root Cause:** Dashboard template (HTML) probably shows static task list without execution status.

**Check:** Does the frontend actually call an API to get execution status, or does it just display task names?

**To verify:**
```bash
# Check frontend files
grep -r "Never run\|last_run\|execution" frontend/src/components/Admin/ | head -20
```

**Likely issue:** Frontend has hardcoded task list without dynamic status updates.

---

## 🎯 **Summary: What to Do**

### **For "Never Run" in PeriodicTask:**
✅ **Run:** `./apply_scheduler_fix_now.sh`
✅ **Wait:** 30 minutes
✅ **Verify:** `PeriodicTask.last_run_at` shows timestamps

### **For Frontend Not Updating:**
1. **First:** Apply the fix above
2. **Then:** Check if frontend actually polls for status updates
3. **If not:** Frontend needs code changes to show TaskResult data

### **For Dashboard Showing Wrong Data:**
- Dashboard backend (`monitoring_dashboard.py`) needs modification
- Add `_get_scheduled_task_executions()` method
- Use `TaskResult` for execution history
- Update API response to include this data

---

## 🔍 **Diagnostic Commands**

### **Check Task Execution (Works Now!):**
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_results.models import TaskResult
recent = TaskResult.objects.order_by('-date_done')[:5]
for r in recent:
    print(f'{r.task_name}: {r.status} at {r.date_done}')
"
```

### **Check PeriodicTask Status (After Fix):**
```bash
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
for t in PeriodicTask.objects.all()[:5]:
    print(f'{t.name}: last_run={t.last_run_at}, runs={t.total_run_count}')
"
```

### **Check Celery Beat Scheduler Type:**
```bash
docker compose logs celery_beat --tail=20 | grep scheduler
```

Should show after fix:
```
beat: Using DatabaseScheduler
```

---

## 📝 **Conclusion**

**Your System is Working!** Tasks execute successfully (30 TaskResult records prove it).

**The Problem:** Dashboard UI doesn't show this success because:
1. `PeriodicTask.last_run_at` is NULL (missing CELERY_BEAT_SCHEDULER setting)
2. Dashboard doesn't query TaskResult for execution history
3. Frontend may not poll for updated status

**The Fix:**
1. ✅ Add CELERY_BEAT_SCHEDULER setting (5 min)
2. ⏳ Wait 30 minutes for updates
3. 🔄 May need dashboard/frontend code changes to display the data

**Quick Win:** Focus on Solution 1 first (add CELERY_BEAT_SCHEDULER). This solves the "Never Run" issue even if dashboard UI needs separate work.

---

**Want me to help with frontend refresh issue separately?**
