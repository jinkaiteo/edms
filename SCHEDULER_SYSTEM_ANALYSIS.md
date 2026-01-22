# EDMS Scheduler System - Comprehensive Analysis

**Generated:** January 16, 2026
**Status:** Production Active

---

## 1. System Overview

### 1.1 Application Architecture

**EDMS (Electronic Document Management System)** is a Django-based web application for managing controlled documents with compliance features for 21 CFR Part 11 (pharmaceutical/FDA regulations).

**Technology Stack:**
- **Backend:** Django 4.x with Django REST Framework
- **Frontend:** React (port 3000)
- **Database:** PostgreSQL 18
- **Message Broker:** Redis 7
- **Task Queue:** Celery with Celery Beat
- **Containerization:** Docker Compose

**Running Services:**
```
edms_backend        - Django application (port 8000)
edms_celery_worker  - Celery worker (multi-queue)
edms_celery_beat    - Celery Beat scheduler
edms_db             - PostgreSQL database (port 5432)
edms_redis          - Redis broker/cache (port 6379)
edms_frontend       - React frontend (port 3000)
```

---

## 2. Scheduler Architecture

### 2.1 Core Components

The scheduler system is located in `backend/apps/scheduler/` and consists of:

#### **A. Task Definitions** (`tasks.py`)
- Thin wrappers around service classes using `@shared_task` decorator
- Auto-discovered by Celery's autodiscover_tasks()
- Delegates all business logic to service classes

#### **B. Service Layer** (`services/`)
- **automation.py** - Document lifecycle automation
- **health.py** - System health monitoring
- **cleanup.py** - Celery results cleanup

#### **C. Celery Configuration** (`celery.py` + `celery_schedule.py`)
- Beat schedule configuration with cron patterns
- Task routing to different queues
- Retry policies and timeout configurations

#### **D. API & Monitoring** 
- **api_views.py** - REST API endpoints for scheduler data
- **monitoring_dashboard.py** - Django views for scheduler monitoring UI
- **notification_service.py** - Email notifications for automated events

#### **E. Models** (`models.py`)
- **ScheduledTask** - Simple model for future batch operations (minimal usage)

---

## 3. Scheduler Tasks Deep Dive

### 3.1 Document Lifecycle Tasks

#### **Task 1: Process Document Effective Dates**
```python
@shared_task(bind=True, max_retries=3)
def process_document_effective_dates(self):
```

**Purpose:** Automatically activate documents when their effective date is reached

**Schedule:** Every hour at minute 0 (hourly)

**Business Logic:**
1. Queries documents with status `APPROVED_PENDING_EFFECTIVE` where `effective_date <= today`
2. Updates document status to `EFFECTIVE`
3. Creates workflow transition record if workflow exists
4. Creates audit trail entry with automation metadata
5. Sends email notification to document author

**Integration Points:**
- Documents: `Document.objects.filter(status='APPROVED_PENDING_EFFECTIVE')`
- Workflows: Updates `DocumentWorkflow.current_state` to `EFFECTIVE`
- Audit: Creates `AuditTrail` record with action `'DOC_EFFECTIVE_PROCESSED'`
- Notifications: Calls `notification_service.send_document_effective_notification()`

**Key Features:**
- Transaction safety with `transaction.atomic()`
- System user attribution (`system_scheduler` user)
- Comprehensive error tracking and retry mechanism
- Detailed results reporting

---

#### **Task 2: Process Document Obsoletion Dates**
```python
@shared_task(bind=True, max_retries=3)
def process_document_obsoletion_dates(self):
```

**Purpose:** Automatically mark documents as obsolete when their obsolescence date is reached

**Schedule:** Every hour at minute 15

**Business Logic:**
1. Queries documents with status `SCHEDULED_FOR_OBSOLESCENCE` where `obsolescence_date <= today`
2. Updates document status to `OBSOLETE`
3. Updates workflow state and marks as terminated
4. Creates audit trail with obsoletion details
5. Sends obsolescence notification

**Integration Points:**
- Documents: Updates to `OBSOLETE` status
- Workflows: Sets `is_terminated=True` and state to `OBSOLETE`
- Audit: Action `'DOC_OBSOLETED'`

**Status Flow:**
```
APPROVED_PENDING_EFFECTIVE → EFFECTIVE → SCHEDULED_FOR_OBSOLESCENCE → OBSOLETE
```

---

### 3.2 Workflow Monitoring Tasks

#### **Task 3: Check Workflow Timeouts**
```python
@shared_task
def check_workflow_timeouts():
```

**Purpose:** Monitor overdue workflows and send escalation notifications

**Schedule:** Every 4 hours at minute 0 (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)

**Business Logic:**
1. Finds active workflows (`is_terminated=False`, `current_state.is_final=False`)
2. Checks if `due_date < today`
3. Calculates days overdue
4. Sends escalation emails for workflows overdue >7 days

**Escalation Threshold:** 7 days overdue triggers notification

**Returns:**
- `checked_count` - Total workflows examined
- `timeout_count` - Number of overdue workflows
- `notification_count` - Escalation emails sent
- `overdue_workflows[]` - Detailed list with days overdue

---

#### **Task 4: Cleanup Workflow Tasks (Deprecated)**
```python
@shared_task
def cleanup_workflow_tasks(dry_run: bool = False):
```

**Purpose:** Legacy no-op task (WorkflowTask model was removed)

**Schedule:** Every 6 hours + Weekly Sunday 02:00

**Status:** Returns success but performs no operations

**Historical Context:** 
- Previously cleaned up `WorkflowTask` model records
- Model removed in favor of direct document filtering
- Task kept for backward compatibility with existing scheduled jobs

---

### 3.3 System Maintenance Tasks

#### **Task 5: System Health Check**
```python
@shared_task
def perform_system_health_check():
```

**Purpose:** Comprehensive system monitoring

**Schedule:** Every 30 minutes

**Health Checks:**
1. **Database** - Connectivity, counts (users, documents, workflows)
2. **Workflows** - Active vs completed workflow counts
3. **Audit System** - Recent audit record count (24h window)
4. **Document Storage** - Accessibility and document count
5. **Performance** - CPU, memory, disk usage (placeholder metrics)

**Returns:**
```python
{
    'overall_status': 'HEALTHY' | 'UNHEALTHY' | 'CRITICAL',
    'timestamp': ISO timestamp,
    'checks': {...},
    'warnings': [...],
    'errors': [...]
}
```

**Audit Integration:** Creates `AuditTrail` record with action `'SYSTEM_HEALTH_CHECK'`

---

#### **Task 6: Cleanup Celery Results**
```python
@shared_task(name='apps.scheduler.celery_cleanup.cleanup_celery_results')
def cleanup_celery_results(days_to_keep=7, remove_revoked=True):
```

**Purpose:** Clean up old Celery task execution records

**Schedule:** Daily at 03:00 AM

**Logic:**
1. Deletes `TaskResult` records older than 7 days
2. Removes all `REVOKED` status tasks (noise reduction)
3. Reports before/after counts

**Configuration:**
- `days_to_keep`: 7 days (configurable)
- `remove_revoked`: True (removes all revoked tasks)

**Storage:** Uses `django_celery_results.models.TaskResult`

---

## 4. Celery Configuration

### 4.1 Beat Schedule (`backend/edms/celery.py`)

```python
app.conf.beat_schedule = {
    'process-document-effective-dates': {
        'task': 'apps.scheduler.tasks.process_document_effective_dates',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'expires': 3600, 'priority': 8}
    },
    'process-document-obsoletion-dates': {
        'task': 'apps.scheduler.tasks.process_document_obsoletion_dates',
        'schedule': crontab(minute=15),  # Every hour at :15
        'options': {'expires': 3600, 'priority': 8}
    },
    'check-workflow-timeouts': {
        'task': 'apps.scheduler.tasks.check_workflow_timeouts',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'options': {'expires': 7200, 'priority': 6}
    },
    'perform-system-health-check': {
        'task': 'apps.scheduler.tasks.perform_system_health_check',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'expires': 1800, 'priority': 4}
    },
    'cleanup-celery-results': {
        'task': 'apps.scheduler.celery_cleanup.cleanup_celery_results',
        'schedule': crontab(minute=0, hour=3),  # Daily 03:00
        'kwargs': {'days_to_keep': 7, 'remove_revoked': True},
        'options': {'expires': 3600, 'priority': 5}
    }
}
```

### 4.2 Task Routing

```python
app.conf.task_routes = {
    'apps.documents.tasks.*': {'queue': 'documents'},
    'apps.workflows.tasks.*': {'queue': 'workflows'},
    'apps.scheduler.tasks.cleanup_workflow_tasks': {'queue': 'maintenance'},
    'apps.scheduler.tasks.*': {'queue': 'scheduler'},
    'apps.audit.tasks.*': {'queue': 'maintenance'},
}
```

**Celery Worker Configuration:**
```bash
celery -A edms worker -l info -Q celery,scheduler,documents,workflows,maintenance
```

The worker listens to **5 queues** for task distribution.

### 4.3 Global Settings

```python
CELERY_TIMEZONE = 'UTC'  # All scheduling in UTC
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_RESULT_BACKEND = "django-db"  # Store results in Django DB
CELERY_RESULT_EXPIRES = 86400  # Keep results for 24 hours
```

---

## 5. Integration with App Components

### 5.1 Document Model Integration

**Document Statuses Monitored by Scheduler:**
```
APPROVED_PENDING_EFFECTIVE  → Processed by effective date task
EFFECTIVE                   → Normal operation
SCHEDULED_FOR_OBSOLESCENCE  → Processed by obsoletion task  
OBSOLETE                    → Terminal state
```

**Critical Fields:**
- `effective_date` - Date for automatic activation
- `obsolescence_date` - Date for automatic obsoletion
- `obsolescence_reason` - Why document became obsolete
- `status` - Current lifecycle state

### 5.2 Workflow Model Integration

**Workflow States Affected:**
```
DocumentWorkflow.current_state → Updated by scheduler
DocumentWorkflow.is_terminated → Set True for obsolete documents
DocumentTransition → Created for each automated transition
```

**Timeout Monitoring:**
- Checks `DocumentWorkflow.due_date` vs current date
- Monitors only active workflows (`is_terminated=False`)
- Excludes final states (`current_state.is_final=False`)

### 5.3 Audit Trail Integration

**Automated Actions Recorded:**
```
DOC_EFFECTIVE_PROCESSED  - Document became effective
DOC_OBSOLETED           - Document became obsolete  
SYSTEM_HEALTH_CHECK     - Health monitoring ran
```

**Audit Metadata:**
- User: `system_scheduler` (automated user)
- IP: `127.0.0.1`
- User Agent: `'EDMS Scheduler Service'` or `'EDMS Health Monitor'`
- Field Changes: JSON with old/new values and timestamps

### 5.4 Notification Service Integration

**Email Notifications Sent:**
1. **Document Effective** - To document author when activated
2. **Document Obsolete** - To document author when obsoleted
3. **Workflow Timeout** - To assigned user for overdue workflows (>7 days)

**Configuration:**
- Uses Django's `send_mail()` with `settings.DEFAULT_FROM_EMAIL`
- Fails silently with logging (doesn't break task execution)

---

## 6. Monitoring & Manual Triggering

### 6.1 Monitoring Dashboard

Location: `backend/apps/scheduler/monitoring_dashboard.py`

**Features:**
- View all scheduled tasks with next run times
- See task execution history and results
- Manual trigger buttons for each task
- Real-time status display

**URL Patterns:**
- Dashboard view: `/scheduler/dashboard/`
- Manual trigger: `/scheduler/trigger/<task_name>/`

### 6.2 API Endpoints

Location: `backend/apps/scheduler/api_views.py`

**Available Endpoints:**
```
GET /api/v1/notifications/recent/     - Recent notifications
GET /api/v1/notifications/my_tasks/   - User's pending tasks
GET /api/v1/scheduler/status/         - Scheduler status
POST /api/v1/scheduler/trigger/<task>/ - Manual trigger
```

### 6.3 Task Execution Results

**Result Schema:**
```python
{
    'processed_count': int,      # Documents examined
    'success_count': int,        # Successfully processed
    'error_count': int,          # Errors encountered
    'processed_documents': [],   # Detailed list
    'errors': [],                # Error messages
    'timestamp': ISO datetime
}
```

---

## 7. Recent Changes & Git History

### 7.1 Recent Commits (Last 30)

**Document Management:**
- `8b0bef2` - Clean up document management interface
- `c900592` - Fix dependency field name in upversion copying
- `4d2f0dd` - Implement complete upversioning with family grouping

**Scheduler Improvements:**
- `358f3c0` - Implement stat cards and integrated scheduler dashboard
- `9e67a76` - Add console logging for dashboard debugging
- `090ce0a` - Comprehensive scheduler refactoring and manual trigger fixes
- `68df358` - Add task detail modal and manual trigger functionality

**Admin Dashboard:**
- `afb067d` - Add recent_activity to dashboard stats API
- `91cdbbf` - Improve admin activity display with action mappings
- `e83d05e` - Add Backup Management to Quick Actions

**Audit Trail:**
- `6f98d05` - Implement CSV and PDF export for Audit Trail
- `ff44b98` - Add pagination controls to Audit Trail

### 7.2 Architecture Decisions

From AGENTS.md workspace memory:

**Status Consolidation:**
- Scheduler expects `EFFECTIVE` status (not `APPROVED_AND_EFFECTIVE`)
- System migrated from dual-status to single standardized status
- Lesson: Check automated systems before standardizing statuses

**WorkflowTask Removal:**
- Removed `WorkflowTask` model in favor of document filtering
- `cleanup_workflow_tasks()` now a no-op for backward compatibility
- Simplified architecture reduces maintenance overhead

**Timezone Strategy:**
- Storage: Always UTC in database
- Display: Dual timezone (UTC + local SGT)
- Scheduler: Uses UTC for all date comparisons
- Effective dates processed at midnight UTC (8 AM SGT)

---

## 8. Error Handling & Reliability

### 8.1 Retry Mechanisms

**Task Retry Configuration:**
```python
@shared_task(bind=True, max_retries=3)
def process_document_effective_dates(self):
    try:
        # ... processing logic
    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise
```

**Retry Pattern:**
- Max retries: 3
- Exponential backoff: 60s, 120s, 180s
- Only document lifecycle tasks use retries
- Monitoring tasks fail immediately

### 8.2 Transaction Safety

**Atomic Operations:**
```python
with transaction.atomic():
    # Update document
    # Update workflow  
    # Create audit trail
    # All or nothing
```

**Benefits:**
- Prevents partial state updates
- Ensures data consistency
- Rollback on any error

### 8.3 Failure Handling

**Graceful Degradation:**
1. Document processing continues even if notifications fail
2. Workflow update failure logs warning but continues
3. Audit trail creation is best-effort
4. Task reports detailed errors without crashing

**Logging Strategy:**
```python
logger.info()   # Successful operations
logger.warning()  # Non-critical failures (notifications)
logger.error()    # Critical failures requiring attention
```

---

## 9. System User Pattern

### 9.1 Automated User Attribution

**System User Creation:**
```python
system_user, created = User.objects.get_or_create(
    username='system_scheduler',
    defaults={
        'email': 'system@edms.local',
        'first_name': 'System',
        'last_name': 'Scheduler',
        'is_active': True,
        'is_staff': False
    }
)
```

**Usage:**
- All automated actions attributed to `system_scheduler`
- Distinguishes automated vs manual actions in audit trail
- Fallback to first superuser if system user doesn't exist

**Lazy Initialization:**
```python
@property
def system_user(self):
    """Avoid database connection at import time"""
    if self._system_user is None:
        self._system_user = self._get_system_user()
    return self._system_user
```

---

## 10. Performance Considerations

### 10.1 Query Optimization

**Filtered Queries:**
```python
# Efficient: Only fetches candidates
Document.objects.filter(
    status='APPROVED_PENDING_EFFECTIVE',
    effective_date__lte=timezone.now().date(),
    is_active=True
)
```

**Select Related:**
```python
# Reduces N+1 queries
DocumentWorkflow.objects.filter(...).select_related('document')
```

### 10.2 Task Expiration

**Prevents Queue Buildup:**
```python
'options': {
    'expires': 3600,  # Task expires after 1 hour
}
```

If Celery Beat misses a scheduled run (server down), expired tasks won't pile up.

### 10.3 Queue Distribution

**5 Separate Queues:**
- `celery` - Default queue
- `scheduler` - Scheduler tasks
- `documents` - Document processing
- `workflows` - Workflow tasks
- `maintenance` - Cleanup and health checks

**Benefits:**
- Priority separation
- Resource isolation
- Independent scaling

---

## 11. Testing

### 11.1 Test Files

Location: `backend/apps/scheduler/tests/`

**Test Coverage:**
- `test_document_activation.py` - Effective date processing
- `test_obsolescence_automation.py` - Obsoletion processing

**Test Strategy:**
```python
CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in tests
CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions
```

### 11.2 Manual Testing

**Via Django Shell:**
```python
from apps.scheduler.tasks import process_document_effective_dates

# Execute task synchronously
result = process_document_effective_dates.apply()
print(result.get())
```

**Via Monitoring Dashboard:**
- Navigate to `/scheduler/dashboard/`
- Click "Trigger Now" button for any task
- View execution results in real-time

---

## 12. Deployment Considerations

### 12.1 Docker Container Requirements

**Critical Pattern:** Python code changes require image rebuild

```bash
# ❌ WRONG - Won't load new code
git pull
docker compose restart backend celery_worker celery_beat

# ✅ CORRECT - Rebuilds with new code
git pull
docker compose build backend celery_worker celery_beat
docker compose up -d
```

**Reason:** Containers run from images (snapshots), not live code on disk

### 12.2 Service Dependencies

**Startup Order:**
```yaml
backend:
  depends_on: [db, redis]
  command: sh -c "sleep 10 && python manage.py migrate && ..."

celery_worker:
  depends_on: [db, redis]
  command: sh -c "sleep 15 && celery -A edms worker ..."

celery_beat:
  depends_on: [db, redis]
  command: sh -c "sleep 20 && celery -A edms beat ..."
```

**Sleep Delays:**
- Backend: 10s (wait for DB)
- Worker: 15s (wait for migrations)
- Beat: 20s (wait for worker)

### 12.3 Health Checks

**Celery Worker:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "celery -A edms inspect ping"]
```

**Celery Beat:**
```yaml
healthcheck:
  disable: true  # Beat doesn't respond to ping
```

**Key Insight:** Beat can be "unhealthy" but still function correctly

---

## 13. Future Enhancements

### 13.1 Disabled Features

**Notification Queue Processing:**
```python
# Currently disabled in celery.py (lines 72-79)
# 'process-notification-queue': {
#     'task': 'apps.scheduler.notification_service.process_notification_queue',
#     'schedule': crontab(minute='*/5'),
# },
```

**Reason:** NotificationQueue model removed, direct notifications used instead

### 13.2 Backup System

**Currently Handled Externally:**
```python
# Note: Backup tasks removed - handled by host-level cron jobs
# See: crontab -l for active backup schedule
```

**Location:** `/backend/apps/core/tasks.py` has backup functionality

---

## 14. Key Takeaways

### 14.1 Architecture Strengths

✅ **Service Layer Pattern** - Clean separation of concerns  
✅ **Transaction Safety** - Atomic operations prevent corruption  
✅ **Comprehensive Audit** - All automated actions tracked  
✅ **Graceful Degradation** - Notification failures don't break processing  
✅ **Queue Distribution** - Multiple queues for priority management  

### 14.2 Common Pitfalls (from AGENTS.md)

❌ **Docker Rebuild Required** - Code changes need image rebuild, not just restart  
❌ **Timezone Assumptions** - Always use UTC for scheduler logic  
❌ **Status Naming** - Check what scheduler expects before changing status names  
❌ **Health Check Status** - "Unhealthy" doesn't always mean broken  

### 14.3 Best Practices

1. **Always use UTC** for date comparisons in scheduler logic
2. **Attribute to system_scheduler** user for audit trail clarity
3. **Wrap in transaction.atomic()** for multi-model updates
4. **Log at appropriate levels** (info/warning/error)
5. **Return detailed results** for monitoring dashboard
6. **Use lazy initialization** for system user to avoid import-time DB connections

---

## 15. Quick Reference

### 15.1 Task Schedule Summary

| Task | Frequency | Next Run Pattern |
|------|-----------|------------------|
| Effective Date Processing | Hourly | XX:00 |
| Obsoletion Processing | Hourly | XX:15 |
| Workflow Timeouts | Every 4 hours | 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 |
| System Health Check | Every 30 min | XX:00, XX:30 |
| Celery Cleanup | Daily | 03:00 |

### 15.2 Important File Locations

```
backend/apps/scheduler/
├── tasks.py                    # Celery task definitions
├── services/
│   ├── automation.py          # Document lifecycle logic
│   ├── health.py              # Health monitoring
│   └── cleanup.py             # Celery results cleanup
├── api_views.py               # REST API endpoints
├── monitoring_dashboard.py    # Django monitoring views
├── notification_service.py    # Email notifications
└── celery_schedule.py         # Beat schedule config

backend/edms/celery.py         # Main Celery configuration
docker-compose.yml             # Container orchestration
```

### 15.3 Database Models Referenced

- `Document` - Document records with status and dates
- `DocumentWorkflow` - Workflow state and assignments
- `DocumentState` - Workflow state definitions
- `DocumentTransition` - Workflow state change history
- `AuditTrail` - Comprehensive audit logging
- `User` - User accounts including system_scheduler
- `TaskResult` - Celery task execution results

---

**End of Analysis**

For questions or clarifications, refer to:
- Git history: `git log --oneline -30`
- Workspace memory: `AGENTS.md`
- Recent documentation: `SCHEDULER_*.md` files
