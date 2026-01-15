# Scheduler Tasks Audit - What to Keep and What to Remove

**Date:** January 15, 2026  
**Current Task Count:** 12 scheduled tasks  
**Recommendation:** Remove or modify 7 tasks (58% reduction possible)

---

## Executive Summary

Out of 12 scheduled tasks, **5 are actively working** and **7 have issues**:
- ✅ 3 tasks working perfectly
- ⚠️ 2 tasks are placeholders (do nothing)
- ⚠️ 2 tasks are legacy no-ops (WorkflowTask removed)
- ❌ 3 backup tasks that cannot work in containers

---

## Task-by-Task Analysis

### 🟢 KEEP - Working Perfectly (5 tasks)

#### 1. ✅ Process Effective Dates
- **Status:** ACTIVE ✅
- **Schedule:** Every hour
- **Purpose:** Activates documents when effective_date arrives
- **Evidence:** Successfully processed TEST-SCHEDULER-2026 document today
- **Recommendation:** **KEEP** - Core functionality

#### 2. ✅ Process Obsolescence Dates  
- **Status:** ACTIVE ✅
- **Schedule:** Every hour (minute 15)
- **Purpose:** Obsoletes documents when obsolescence_date arrives
- **Evidence:** Task runs successfully (0 documents pending is normal)
- **Recommendation:** **KEEP** - Core functionality

#### 3. ✅ Check Workflow Timeouts
- **Status:** ACTIVE ✅
- **Schedule:** Every 4 hours
- **Purpose:** Monitors overdue workflows, sends escalation emails
- **Evidence:** Runs successfully, checks active workflows
- **Recommendation:** **KEEP** - Important monitoring

#### 4. ✅ System Health Check
- **Status:** ACTIVE ✅
- **Schedule:** Every 30 minutes
- **Purpose:** Comprehensive system health validation
- **Evidence:** Successfully runs, creates audit trails
- **Recommendation:** **KEEP** - Critical monitoring

#### 5. ✅ Cleanup Celery Results (NEW)
- **Status:** ACTIVE ✅
- **Schedule:** Daily at 03:00
- **Purpose:** Cleans old task results and REVOKED tasks
- **Evidence:** Just cleaned 423 REVOKED tasks successfully
- **Recommendation:** **KEEP** - Essential maintenance

---

### ⚠️ PLACEHOLDER - Do Nothing (2 tasks)

#### 6. ⚠️ Process Notification Queue
- **Status:** PLACEHOLDER
- **Schedule:** Every 5 minutes
- **Purpose:** Process queued notifications (future implementation)
- **Current Code:**
  ```python
  processed_count = 0  # Does nothing
  return {'processed': processed_count}
  ```
- **Evidence:** Runs 288 times/day, processes 0 notifications
- **Cost:** Wasted CPU cycles, database bloat
- **Recommendation:** **REMOVE** or disable until actually implemented

#### 7. ⚠️ Daily Summary Emails
- **Status:** PLACEHOLDER
- **Schedule:** Daily at 08:00
- **Purpose:** Send daily summary emails (future implementation)
- **Current Code:**
  ```python
  sent_count = 0  # Does nothing
  return {'sent': sent_count}
  ```
- **Evidence:** Runs but sends 0 emails
- **Recommendation:** **REMOVE** or disable until actually implemented

---

### ⚠️ LEGACY NO-OP - WorkflowTask Removed (2 tasks)

#### 8. ⚠️ Cleanup Workflow Tasks
- **Status:** LEGACY NO-OP
- **Schedule:** Every 6 hours
- **Purpose:** Clean up orphaned workflow tasks
- **Issue:** `WorkflowTask` model was removed in favor of document filtering
- **Current Code:** 
  ```python
  # WorkflowTask removed - using document filtering approach
  final_state_tasks = []  # No actual tasks to process
  ```
- **Evidence:** Code has 18 comments saying "WorkflowTask removed"
- **Recommendation:** **REMOVE** - Does nothing, just burns CPU

#### 9. ⚠️ Weekly Comprehensive Cleanup
- **Status:** LEGACY NO-OP (duplicate of #8)
- **Schedule:** Sundays at 02:00
- **Purpose:** Same as #8, but runs weekly
- **Issue:** Same function as #8, also does nothing
- **Recommendation:** **REMOVE** - Duplicate of non-functional task

---

### ❌ BROKEN - Cannot Work in Containers (3 tasks)

#### 10. ❌ Database Backup Daily
- **Status:** BROKEN ❌
- **Schedule:** Daily at 02:00
- **Purpose:** Automated database + file backup
- **Issue:** Requires host-level docker-compose access, cannot run from container
- **Evidence:**
  - Task never appears in TaskResult (0 executions)
  - Creates empty tmp folders: `backups/tmp_20260115_020001/` with 0-byte files
  - Returns: `'error': 'Backup must be run from host system'`
- **Recommendation:** **REMOVE from Celery** - Use cron on host instead

#### 11. ❌ Database Backup Weekly
- **Status:** BROKEN ❌
- **Schedule:** Sundays at 03:00
- **Purpose:** Same as #10
- **Issue:** Same as #10
- **Recommendation:** **REMOVE from Celery** - Use cron on host instead

#### 12. ❌ Database Backup Monthly
- **Status:** BROKEN ❌
- **Schedule:** 1st of month at 04:00
- **Purpose:** Same as #10
- **Issue:** Same as #10
- **Recommendation:** **REMOVE from Celery** - Use cron on host instead

---

## Detailed Recommendations

### HIGH PRIORITY: Remove Broken Backup Tasks (3 tasks)

**Problem:** Backup tasks run from Celery Beat but fail silently because:
1. They need docker-compose access to run `docker compose exec`
2. Containers cannot execute host docker-compose commands
3. Tasks create empty directories and log warnings but appear to succeed

**Solution:** Remove from Celery, use **host-level cron** instead:

```bash
# Add to host crontab
0 2 * * * cd /path/to/edms && ./scripts/backup-hybrid.sh >> /var/log/edms-backup.log 2>&1
0 3 * * 0 cd /path/to/edms && ./scripts/backup-hybrid.sh >> /var/log/edms-backup.log 2>&1
0 4 1 * * cd /path/to/edms && ./scripts/backup-hybrid.sh >> /var/log/edms-backup.log 2>&1
```

**Why:** The backup script `backup-hybrid.sh` is designed to run from the host and execute docker commands. It cannot work from inside a container.

---

### MEDIUM PRIORITY: Remove Placeholder Tasks (2 tasks)

**Problem:** Tasks run hundreds of times per day but do nothing:
- `process-notification-queue`: 288 executions/day × 0 notifications = wasted effort
- `send-daily-summary`: 1 execution/day × 0 emails = wasted effort

**Impact:**
- Database bloat (16 TaskResult records/day from these alone)
- Misleading metrics (shows "tasks running" but accomplishing nothing)
- Maintenance overhead (need to monitor tasks that serve no purpose)

**Solution:** Comment out in `celery.py` until actually implemented:

```python
# Disabled - not yet implemented
# 'process-notification-queue': { ... },
# 'send-daily-summary': { ... },
```

---

### LOW PRIORITY: Remove Legacy Cleanup Tasks (2 tasks)

**Problem:** WorkflowTask model was removed, but cleanup tasks remain:
- Code has 11 comments saying "WorkflowTask removed"
- Functions return immediately with no actual cleanup
- Misleading task names suggest they do something useful

**Solution:** Remove both tasks:
- `cleanup-workflow-tasks`
- `weekly-comprehensive-cleanup`

**Note:** These are lower priority because at least they don't create data issues like the backup tasks do.

---

## Proposed New Schedule (5 tasks)

After cleanup, you'll have a lean, functional scheduler:

| Task | Schedule | Purpose |
|------|----------|---------|
| Process Effective Dates | Every hour | Activate pending documents |
| Process Obsolescence Dates | Every hour (min 15) | Obsolete scheduled documents |
| Check Workflow Timeouts | Every 4 hours | Monitor overdue workflows |
| System Health Check | Every 30 minutes | System monitoring |
| Cleanup Celery Results | Daily 03:00 | Clean old task logs |

**Benefits:**
- ✅ All 5 tasks are actively working
- ✅ No silent failures or placeholders
- ✅ 58% reduction in scheduled tasks (12 → 5)
- ✅ Clearer monitoring (only meaningful tasks)
- ✅ Reduced database load (fewer TaskResult records)

---

## Implementation Plan

### Step 1: Remove Broken Backup Tasks (Immediate)

**File:** `backend/edms/celery.py`

Remove lines 110-138:
```python
# REMOVE THESE - they cannot work from containers
# 'hybrid-backup-daily': { ... },
# 'hybrid-backup-weekly': { ... },
# 'hybrid-backup-monthly': { ... },
```

**Replace with host cron:**
```bash
# On the host machine, add to crontab
crontab -e

# Add these lines
0 2 * * * cd /home/user/edms && ./scripts/backup-hybrid.sh
0 3 * * 0 cd /home/user/edms && ./scripts/backup-hybrid.sh
0 4 1 * * cd /home/user/edms && ./scripts/backup-hybrid.sh
```

### Step 2: Remove Placeholder Tasks (When convenient)

**File:** `backend/edms/celery.py`

Comment out lines 68-86:
```python
# Disabled until notification system is implemented
# 'process-notification-queue': { ... },
# 'send-daily-summary': { ... },
```

### Step 3: Remove Legacy Cleanup Tasks (When convenient)

**File:** `backend/edms/celery.py`

Remove lines 88-108:
```python
# REMOVE THESE - WorkflowTask model no longer exists
# 'cleanup-workflow-tasks': { ... },
# 'weekly-comprehensive-cleanup': { ... },
```

### Step 4: Clean Up Empty Backup Folders (Housekeeping)

```bash
# Remove failed backup attempts
rm -rf backups/tmp_*/
```

### Step 5: Restart Services

```bash
docker compose restart celery_beat celery_worker
```

---

## Testing After Cleanup

### Verify Only 5 Tasks Remain

```bash
curl -s http://localhost:8000/api/v1/scheduler/monitoring/status/ | jq '.summary.total_tasks'
# Expected: 5
```

### Verify All Tasks Are Healthy

```bash
curl -s http://localhost:8000/api/v1/scheduler/monitoring/status/ | jq '.summary'
# Expected: { "total_tasks": 5, "healthy": 5, "failed": 0, "warnings": 0 }
```

### Verify Backups Work from Host

```bash
# On host machine
./scripts/backup-hybrid.sh

# Should create: backups/backup_YYYYMMDD_HHMMSS.tar.gz
ls -lh backups/*.tar.gz
```

---

## Benefits of Cleanup

### Before Cleanup:
- 12 tasks scheduled
- 4 actually working (33%)
- 7 broken/placeholder (58%)
- 3 creating empty backup folders
- 288+ wasted task executions per day

### After Cleanup:
- 5 tasks scheduled
- 5 actually working (100%)
- 0 broken/placeholder
- 0 wasted executions
- Clear, truthful monitoring

---

## Summary Table

| Task | Keep? | Reason |
|------|-------|--------|
| Process Effective Dates | ✅ YES | Core functionality |
| Process Obsolescence Dates | ✅ YES | Core functionality |
| Check Workflow Timeouts | ✅ YES | Important monitoring |
| System Health Check | ✅ YES | Critical monitoring |
| Cleanup Celery Results | ✅ YES | Essential maintenance |
| Process Notification Queue | ❌ NO | Placeholder (does nothing) |
| Daily Summary Emails | ❌ NO | Placeholder (does nothing) |
| Cleanup Workflow Tasks | ❌ NO | Legacy no-op (WorkflowTask removed) |
| Weekly Comprehensive Cleanup | ❌ NO | Legacy no-op (duplicate) |
| Database Backup Daily | ❌ NO | Cannot work in container |
| Database Backup Weekly | ❌ NO | Cannot work in container |
| Database Backup Monthly | ❌ NO | Cannot work in container |

**Final Count:** 5 tasks to KEEP, 7 tasks to REMOVE

---

## Questions?

**Q: Will removing these tasks break anything?**  
A: No. The tasks being removed are either placeholders (do nothing), legacy code (WorkflowTask removed), or broken (backup tasks that never worked).

**Q: What about backups?**  
A: Move them to host-level cron jobs where they can actually work. The script is already perfect, just needs to run from the host.

**Q: Can we re-add notification tasks later?**  
A: Yes! When the notification system is actually implemented, uncomment and configure those tasks.

**Q: Will this affect existing functionality?**  
A: No. All working functionality (document activation, obsolescence, health checks) remains intact.

---

**End of Audit**
