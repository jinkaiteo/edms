# Scheduler Manual Trigger Timeout Fix - Summary

**Date:** January 16, 2026  
**Issue:** `timeout of 30000ms exceeded` when manually triggering scheduler tasks  
**Status:** ✅ **FIXED**

---

## What Was Wrong

**Symptom:**
```javascript
Failed to trigger task: 
{error: {code: 'ECONNABORTED', message: 'timeout of 30000ms exceeded'}}
```

**Root Cause:**
- Backend was waiting synchronously for task completion: `async_result.get(timeout=30)`
- If task took >30 seconds OR Celery worker was busy, HTTP request would timeout
- Frontend also had 30-second timeout, causing double timeout issue

**Old Flow:**
```
User clicks "Run Now" 
  → Frontend waits 30s
    → Backend waits 30s for task completion
      → Task executes
      → Backend returns result
    → Frontend gets response
  → User sees result

❌ Problem: If task takes >30s, everything times out
```

---

## What Was Fixed

**Solution:** Fire-and-forget pattern - queue task and return immediately

**New Flow:**
```
User clicks "Run Now"
  → Frontend waits ~0.5s
    → Backend queues task in Celery
    → Backend returns task_id immediately
  → Frontend shows "Task queued successfully"
  → Task executes in background
  → Dashboard auto-refreshes to show result

✅ Result: Instant response, no timeouts
```

---

## Changes Made

### 1. Backend Fix
**File:** `backend/apps/scheduler/monitoring_dashboard.py`

**Before:**
```python
async_result = celery_task.apply_async()
result = async_result.get(timeout=30)  # ❌ Blocks for 30 seconds
return {'success': True, 'result': result}
```

**After:**
```python
async_result = celery_task.apply_async()
# ✅ Return immediately with task_id
return {
    'success': True,
    'task_id': async_result.id,
    'status': 'queued',
    'message': 'Task queued successfully'
}
```

### 2. Frontend Fix
**File:** `frontend/src/components/scheduler/TaskListWidget.tsx`

**Before:**
```typescript
const result = await apiService.post('/scheduler/monitoring/manual-trigger/', {...});
await fetchTaskStatus();
alert(`Task executed successfully! Duration: ${result.duration_seconds}s`);
```

**After:**
```typescript
const result = await apiService.post('/scheduler/monitoring/manual-trigger/', {...});
if (result.success) {
  alert(
    `✅ Task queued successfully!\n` +
    `Task ID: ${result.task_id}\n` +
    `Status: ${result.status}\n\n` +
    `The task is running in the background.`
  );
  setTimeout(() => fetchTaskStatus(), 2000); // Refresh after 2 seconds
}
```

---

## Deployment Instructions

### Option 1: Automated Deployment (Recommended)

```bash
./deploy_scheduler_timeout_fix.sh
```

### Option 2: Manual Deployment

```bash
# 1. Stop services
docker compose down

# 2. Rebuild backend and frontend
docker compose build backend frontend

# 3. Start all services
docker compose up -d

# 4. Wait for services to be ready
sleep 15

# 5. Verify deployment
docker compose ps
```

---

## Testing the Fix

### Test 1: Manual Trigger via UI

1. Navigate to: `http://your-server/admin/dashboard`
2. Find the "Scheduled Tasks" widget
3. Expand any category (e.g., "Document Lifecycle")
4. Click "▶️ Run Now" on any task
5. **Expected Result:**
   ```
   ✅ Task queued successfully!
   
   Task: process-document-effective-dates
   Task ID: abc-123-def-456
   Status: queued
   
   The task is now running in the background.
   The dashboard will update automatically when it completes.
   ```
6. Wait 2 seconds - dashboard auto-refreshes
7. Task status should update to show "SUCCESS" or "COMPLETED"

### Test 2: Manual Trigger via API

```bash
# Trigger a task
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}'

# Expected response (instant, ~0.5s):
{
  "success": true,
  "task_name": "perform_system_health_check",
  "task_display_name": "System Health Check",
  "task_id": "abc-123-def-456",
  "execution_time": "2026-01-16T23:51:05.123456+00:00",
  "status": "queued",
  "message": "Task queued successfully. Check task list for execution results.",
  "executed_by": "admin"
}
```

### Test 3: Verify Task Execution

```bash
# Check backend logs
docker logs edms_backend --tail=50 | grep "queued successfully"
# Output: Task perform_system_health_check queued successfully with ID: abc-123-def

# Check celery worker logs
docker logs edms_celery_worker --tail=50 | grep "perform_system_health_check"
# Output: 
# Task apps.scheduler.tasks.perform_system_health_check[abc-123-def] received
# Task apps.scheduler.tasks.perform_system_health_check[abc-123-def] succeeded
```

---

## Before vs After Comparison

| Aspect | Before (Synchronous) | After (Fire-and-Forget) |
|--------|---------------------|------------------------|
| **Response Time** | 30+ seconds | ~0.5 seconds ✅ |
| **Timeout Risk** | High ❌ | None ✅ |
| **User Experience** | Waiting, uncertain | Instant feedback ✅ |
| **Long-running Tasks** | Fail after 30s ❌ | Complete normally ✅ |
| **Task Execution** | Blocks HTTP request | Background, async ✅ |
| **Error Handling** | Connection timeout | Clean error messages ✅ |

---

## Verification Checklist

After deployment, verify:

- ✅ Backend container rebuilt successfully
- ✅ Frontend container rebuilt successfully
- ✅ All services running (6 containers)
- ✅ Manual trigger returns instantly (<2 seconds)
- ✅ No timeout errors in browser console
- ✅ Task executes successfully in background
- ✅ Dashboard auto-refreshes after 2 seconds
- ✅ Audit trail records task execution

---

## Rollback Plan

If issues occur, rollback with:

```bash
# 1. Checkout previous commit
git checkout HEAD~1

# 2. Rebuild and restart
docker compose down
docker compose build backend frontend
docker compose up -d
```

Or revert specific files:
```bash
git checkout HEAD~1 -- backend/apps/scheduler/monitoring_dashboard.py
git checkout HEAD~1 -- frontend/src/components/scheduler/TaskListWidget.tsx
docker compose restart backend frontend
```

---

## Additional Benefits

Beyond fixing the timeout issue, this change provides:

1. **Better Scalability** - Can handle long-running tasks (hours) without HTTP connection limits
2. **Improved UX** - Users get instant feedback instead of waiting
3. **Resource Efficiency** - No HTTP connections held open for 30+ seconds
4. **Clearer Status** - Task ID allows tracking execution progress
5. **Audit Trail** - Still records task execution start in audit logs

---

## Related Documentation

- Full analysis: `SCHEDULER_MANUAL_TRIGGER_TIMEOUT_FIX.md`
- Scheduler overview: `SCHEDULER_SYSTEM_ANALYSIS.md`
- Architecture diagrams: `SCHEDULER_ARCHITECTURE_DIAGRAM.md`

---

## Support

If issues persist:

1. Check Celery worker is running: `docker compose ps | grep celery_worker`
2. Check Redis is accessible: `docker exec edms_redis redis-cli ping`
3. Check backend logs: `docker logs edms_backend --tail=100`
4. Check worker logs: `docker logs edms_celery_worker --tail=100`
5. Verify task registration: `docker exec edms_backend python manage.py shell -c "from celery import current_app; print(current_app.control.inspect().registered())"`

---

**Status:** ✅ Ready for Production  
**Risk Level:** Low (only affects manual trigger feature)  
**Testing Required:** Manual trigger functionality  
**Downtime:** ~2 minutes for container rebuild
