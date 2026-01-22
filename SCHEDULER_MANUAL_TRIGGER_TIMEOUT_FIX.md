# Scheduler Manual Trigger Timeout Issue - Analysis & Fix

**Issue Reported:** January 16, 2026
**Error:** `timeout of 30000ms exceeded` when manually triggering scheduler tasks

---

## Problem Analysis

### Root Cause

The issue is in `backend/apps/scheduler/monitoring_dashboard.py` line 205:

```python
# Execute the task asynchronously so it gets saved to TaskResult
celery_task = task_info['celery_task']
async_result = celery_task.apply_async()

# Wait for the task to complete (with timeout)
result = async_result.get(timeout=30)  # ← PROBLEM HERE
```

**What's happening:**

1. **Frontend timeout:** 30 seconds (in `api.ts`)
2. **Backend wait:** 30 seconds (in `monitoring_dashboard.py` line 205)
3. **Total delay:** If Celery worker is busy or task takes >30s, both timeouts trigger

**Why it fails:**

- `async_result.get(timeout=30)` **blocks** the HTTP request until task completes
- If task takes 30+ seconds, it times out
- If Celery worker is processing other tasks, it queues and waits
- Frontend sees no response and times out at 30 seconds
- User sees: `{error: {code: 'ECONNABORTED', message: 'timeout of 30000ms exceeded'}}`

---

## The Fix

**Strategy:** Use **asynchronous task triggering** instead of synchronous waiting.

### Option 1: Fire-and-Forget (Recommended) ⚡

Return immediately after queuing the task, don't wait for completion.

**Changes needed:**

#### 1. Update `monitoring_dashboard.py` - `manually_execute_task()` method

```python
def manually_execute_task(self, task_name, user=None, dry_run=False):
    """
    Manually execute a scheduled task with full audit trail.
    
    MODIFIED: Returns immediately after queuing task (fire-and-forget pattern).
    Task execution status can be checked via task_id.
    """
    if task_name not in self.available_tasks:
        return {
            'success': False,
            'error': f'Unknown task: {task_name}',
            'available_tasks': list(self.available_tasks.keys())
        }
    
    task_info = self.available_tasks[task_name]
    
    try:
        # Get user for audit trail
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not user or not user.is_authenticated:
            user = User.objects.filter(is_staff=True, is_active=True).first()
            if not user:
                user = User.objects.filter(is_active=True).first()
            if not user:
                user = User.objects.create(
                    username='admin',
                    email='admin@edms.local',
                    is_staff=True,
                    is_active=True
                )
        
        start_time = timezone.now()
        
        # Create audit record for manual execution
        AuditTrail.objects.create(
            user=user,
            action='TASK_EXECUTION_STARTED',
            description=f'Manual execution: {task_info["name"]}'[:200],
            field_changes={
                'task_name': task_name,
                'task_description': task_info['description'],
                'dry_run': dry_run,
                'execution_time': start_time.isoformat()
            },
            ip_address=getattr(user, '_current_ip', '127.0.0.1'),
            user_agent=getattr(user, '_current_user_agent', 'Manual Execution')
        )
        
        # Execute the task asynchronously
        celery_task = task_info['celery_task']
        
        # Handle tasks that support parameters
        if task_name == 'cleanup_celery_results':
            async_result = celery_task.apply_async(kwargs={
                'days_to_keep': 7,
                'remove_revoked': True
            })
        else:
            async_result = celery_task.apply_async()
        
        # ✅ FIX: Return immediately with task_id instead of waiting
        return {
            'success': True,
            'task_name': task_name,
            'task_display_name': task_info['name'],
            'task_id': async_result.id,
            'execution_time': start_time.isoformat(),
            'status': 'queued',
            'message': 'Task queued successfully. Check status in task list.',
            'executed_by': user.get_full_name() or user.username
        }
        
    except Exception as e:
        logger.error(f"Failed to queue task {task_name}: {str(e)}")
        
        # Create error audit record
        AuditTrail.objects.create(
            user=user,
            action='TASK_EXECUTION_FAILED',
            description=f'Failed to queue: {task_info["name"]} - {str(e)}'[:200],
            field_changes={
                'task_name': task_name,
                'error': str(e),
                'dry_run': dry_run
            },
            ip_address=getattr(user, '_current_ip', '127.0.0.1'),
            user_agent=getattr(user, '_current_user_agent', 'Manual Execution')
        )
        
        return {
            'success': False,
            'task_name': task_name,
            'error': str(e),
            'executed_by': user.get_full_name() or user.username
        }
```

#### 2. Update Frontend - `TaskListWidget.tsx` (line 83-106)

```typescript
const handleManualTrigger = async (taskName: string) => {
  if (!window.confirm(`Are you sure you want to manually trigger this task?\n\nTask: ${taskName}`)) {
    return;
  }

  setTriggeringTask(taskName);
  try {
    // Convert hyphenated schedule name to underscore format expected by backend
    const backendTaskName = taskName.replace(/-/g, '_');
    const result = await apiService.post('/scheduler/monitoring/manual-trigger/', {
      task_name: backendTaskName
    });
    
    // Check if task was queued successfully
    if (result.success) {
      alert(
        `✅ Task queued successfully!\n\n` +
        `Task: ${taskName}\n` +
        `Task ID: ${result.task_id}\n` +
        `Status: ${result.status}\n\n` +
        `The task is now running in the background. ` +
        `The dashboard will update automatically when it completes.`
      );
      
      // Refresh after a short delay to show updated status
      setTimeout(() => fetchTaskStatus(), 2000);
    } else {
      alert(`❌ Failed to queue task: ${result.error}`);
    }
  } catch (err: any) {
    console.error('Failed to trigger task:', err);
    alert(`❌ Failed to trigger task: ${err.response?.data?.error || err.message}`);
  } finally {
    setTriggeringTask(null);
  }
};
```

---

## Option 2: Increase Timeout (Quick Fix) ⏱️

If you want to keep synchronous execution (not recommended):

#### 1. Backend - Increase timeout to 120 seconds

```python
# Line 205 in monitoring_dashboard.py
result = async_result.get(timeout=120)  # Increased from 30 to 120 seconds
```

#### 2. Frontend - Increase timeout to 150 seconds

```typescript
// frontend/src/services/api.ts
timeout: 150000,  // Increased from 30000 to 150000 (150 seconds)
```

**Drawback:** HTTP requests hanging for 2+ minutes is poor UX. Not recommended.

---

## Recommended Solution

**Use Option 1 (Fire-and-Forget)** because:

✅ **Instant response** - User gets immediate feedback  
✅ **No timeouts** - Tasks can take as long as needed  
✅ **Better UX** - Dashboard auto-refreshes show progress  
✅ **Scalable** - Supports long-running tasks  
✅ **Audit trail** - Still records execution start  

**Implementation Steps:**

1. Apply backend changes to `monitoring_dashboard.py`
2. Apply frontend changes to `TaskListWidget.tsx`
3. Rebuild backend container: `docker compose build backend`
4. Restart services: `docker compose restart backend frontend`
5. Test manual trigger - should return instantly

---

## Testing the Fix

### Before Fix:
```bash
# Trigger a task - hangs for 30 seconds then times out
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "process_document_effective_dates"}' \
  -w "\nTime: %{time_total}s\n"

# Result: timeout after 30 seconds
```

### After Fix:
```bash
# Trigger a task - returns immediately
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "process_document_effective_dates"}' \
  -w "\nTime: %{time_total}s\n"

# Result: 
# {
#   "success": true,
#   "task_id": "abc-123-def",
#   "status": "queued",
#   "message": "Task queued successfully"
# }
# Time: 0.5s ✅
```

### Verify Task Execution:

```bash
# Check Celery worker logs
docker logs edms_celery_worker --tail=50 | grep process_document_effective_dates

# Should see:
# Task apps.scheduler.tasks.process_document_effective_dates[abc-123-def] received
# Task apps.scheduler.tasks.process_document_effective_dates[abc-123-def] succeeded
```

---

## Additional Debugging

If issue persists after fix:

### 1. Check Celery Worker Status

```bash
docker exec edms_backend python manage.py shell -c "
from celery import current_app
inspect = current_app.control.inspect()
active = inspect.active()
print('Active workers:', list(active.keys()) if active else 'None')
"
```

### 2. Check Registered Tasks

```bash
docker exec edms_backend python manage.py shell -c "
from celery import current_app
inspect = current_app.control.inspect()
registered = inspect.registered()
if registered:
    for worker, tasks in registered.items():
        scheduler_tasks = [t for t in tasks if 'scheduler' in t]
        print(f'{worker}: {len(scheduler_tasks)} scheduler tasks')
"
```

### 3. Check Task Queue

```bash
docker exec edms_redis redis-cli LLEN celery
docker exec edms_redis redis-cli LLEN scheduler
```

---

## Why This Pattern is Better

### Synchronous (Current - BAD) ❌
```
User → Frontend (wait) → Backend (wait) → Celery → Backend → Frontend → User
         30s timeout          30s timeout                        
```

### Asynchronous (Fix - GOOD) ✅
```
User → Frontend → Backend → Celery
         0.5s        0.5s      
         ↓
    Immediate response
    
Later: Dashboard auto-refresh shows result
```

---

## Summary

**Problem:** 30-second timeout when manually triggering tasks  
**Root Cause:** Synchronous wait for task completion in backend  
**Solution:** Fire-and-forget pattern - queue task and return immediately  
**Implementation:** Update `monitoring_dashboard.py` + `TaskListWidget.tsx`  
**Rebuild Required:** Yes - backend container needs rebuild  
**Testing:** Task should trigger instantly, no timeout errors  

Apply Option 1 changes and rebuild to fix the issue permanently.
