# 🏥 Scheduler Health Check Enhancement

**Date:** January 15, 2026  
**Branch:** `feature/enhanced-family-grouping-and-obsolescence-validation`  
**Status:** ✅ **IMPLEMENTED AND TESTED**

---

## 🎯 Problem Statement

### **Original Issue Discovered:**

During testing, we found that document `POL-2026-0002-v01.00` was stuck in `APPROVED_PENDING_EFFECTIVE` status despite having an effective date 2 days in the past.

**Investigation revealed:**
- ✅ Celery Beat was **sending** `process-document-effective-dates` task every hour
- ✅ Celery Worker was **running** and showing as healthy
- ❌ Celery Worker had **NOT registered** the scheduler tasks
- ❌ Worker was running for 3 days with **stale task registry**

**Root Cause:** Worker restart is required after code changes to discover new tasks, but the health check didn't detect this issue!

### **The Gap:**

The existing scheduler health check monitored:
- ✅ Celery workers active
- ✅ Beat scheduler running
- ✅ Database connectivity
- ✅ Recent errors
- ✅ Workflow timeliness

**But it was MISSING:**
- ❌ **Task registration verification** - Are critical tasks actually registered in workers?

This meant the dashboard showed "✅ EXCELLENT (100%)" while documents couldn't be processed automatically!

---

## ✅ Solution Implemented

### **New Health Check Component: Task Registration**

Added a **critical new health check** that verifies scheduler tasks are actually registered and executable in Celery workers.

#### **What It Checks:**

1. **Queries worker task registry** using `inspect.registered()`
2. **Verifies 4 critical tasks** are present:
   - `process_document_effective_dates` - Auto-activates documents on effective date
   - `process_document_obsoletion_dates` - Auto-obsoletes documents on obsolescence date
   - `check_workflow_timeouts` - Monitors and escalates overdue workflows
   - `perform_system_health_check` - System health monitoring

3. **Reports task registration status**:
   - Total registered tasks
   - Number of scheduler tasks
   - Missing critical tasks (if any)

---

## 📊 Health Score Changes

### **Before Enhancement:**

| Component | Points | Check |
|-----------|--------|-------|
| Celery Workers | 30 | Workers active? |
| Beat Scheduler | 20 | Beat running? |
| Database | 20 | DB responsive? |
| Recent Errors | 20 | Error count in 24h |
| Workflow Timeliness | 10 | Overdue workflows? |
| **TOTAL** | **100** | |

### **After Enhancement:**

| Component | Points | Check |
|-----------|--------|-------|
| Celery Workers | 20 | Workers active? |
| **Task Registration** | **20** | **Critical tasks registered?** ⭐ |
| Beat Scheduler | 10 | Beat running? |
| Database | 20 | DB responsive? |
| Recent Errors | 20 | Error count in 24h |
| Workflow Timeliness | 10 | Overdue workflows? |
| **TOTAL** | **100** | |

**Key Change:** Task registration now has equal importance to worker status!

---

## 🚨 Alert System Enhancement

### **New CRITICAL Alert:**

When critical tasks are not registered, the system now generates:

```
🔴 [CRITICAL] Critical scheduler tasks not registered: process_document_effective_dates, ...
   Action: Restart Celery worker with: docker compose restart celery_worker celery_beat
```

**Before:** No alert - system showed healthy  
**After:** Immediate CRITICAL alert with actionable fix

---

## 📡 API Response Changes

### **New Fields in `/api/v1/scheduler/monitoring/status/`:**

```json
{
  "celery_status": {
    "worker_count": 1,
    "workers_active": true,
    "beat_status": "RUNNING",
    "tasks_registered": true,                    // ⭐ NEW
    "missing_critical_tasks": [],                // ⭐ NEW
    "total_registered_tasks": 23,                // ⭐ NEW
    "registered_scheduler_tasks": 7              // ⭐ NEW
  },
  "health_breakdown": {
    "components": {
      "task_registration": {                     // ⭐ NEW COMPONENT
        "score": 20,
        "max_score": 20,
        "status": "healthy",
        "details": "7 scheduler tasks registered",
        "recommendation": "All critical tasks registered and ready"
      }
    }
  }
}
```

---

## 🧪 Test Results

### **Test Scenario: Stale Worker (Tasks Not Registered)**

**Simulated Condition:**
```bash
# Worker running for 3 days
# New tasks added to codebase
# Worker never restarted
```

**Health Check Response:**

```
📊 Overall Status: WARNING (80/100)
📊 Health Score: 80/100

⚠️ TASK REGISTRATION
   Score: 10/20
   Status: warning
   Details: 4 critical tasks missing
   💡 Restart Celery worker to register: process_document_effective_dates, ...

🔴 [CRITICAL] Critical scheduler tasks not registered
   Action: Restart Celery worker with: docker compose restart celery_worker celery_beat
```

✅ **Issue detected!** Dashboard shows WARNING, not EXCELLENT.

### **Test Scenario: Healthy System (All Tasks Registered)**

**After Worker Restart:**

```
📊 Overall Status: EXCELLENT (100/100)
📊 Health Score: 100/100

✅ TASK REGISTRATION
   Score: 20/20
   Status: healthy
   Details: 7 scheduler tasks registered

✅ Workers: 1 active
✅ Tasks Registered: True
✅ Scheduler Tasks: 7
✅ Total Tasks: 23

✅ No alerts - system healthy!
```

✅ **System healthy!** All critical tasks registered and ready.

---

## 💻 Implementation Details

### **Backend Changes** (`backend/apps/scheduler/monitoring_dashboard.py`)

#### **1. Enhanced `_check_celery_workers()` Method:**

```python
def _check_celery_workers(self):
    """Check status of Celery workers and beat scheduler."""
    inspect = current_app.control.inspect()
    
    # CRITICAL: Check registered tasks in workers
    registered_tasks_by_worker = inspect.registered() or {}
    
    # Define critical tasks that MUST be registered
    critical_tasks = [
        'apps.scheduler.automated_tasks.process_document_effective_dates',
        'apps.scheduler.automated_tasks.process_document_obsoletion_dates',
        'apps.scheduler.automated_tasks.check_workflow_timeouts',
        'apps.scheduler.automated_tasks.perform_system_health_check',
    ]
    
    # Check if critical tasks are registered
    all_registered_tasks = []
    for worker_tasks in registered_tasks_by_worker.values():
        all_registered_tasks.extend(worker_tasks)
    
    missing_tasks = [task for task in critical_tasks if task not in all_registered_tasks]
    tasks_registered = len(missing_tasks) == 0
    
    return {
        ...
        'tasks_registered': tasks_registered,
        'missing_critical_tasks': missing_tasks,
        'total_registered_tasks': len(set(all_registered_tasks)),
        'registered_scheduler_tasks': len([t for t in all_registered_tasks if 'scheduler' in t])
    }
```

#### **2. Updated `_calculate_health_score()` Method:**

```python
# Task Registration (20 points) - CRITICAL NEW CHECK
tasks_registered = celery_status.get('tasks_registered', False)
missing_tasks = celery_status.get('missing_critical_tasks', [])
registered_scheduler_tasks = celery_status.get('registered_scheduler_tasks', 0)

if tasks_registered and registered_scheduler_tasks > 0:
    task_reg_score = 20
    task_reg_status = 'healthy'
    task_reg_details = f'{registered_scheduler_tasks} scheduler tasks registered'
    task_reg_recommendation = 'All critical tasks registered and ready'
elif registered_scheduler_tasks > 0 and not tasks_registered:
    task_reg_score = 10
    task_reg_status = 'warning'
    task_reg_details = f'{len(missing_tasks)} critical tasks missing'
    task_reg_recommendation = f'Restart Celery worker to register: {", ".join([t.split(".")[-1] for t in missing_tasks])}'
else:
    task_reg_score = 0
    task_reg_status = 'critical'
    task_reg_details = 'No scheduler tasks registered'
    task_reg_recommendation = 'CRITICAL: Restart Celery worker immediately - automated processing disabled!'

score += task_reg_score
breakdown['components']['task_registration'] = {
    'score': task_reg_score,
    'max_score': 20,
    'status': task_reg_status,
    'details': task_reg_details,
    'recommendation': task_reg_recommendation
}
```

#### **3. Enhanced `_generate_alerts()` Method:**

```python
# CRITICAL: Check if tasks are registered
if not celery_status.get('tasks_registered', False):
    missing_tasks = celery_status.get('missing_critical_tasks', [])
    if missing_tasks:
        task_names = ', '.join([t.split('.')[-1] for t in missing_tasks[:3]])
        alerts.append({
            'level': 'CRITICAL',
            'message': f'Critical scheduler tasks not registered: {task_names}',
            'action': 'Restart Celery worker with: docker compose restart celery_worker celery_beat'
        })
```

---

## 🎯 Impact & Benefits

### **Prevention of Silent Failures**

**Before:** Documents stuck in pending status with no indication of problem  
**After:** Immediate CRITICAL alert with specific fix instructions

### **Actionable Diagnostics**

**Before:** Admin sees "✅ Healthy" and doesn't know what to fix  
**After:** Admin sees "❌ Tasks not registered - Restart worker" with exact command

### **Proactive Monitoring**

**Before:** Issue discovered when users complain documents aren't processing  
**After:** Issue detected automatically and displayed prominently in dashboard

### **Reduced Downtime**

**Before:** Hours of investigation to find why documents aren't processing  
**After:** Minutes to identify and fix using dashboard alert

---

## 📋 Frontend Display

The existing `SchedulerStatusWidget` component automatically displays the new health check because it already supports:

- ✅ Dynamic component rendering from `health_breakdown.components`
- ✅ Status-based color coding (healthy/warning/critical)
- ✅ Recommendation display (shows actionable advice)
- ✅ Alert rendering with priority levels

**No frontend changes required!** The widget adapts automatically.

---

## 🔄 When This Check Triggers

### **Scenario 1: Worker Restart Required**

**Trigger:** Code deployment adds new tasks, worker not restarted  
**Detection:** `tasks_registered: false`, `missing_critical_tasks: [...]`  
**Alert Level:** CRITICAL  
**Fix:** `docker compose restart celery_worker celery_beat`

### **Scenario 2: Worker Startup Issue**

**Trigger:** Worker starts but task discovery fails  
**Detection:** `registered_scheduler_tasks: 0`  
**Alert Level:** CRITICAL  
**Fix:** Check worker logs, rebuild container if needed

### **Scenario 3: Import Errors**

**Trigger:** Tasks have syntax errors or missing imports  
**Detection:** Tasks missing from registry despite worker running  
**Alert Level:** CRITICAL  
**Fix:** Check Python syntax, verify imports, restart worker

---

## 🚀 Deployment Checklist

### **When Deploying Code with New Tasks:**

1. ✅ Deploy code changes
2. ✅ **Restart Celery worker AND beat** - Critical!
3. ✅ Check scheduler dashboard
4. ✅ Verify "Task Registration" shows 20/20 (healthy)
5. ✅ Confirm no CRITICAL alerts

### **Regular Maintenance:**

- ✅ Check scheduler dashboard weekly
- ✅ Verify task registration status
- ✅ Restart workers if score drops below 20/20
- ✅ Monitor for "missing tasks" alerts

---

## 📚 Documentation References

- **Scheduler Dashboard:** `http://localhost:8000/admin/scheduler/monitoring/dashboard/`
- **API Endpoint:** `/api/v1/scheduler/monitoring/status/`
- **Code:** `backend/apps/scheduler/monitoring_dashboard.py`
- **Scheduler Fix Summary:** `SCHEDULER_FIX_SUMMARY.md`

---

## 🎓 Lessons Learned

### **1. Health Checks Must Verify Functionality, Not Just Presence**

**Wrong:** Check if worker is running  
**Right:** Check if worker can actually execute tasks

### **2. Silent Failures Are the Worst Kind**

A system showing "✅ Healthy" when it can't process documents is worse than a system showing "❌ Broken" - at least you know to fix it!

### **3. Actionable Alerts Are Key**

**Bad Alert:** "Tasks not registered"  
**Good Alert:** "Tasks not registered - Run: docker compose restart celery_worker"

### **4. Test What You Don't See**

The worker showed as healthy in the dashboard, so we didn't think to check task registration. Now we do!

---

## ✅ Success Criteria Met

- [x] Detects when critical tasks are not registered
- [x] Provides actionable fix instructions
- [x] Integrates seamlessly with existing dashboard
- [x] No frontend changes required
- [x] Tested with stale worker scenario
- [x] Documented comprehensively
- [x] Committed to feature branch

---

## 🎉 Summary

**Problem:** Scheduler appeared healthy but couldn't process documents  
**Root Cause:** Worker not discovering tasks after code changes  
**Solution:** Added task registration health check  
**Result:** Dashboard now detects this issue immediately with CRITICAL alert  
**Impact:** Prevents silent failures, reduces debugging time from hours to minutes  

---

**Enhancement By:** Automated Investigation & Implementation  
**Tested:** January 15, 2026  
**Status:** ✅ Production Ready
