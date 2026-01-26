# Frontend Not Updating After Manual Trigger - Root Cause Analysis

## 🎯 **Issue Summary**

**Problem:** When you manually trigger "Send Test Email" from frontend:
- ✅ Email sends successfully
- ✅ Task executes (proven by email delivery)
- ❌ Frontend dashboard doesn't update to show execution
- ❌ Status still shows "Never run" or old status

---

## 🔍 **Complete Data Flow Analysis**

### **Step 1: Frontend Triggers Task**
**File:** `frontend/src/components/scheduler/TaskListWidget.tsx` (Line 83-118)

```typescript
const handleManualTrigger = async (taskName: string) => {
    // Convert hyphenated schedule name to underscore format
    const backendTaskName = taskName.replace(/-/g, '_');
    
    // POST to backend
    const result = await apiService.post('/scheduler/monitoring/manual-trigger/', {
        task_name: backendTaskName
    });
    
    if (result.success) {
        alert('✅ Task queued successfully!');
        
        // CRITICAL LINE 108: Refresh after 2 seconds
        setTimeout(() => fetchTaskStatus(), 2000);
    }
}
```

**Frontend expects:** Status will update after 2 seconds

---

### **Step 2: Backend Queues Task**
**File:** `backend/apps/scheduler/monitoring_dashboard.py` (Line 179-278)

```python
def manually_execute_task(self, task_name, user=None, dry_run=False):
    # Execute task asynchronously
    async_result = celery_task.apply_async()
    
    # Return immediately (fire-and-forget)
    return {
        'success': True,
        'task_id': async_result.id,
        'status': 'queued',  # ← Returns 'queued', not 'SUCCESS'
        'message': 'Task queued successfully'
    }
```

**Backend returns:** Task is queued but NOT yet executed

---

### **Step 3: Frontend Refreshes Status (2 seconds later)**
**File:** `frontend/src/components/scheduler/TaskListWidget.tsx` (Line 55-66)

```typescript
const fetchTaskStatus = async () => {
    // GET from backend
    const response = await apiService.get('/scheduler/monitoring/status/');
    setData(response);
}
```

**Frontend calls:** `/scheduler/monitoring/status/`

---

### **Step 4: Backend Returns Task Status**
**File:** `backend/apps/scheduler/task_monitor.py` (Line 82-172)

This is **THE CRITICAL ISSUE!**

```python
def get_task_status(self):
    # Get scheduled tasks from Celery Beat
    beat_schedule = current_app.conf.beat_schedule or {}  # ← Line 86
    
    # Build task list from beat_schedule
    tasks = []
    for schedule_name, schedule_config in beat_schedule.items():
        task_info = self._get_task_info(schedule_name, ...)
        tasks.append(task_info)
```

**Where does it get tasks from?**
- ✅ `current_app.conf.beat_schedule` (from `celery.py` line 28)
- ✅ Database `PeriodicTask` records (line 109-127)

**What's in `beat_schedule`?**
From `backend/edms/celery.py` line 28:
```python
app.conf.beat_schedule = {
    'process-document-effective-dates': {...},
    'process-document-obsoletion-dates': {...},
    'check-workflow-timeouts': {...},
    'perform-system-health-check': {...},
    'process-periodic-reviews': {...},
    'send-daily-health-report': {...},
    'cleanup-celery-results': {...},
    'run-daily-integrity-check': {...},
    'verify-audit-trail-checksums': {...},
}
```

**❌ MISSING:** `send_test_email_to_self` is NOT in `beat_schedule`!

---

### **Step 5: Backend Gets Last Run from TaskResult**
**File:** `backend/apps/scheduler/task_monitor.py` (Line 209-253)

```python
def _get_last_run(self, task_name):
    # Get most recent execution from TaskResult
    last_result = TaskResult.objects.filter(
        task_name=task_name
    ).exclude(
        status='REVOKED'
    ).order_by('-date_done').first()
    
    if not last_result:
        return {
            'relative_time': 'Never run',  # ← Shows "Never run"
            'status': 'PENDING'
        }
```

**This SHOULD work!** Your staging has 30 TaskResult records including test email executions.

---

## 🔴 **Root Cause Identified**

### **The Problem: "Send Test Email" Not in beat_schedule**

**Where the task IS defined:**
- ✅ Database: `PeriodicTask` record exists (from your diagnostic)
- ✅ TaskResult: 30 execution records exist
- ✅ Frontend: Displays the task in UI

**Where the task is MISSING:**
- ❌ `backend/edms/celery.py` - NOT in `app.conf.beat_schedule`
- ❌ Status API only reads from `beat_schedule` + database PeriodicTask

**Result:**
1. Frontend triggers "Send Test Email"
2. Task executes successfully (email sent)
3. TaskResult record created with SUCCESS status
4. Frontend refreshes status API
5. Status API reads from `beat_schedule` → "Send Test Email" not found
6. Falls back to database PeriodicTask → finds it
7. Calls `_get_last_run()` with task path
8. **BUG:** Task path from database might not match TaskResult task name!

---

## 🔍 **Task Name Mismatch Investigation**

**In Database (PeriodicTask):**
```
name: "Send Test Email"
task: "apps.scheduler.tasks.send_test_email_to_self"
```

**In TaskResult (after execution):**
```
task_name: "apps.scheduler.tasks.send_test_email_to_self"  ← Should match!
status: SUCCESS
date_done: 2026-01-26 08:00:00
```

**In task_monitor.py `_get_last_run()` (Line 209):**
```python
last_result = TaskResult.objects.filter(
    task_name=task_name  # ← Searches for exact match
).exclude(
    status='REVOKED'
).order_by('-date_done').first()
```

**Should work IF:** Task name matches exactly between PeriodicTask and TaskResult

---

## 🧪 **Diagnostic Test**

Let's verify the task name match on staging:

```bash
# Check PeriodicTask task path
docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
test_email_task = PeriodicTask.objects.filter(name__icontains='Test Email').first()
if test_email_task:
    print(f'PeriodicTask task: {test_email_task.task}')
else:
    print('PeriodicTask not found')
"

# Check TaskResult task name
docker compose exec -T backend python manage.py shell -c "
from django_celery_results.models import TaskResult
test_email_results = TaskResult.objects.filter(task_name__icontains='test_email').order_by('-date_done')[:3]
print(f'TaskResult count: {test_email_results.count()}')
for r in test_email_results:
    print(f'TaskResult task_name: {r.task_name}')
    print(f'  Status: {r.status}, Date: {r.date_done}')
"

# Check what status API returns for test email task
docker compose exec -T backend python manage.py shell -c "
from apps.scheduler.task_monitor import get_task_status
status = get_task_status()
test_tasks = [t for t in status['tasks'] if 'test' in t['name'].lower() or 'email' in t['name'].lower()]
print(f'Tasks with test/email: {len(test_tasks)}')
for t in test_tasks:
    print(f\"Task: {t['name']}\")
    print(f\"  Path: {t['task_path']}\")
    print(f\"  Last run: {t['last_run']['relative_time']}\")
    print(f\"  Status: {t['status']}\")
"
```

---

## 💡 **Expected Findings**

### **Scenario A: Task Name Matches** ✅
```
PeriodicTask task: apps.scheduler.tasks.send_test_email_to_self
TaskResult task_name: apps.scheduler.tasks.send_test_email_to_self
Status API: Shows recent execution timestamp
```
**If this:** Frontend should update correctly, but there's a different bug

### **Scenario B: Task Name Mismatch** ❌
```
PeriodicTask task: apps.scheduler.tasks.send_test_email_to_self
TaskResult task_name: apps.scheduler.tasks.send_test_email  ← Different!
Status API: Shows "Never run"
```
**If this:** Task name inconsistency prevents status lookup

### **Scenario C: Task Not in Status API** ❌
```
Tasks with test/email: 0
```
**If this:** Task not being loaded into status API at all

---

## 🔧 **Solutions by Scenario**

### **Solution A: Task Not in beat_schedule**

Add to `backend/edms/celery.py` around line 110 (after other tasks):

```python
app.conf.beat_schedule = {
    # ... existing tasks ...
    
    # Manual Test Email (triggered manually, not scheduled)
    'send-test-email': {
        'task': 'apps.scheduler.tasks.send_test_email_to_self',
        'schedule': crontab(minute=0, hour=0, day_of_month=31, month_of_year=2),  # Feb 31 (never)
        'options': {
            'expires': 300,
            'priority': 3,
        }
    },
}
```

**Why this works:**
- Task now in `beat_schedule` so status API can find it
- Schedule set to impossible date (Feb 31) so it never runs automatically
- Can still be triggered manually
- Status API will now check TaskResult for execution history

---

### **Solution B: Fix Status API to Check ALL TaskResults**

Modify `backend/apps/scheduler/task_monitor.py` line 82:

```python
def get_task_status(self):
    # ... existing code ...
    
    # ALSO include tasks from TaskResult that aren't in beat_schedule
    # This catches manually-triggered tasks
    if CELERY_RESULTS_AVAILABLE and TaskResult:
        # Get unique task names from TaskResult in last 7 days
        recent_results = TaskResult.objects.filter(
            date_done__gte=timezone.now() - timedelta(days=7)
        ).values('task_name').distinct()
        
        for result in recent_results:
            task_path = result['task_name']
            # Skip if already in tasks list
            if any(t['task_path'] == task_path for t in tasks):
                continue
            
            # Add as discovered task
            task_info = self._get_task_info(
                task_path.split('.')[-1],  # Use function name as schedule_name
                task_path,
                {'task': task_path, 'schedule': None},
                all_registered_tasks,
                is_manual=True
            )
            tasks.append(task_info)
```

**Why this works:**
- Discovers tasks from TaskResult execution history
- No need to add to beat_schedule
- Shows any task that has executed recently
- More dynamic and flexible

---

### **Solution C: Frontend Poll More Aggressively After Trigger**

Modify `frontend/src/components/scheduler/TaskListWidget.tsx` line 108:

```typescript
if (result.success) {
    alert('✅ Task queued successfully!');
    
    // Poll multiple times to catch execution
    setTimeout(() => fetchTaskStatus(), 2000);   // 2 seconds
    setTimeout(() => fetchTaskStatus(), 5000);   // 5 seconds
    setTimeout(() => fetchTaskStatus(), 10000);  // 10 seconds
    setTimeout(() => fetchTaskStatus(), 20000);  // 20 seconds
}
```

**Why this works:**
- Task takes 1-3 seconds to execute
- 2-second delay might be too fast
- Multiple polls catch the update eventually
- Doesn't fix root cause but improves UX

---

## 🎯 **Recommended Solution: Combination**

**Best approach:** Apply Solutions A + C

1. **Add task to beat_schedule** (never-run schedule)
2. **Poll multiple times** after manual trigger
3. **Optional:** Also apply Solution B for robustness

---

## 📝 **Implementation Steps**

### **Step 1: Add Test Email to beat_schedule**

```bash
# On your local machine (not staging yet)
cd ~/edms

# Edit backend/edms/celery.py
# Add the send-test-email entry shown in Solution A

# Commit
git add backend/edms/celery.py
git commit -m "feat: Add send-test-email to beat_schedule for status tracking"
```

### **Step 2: Improve Frontend Polling**

```bash
# Edit frontend/src/components/scheduler/TaskListWidget.tsx
# Modify line 108 as shown in Solution C

# Commit
git add frontend/src/components/scheduler/TaskListWidget.tsx
git commit -m "fix: Poll multiple times after manual task trigger"
```

### **Step 3: Deploy to Staging**

```bash
git push origin main

# On staging server
cd ~/edms
git pull origin main

# Rebuild containers (code changed)
docker compose stop backend frontend
docker compose build backend frontend
docker compose up -d backend frontend

# Wait 30 seconds for startup
sleep 30
```

### **Step 4: Test**

```bash
# Open browser to staging
# Go to Admin → Scheduler Dashboard
# Click "Run Now" on "Send Test Email"
# Wait 2-5 seconds
# Dashboard should update with recent execution time
```

---

## 🔍 **Verification**

After applying fix, verify:

```bash
# Check task appears in status API
curl -s http://staging-server:8001/api/v1/scheduler/monitoring/status/ | jq '.tasks[] | select(.name | contains("Test Email"))'

# Should show:
{
  "schedule_name": "send-test-email",
  "task_path": "apps.scheduler.tasks.send_test_email_to_self",
  "name": "Send Test Email",
  "last_run": {
    "timestamp": "2026-01-26T08:15:30+00:00",  ← Recent timestamp!
    "relative_time": "5m ago",  ← Not "Never run"!
    "status": "SUCCESS"
  },
  "status": "SUCCESS"
}
```

---

## 📊 **Summary**

### **Root Cause:**
`send_test_email_to_self` task not in `beat_schedule`, so status API can't track it properly

### **Why Email Works:**
Task executes fine, creates TaskResult record, email sends

### **Why Status Doesn't Update:**
Status API only tracks tasks from `beat_schedule` + database PeriodicTask, and task lookup may fail

### **The Fix:**
1. Add task to `beat_schedule` with never-run schedule
2. Poll multiple times after manual trigger
3. Rebuild containers to load new code

### **Expected Result:**
After manual trigger, dashboard updates within 5-10 seconds showing recent execution

---

**Run the diagnostic commands above to confirm which scenario you have, then apply the appropriate solution!**
