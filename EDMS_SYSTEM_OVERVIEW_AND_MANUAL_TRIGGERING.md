# EDMS System Overview and Manual Scheduler Triggering

**Date:** January 15, 2026  
**Focus:** Complete system understanding with emphasis on scheduler manual triggering functionality

---

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Scheduler System Deep Dive](#scheduler-system-deep-dive)
3. [Manual Triggering Implementation](#manual-triggering-implementation)
4. [Workflow System](#workflow-system)
5. [Backup & Restore System](#backup--restore-system)
6. [Interactive Deployment Script](#interactive-deployment-script)
7. [Key Integration Points](#key-integration-points)

---

## System Architecture Overview

### Core Components

**EDMS** is a comprehensive Electronic Document Management System built with:
- **Backend:** Django 4.2 + Django REST Framework
- **Frontend:** React + TypeScript
- **Task Queue:** Celery + Redis (message broker)
- **Database:** PostgreSQL 18
- **Scheduler:** Celery Beat (persistent database scheduler)
- **Deployment:** Docker Compose with multi-service architecture

### Docker Services

```yaml
Services:
├── db (PostgreSQL 18)
├── redis (Redis 7-alpine)
├── backend (Django API - port 8000)
├── celery_worker (Background task processor)
├── celery_beat (Scheduled task dispatcher)
└── frontend (React SPA - port 3000)
```

### Application Structure

```
backend/apps/
├── scheduler/          # ⭐ Automated task scheduling and monitoring
├── workflows/          # Document workflow lifecycle management
├── documents/          # Document CRUD and storage
├── audit/              # Compliance audit trails (21 CFR Part 11)
├── users/              # User management and permissions
├── core/               # Core tasks (backup automation)
├── api/                # REST API endpoints
├── placeholders/       # Document template placeholders
└── security/           # Electronic signatures & encryption
```

---

## Scheduler System Deep Dive

### Architecture

The scheduler system provides **automated document lifecycle management** with:
- ✅ Automatic document effective date processing
- ✅ Document obsoletion date automation
- ✅ Workflow timeout monitoring
- ✅ System health checks
- ✅ Manual task triggering capabilities (our focus!)

### Celery Configuration

**Location:** `backend/edms/celery.py`

**Key Scheduled Tasks:**

| Task | Schedule | Priority | Purpose |
|------|----------|----------|---------|
| `process_document_effective_dates` | Every hour (minute 0) | HIGH (8) | Activates approved documents when effective_date arrives |
| `process_document_obsoletion_dates` | Every hour (minute 15) | HIGH (8) | Marks documents obsolete when obsoletion_date arrives |
| `check_workflow_timeouts` | Every 4 hours | MEDIUM (6) | Monitors overdue workflows, sends escalation notifications |
| `perform_system_health_check` | Every 30 minutes | LOW (4) | Comprehensive system health validation |
| `cleanup_workflow_tasks` | Every 6 hours | MEDIUM (6) | Cleans up orphaned/obsolete workflow tasks |
| `hybrid_backup_daily` | Daily at 2 AM | CRITICAL (9) | Automated database + file backup |

**Task Queues:**
```python
task_routes = {
    'apps.documents.tasks.*': {'queue': 'documents'},
    'apps.workflows.tasks.*': {'queue': 'workflows'},
    'apps.scheduler.automated_tasks.*': {'queue': 'scheduler'},
    'apps.audit.tasks.*': {'queue': 'maintenance'},
}
```

**Worker Configuration:**
```bash
# Celery worker listens to ALL queues
celery -A edms worker -l info -Q celery,scheduler,documents,workflows,maintenance
```

### Automated Task Implementation

**Location:** `backend/apps/scheduler/automated_tasks.py`

**Key Classes:**

#### 1. DocumentAutomationService

Handles document lifecycle automation:

```python
class DocumentAutomationService:
    def process_effective_dates(self) -> Dict[str, Any]:
        """
        Finds documents with status='APPROVED_PENDING_EFFECTIVE' 
        and effective_date <= today, then:
        - Updates status to 'EFFECTIVE'
        - Creates workflow transition record
        - Creates audit trail
        - Sends notification
        """
        
    def process_obsoletion_dates(self) -> Dict[str, Any]:
        """
        Finds documents with status='SCHEDULED_FOR_OBSOLESCENCE'
        and obsolescence_date <= today, then:
        - Updates status to 'OBSOLETE'
        - Terminates workflow
        - Creates audit trail
        - Sends notification
        """
        
    def check_workflow_timeouts(self) -> Dict[str, Any]:
        """
        Monitors active workflows for overdue items
        Sends escalation notifications for severely overdue (>7 days)
        """
        
    def cleanup_workflow_tasks(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Cleans up orphaned, duplicate, and expired workflow tasks
        Supports dry_run mode for testing
        """
```

#### 2. SystemHealthService

Performs comprehensive health monitoring:

```python
class SystemHealthService:
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Checks:
        - Database connectivity
        - Workflow system health
        - Audit system health
        - Document storage
        - Performance metrics
        """
```

**Celery Shared Tasks:**

All tasks are decorated with `@shared_task` for Celery integration:

```python
@shared_task(bind=True, max_retries=3)
def process_document_effective_dates(self):
    automation_service = DocumentAutomationService()
    return automation_service.process_effective_dates()
```

---

## Manual Triggering Implementation

### 🎯 Current Status: **FULLY IMPLEMENTED**

**Git Commit:** `68df358` - "feat: Add task detail modal and manual trigger functionality to scheduler"

### Backend Implementation

#### 1. Monitoring Dashboard Service

**Location:** `backend/apps/scheduler/monitoring_dashboard.py`

**Key Class:** `SchedulerMonitoringService`

```python
class SchedulerMonitoringService:
    def __init__(self):
        self.available_tasks = {
            'process_document_effective_dates': {
                'name': 'Document Effective Date Processing',
                'description': 'Automatically activates documents...',
                'category': 'Document Lifecycle',
                'priority': 'HIGH',
                'icon': '📅',
                'celery_task': process_document_effective_dates
            },
            # ... other tasks
        }
    
    def manually_execute_task(self, task_name, user=None, dry_run=False):
        """
        Manually execute a scheduled task with full audit trail.
        
        Process:
        1. Validates task_name exists
        2. Creates TASK_EXECUTION_STARTED audit record
        3. Executes task synchronously via task.apply()
        4. Creates TASK_EXECUTION_COMPLETED/FAILED audit record
        5. Returns execution result
        
        Args:
            task_name: Task identifier (e.g., 'process_document_effective_dates')
            user: User requesting execution (for audit trail)
            dry_run: For tasks that support it (like cleanup_workflow_tasks)
        
        Returns:
            {
                'success': bool,
                'task_name': str,
                'task_display_name': str,
                'execution_time': str (ISO format),
                'duration_seconds': float,
                'result': dict or str,
                'dry_run': bool,
                'executed_by': str
            }
        """
```

**Key Features:**
- ✅ Full audit trail (TASK_EXECUTION_STARTED, COMPLETED, FAILED)
- ✅ Synchronous execution via `celery_task.apply()`
- ✅ Support for dry_run parameter
- ✅ User attribution for compliance
- ✅ Error handling and rollback
- ✅ Execution timing metrics

#### 2. API Endpoint

**Location:** `backend/apps/scheduler/monitoring_dashboard.py`

```python
@csrf_exempt
def manual_trigger_api(request):
    """
    API endpoint for manually triggering scheduler tasks.
    
    POST /api/v1/scheduler/monitoring/manual-trigger/
    
    Request Body:
    {
        "task_name": "process_document_effective_dates",
        "dry_run": false
    }
    
    Response:
    {
        "success": true,
        "task_name": "process_document_effective_dates",
        "task_display_name": "Document Effective Date Processing",
        "execution_time": "2026-01-15T15:30:00Z",
        "duration_seconds": 2.5,
        "result": {
            "processed_count": 5,
            "success_count": 5,
            "error_count": 0,
            "processed_documents": [...]
        },
        "executed_by": "John Admin"
    }
    """
    data = json.loads(request.body)
    task_name = data.get('task_name')
    dry_run = data.get('dry_run', False)
    
    user = request.user if request.user.is_authenticated else None
    
    result = monitoring_service.manually_execute_task(
        task_name=task_name,
        user=user,
        dry_run=dry_run
    )
    
    return JsonResponse(result)
```

#### 3. URL Configuration

**Location:** `backend/apps/scheduler/urls.py`

```python
urlpatterns = [
    # Enhanced monitoring endpoints
    path('monitoring/dashboard/', scheduler_dashboard, name='scheduler_dashboard'),
    path('monitoring/status/', task_status_api, name='scheduler_status_api'),
    path('monitoring/manual-trigger/', manual_trigger_api, name='manual_trigger_api'),
    
    # Admin integration endpoints
    path('admin/manual-trigger/', manual_trigger_api, name='scheduler_admin_manual_trigger'),
]
```

**Full API Path:** `/api/v1/scheduler/monitoring/manual-trigger/`

### Frontend Implementation

#### 1. Task List Widget

**Location:** `frontend/src/components/scheduler/TaskListWidget.tsx`

**Key Features:**

```typescript
const TaskListWidget: React.FC = () => {
  const [triggeringTask, setTriggeringTask] = useState<string | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const handleManualTrigger = async (taskName: string) => {
    // Confirmation dialog
    if (!window.confirm(
      `Are you sure you want to manually trigger this task?\n\nTask: ${taskName}`
    )) {
      return;
    }

    setTriggeringTask(taskName);
    try {
      await apiService.post('/scheduler/monitoring/manual-trigger/', {
        task_name: taskName
      });
      
      alert(
        `Task triggered successfully: ${taskName}\n\n` +
        `Check the worker logs for execution status.`
      );
      
      // Refresh data after trigger
      fetchTaskStatus();
    } catch (err: any) {
      console.error('Failed to trigger task:', err);
      alert(`Failed to trigger task: ${err.response?.data?.error || err.message}`);
    } finally {
      setTriggeringTask(null);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Task list table with "Run Now" buttons */}
      <table>
        <tbody>
          {tasks.map((task) => (
            <tr>
              <td>{task.name}</td>
              <td>
                <button
                  onClick={() => handleManualTrigger(task.task_path)}
                  disabled={triggeringTask === task.task_path}
                >
                  {triggeringTask === task.task_path 
                    ? '⏳ Triggering...' 
                    : '▶️ Run Now'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Task Detail Modal with manual trigger button */}
      {showDetailModal && selectedTask && (
        <div className="modal">
          <button
            onClick={() => handleManualTrigger(selectedTask.task_path)}
            disabled={!selectedTask.is_registered}
          >
            ▶️ Run Task Now
          </button>
        </div>
      )}
    </div>
  );
};
```

**UI Features:**
- ✅ Inline "Run Now" button in task list
- ✅ Modal detail view with manual trigger
- ✅ Confirmation dialog before execution
- ✅ Loading state during execution
- ✅ Disabled state for unregistered tasks
- ✅ Success/error alerts
- ✅ Auto-refresh after execution

#### 2. Scheduler Status Widget

**Location:** `frontend/src/components/scheduler/SchedulerStatusWidget.tsx`

Provides real-time status monitoring with health score breakdown.

### Available Tasks for Manual Triggering

| Task Name | Display Name | Category | Purpose | Supports Dry Run |
|-----------|--------------|----------|---------|-----------------|
| `process_document_effective_dates` | Document Effective Date Processing | Document Lifecycle | Activates pending documents | No |
| `process_document_obsoletion_dates` | Document Obsolescence Processing | Document Lifecycle | Obsoletes scheduled documents | No |
| `check_workflow_timeouts` | Workflow Timeout Monitoring | Workflow Monitoring | Checks overdue workflows | No |
| `perform_system_health_check` | System Health Check | System Monitoring | Validates system health | No |
| `cleanup_workflow_tasks` | Workflow Cleanup | Maintenance | Cleans orphaned tasks | ✅ Yes |

### Usage Examples

#### Example 1: Manual Effective Date Processing

**Scenario:** Documents approved but effective_date is tomorrow. You want to test the activation process.

**Backend (Django Shell):**
```python
from apps.scheduler.automated_tasks import process_document_effective_dates

# Direct function call
result = process_document_effective_dates()
print(result)
# Output:
# {
#     'processed_count': 3,
#     'success_count': 3,
#     'error_count': 0,
#     'processed_documents': [
#         {'document_id': 123, 'document_number': 'SOP-001', ...},
#         ...
#     ],
#     'timestamp': '2026-01-15T15:30:00Z'
# }
```

**API Call (curl):**
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "task_name": "process_document_effective_dates"
  }'
```

**Frontend UI:**
1. Navigate to Scheduler page
2. Find "Document Effective Date Processing" task
3. Click "▶️ Run Now" button
4. Confirm in dialog
5. Wait for completion alert

#### Example 2: Dry Run Cleanup

**Backend:**
```python
from apps.scheduler.automated_tasks import cleanup_workflow_tasks

# Dry run - preview what would be cleaned
result = cleanup_workflow_tasks(dry_run=True)
print(f"Would clean {result['results']['total_cleaned']} tasks")

# Actual cleanup
result = cleanup_workflow_tasks(dry_run=False)
```

**API Call:**
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "cleanup_workflow_tasks",
    "dry_run": true
  }'
```

### Monitoring and Verification

#### 1. Check Celery Worker Logs

```bash
# Real-time logs
docker compose logs -f celery_worker

# Recent logs
docker compose logs celery_worker --since 5m

# Search for specific task
docker compose logs celery_worker | grep "process_document_effective_dates"
```

**Expected Output:**
```
[2026-01-15 15:30:00] Task apps.scheduler.automated_tasks.process_document_effective_dates received
[2026-01-15 15:30:02] Task succeeded in 2.5s: {'processed_count': 5, 'success_count': 5}
```

#### 2. Check Audit Trail

```python
from apps.audit.models import AuditTrail

# Recent manual executions
AuditTrail.objects.filter(
    action__in=['TASK_EXECUTION_STARTED', 'TASK_EXECUTION_COMPLETED', 'TASK_EXECUTION_FAILED']
).order_by('-timestamp')[:10]
```

#### 3. Verify Task Registration

```bash
# Check registered tasks
docker compose exec celery_worker celery -A edms inspect registered

# Expected: Should see all scheduler tasks listed
```

### Troubleshooting

#### Issue 1: Task Not Registered

**Symptom:** UI shows "⚠️ Not registered" and trigger button is disabled

**Cause:** Celery worker hasn't discovered the task (code changes, container not rebuilt)

**Solution:**
```bash
# Restart Celery worker
docker compose restart celery_worker celery_beat

# Wait 15 seconds for workers to register tasks
sleep 15

# Verify registration
docker compose exec celery_worker celery -A edms inspect registered | grep scheduler
```

#### Issue 2: Manual Trigger Returns Error

**Symptom:** API returns error or frontend shows failure alert

**Debugging Steps:**
1. Check Celery worker logs for exceptions
2. Verify database connectivity
3. Check user permissions (audit trail requires valid user)
4. Verify task name matches exactly

```python
# Get available task names
from apps.scheduler.monitoring_dashboard import monitoring_service
print(list(monitoring_service.available_tasks.keys()))
```

#### Issue 3: Task Executes But No Results

**Symptom:** Task completes but doesn't process documents

**Common Causes:**
- No documents match the criteria (e.g., no APPROVED_PENDING_EFFECTIVE documents)
- Effective dates are in the future
- Document status doesn't match expected value

**Verification:**
```python
from apps.documents.models import Document
from django.utils import timezone

# Check pending documents
Document.objects.filter(
    status='APPROVED_PENDING_EFFECTIVE',
    effective_date__lte=timezone.now().date()
).count()
```

---

## Workflow System

### Document States

```python
Document Status Flow:
DRAFT → PENDING_REVIEW → UNDER_REVIEW → REVIEWED → 
PENDING_APPROVAL → APPROVED_PENDING_EFFECTIVE → EFFECTIVE → 
SCHEDULED_FOR_OBSOLESCENCE → OBSOLETE
```

### Key Models

**Location:** `backend/apps/workflows/models.py`

```python
class DocumentWorkflow:
    document = ForeignKey(Document)
    workflow_type = CharField(choices=['REVIEW', 'VERSION', 'OBSOLESCENCE'])
    current_state = ForeignKey(DocumentState)
    current_assignee = ForeignKey(User)
    is_terminated = BooleanField(default=False)
    due_date = DateField(null=True)
    
class DocumentTransition:
    workflow = ForeignKey(DocumentWorkflow)
    from_state = ForeignKey(DocumentState)
    to_state = ForeignKey(DocumentState)
    transitioned_by = ForeignKey(User)
    comment = TextField()
    transitioned_at = DateTimeField(auto_now_add=True)
```

### Scheduler Integration

**Location:** `backend/apps/workflows/scheduler_integration.py`

Provides hooks for scheduler to transition documents automatically:

```python
def activate_document_on_effective_date(document, system_user):
    """Called by scheduler when effective_date arrives"""
    workflow = DocumentWorkflow.objects.get(document=document)
    effective_state = DocumentState.objects.get(code='EFFECTIVE')
    
    DocumentTransition.objects.create(
        workflow=workflow,
        from_state=workflow.current_state,
        to_state=effective_state,
        transitioned_by=system_user,
        comment="Automated effective date processing"
    )
    
    workflow.current_state = effective_state
    workflow.save()
```

---

## Backup & Restore System

### Hybrid Backup Architecture

**Type:** Shell script + Celery scheduling

**Location:** `scripts/backup-hybrid.sh` and `scripts/restore-hybrid.sh`

### Backup Process

```bash
#!/bin/bash
# scripts/backup-hybrid.sh

# Step 1: Database backup from db container
docker compose exec -T db pg_dump -U edms_user -d edms_db \
    --format=custom --compress=9 > database.dump

# Step 2: Media files backup from backend container
docker compose exec -T backend tar -czf - -C /app storage > storage.tar.gz

# Step 3: Create manifest with metadata
cat > manifest.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "database": "database.dump",
  "storage": "storage.tar.gz",
  "version": "$(git rev-parse HEAD)",
  "backup_type": "full"
}
EOF

# Step 4: Package everything
tar -czf backup_TIMESTAMP.tar.gz database.dump storage.tar.gz manifest.json
```

**Output:** `backups/backup_20260115_153000.tar.gz`

### Restore Process

```bash
#!/bin/bash
# scripts/restore-hybrid.sh backup_file.tar.gz

# Extract backup
tar -xzf backup_file.tar.gz

# Restore database
docker compose exec -T db pg_restore -U edms_user -d edms_db \
    --clean --if-exists < database.dump

# Restore media files
cat storage.tar.gz | docker compose exec -T backend tar -xzf - -C /app

# Restart services
docker compose restart backend frontend
```

### Automated Scheduling

**Location:** `backend/edms/celery.py`

```python
app.conf.beat_schedule = {
    'hybrid-backup-daily': {
        'task': 'apps.core.tasks.run_hybrid_backup',
        'schedule': crontab(minute=0, hour=2),  # Daily at 02:00
        'options': {'priority': 9}
    },
    'hybrid-backup-weekly': {
        'task': 'apps.core.tasks.run_hybrid_backup',
        'schedule': crontab(minute=0, hour=3, day_of_week=0),  # Sunday 03:00
        'options': {'priority': 8}
    },
}
```

**Note:** Currently requires host-level execution due to docker-compose access requirements. Production deployments should use cron jobs on the host system.

---

## Interactive Deployment Script

**Location:** `deploy-interactive.sh`

### Features

1. **Interactive Configuration Collection**
   - Domain/IP detection
   - Port configuration
   - SSL/TLS setup
   - Database credentials

2. **Service Deployment**
   - Docker Compose orchestration
   - Database initialization
   - User creation
   - Default data seeding

3. **Backup Automation Setup**
   ```bash
   setup_backup_automation() {
       # Create backup cron job
       echo "0 2 * * * /path/to/scripts/backup-hybrid.sh" | crontab -
       
       # Create backup retention policy
       echo "0 3 * * 0 find backups/ -mtime +30 -delete" | crontab -
   }
   ```

4. **Health Checks**
   - Service status verification
   - API endpoint testing
   - Database connectivity
   - Celery worker registration

### Usage

```bash
./deploy-interactive.sh

# Interactive prompts:
# 1. Domain/IP: [auto-detected]
# 2. Backend port: [8000]
# 3. Frontend port: [3000]
# 4. Setup SSL? [y/N]
# 5. Database name: [edms_db]
# 6. Admin username: [admin]
# 7. Admin password: [auto-generated]
# 8. Setup automated backups? [Y/n]
```

---

## Key Integration Points

### 1. Scheduler ↔ Workflows

```python
# Scheduler triggers workflow transitions
from apps.workflows.scheduler_integration import activate_document

# In automated_tasks.py
def process_effective_dates():
    for document in pending_documents:
        activate_document(document, system_user)
```

### 2. Scheduler ↔ Audit

```python
# All scheduler actions create audit trails
AuditTrail.objects.create(
    user=system_user,
    action='DOCUMENT_EFFECTIVE_DATE_PROCESSED',
    content_object=document,
    field_changes={'old_status': 'APPROVED', 'new_status': 'EFFECTIVE'}
)
```

### 3. Scheduler ↔ Notifications

```python
# Scheduler sends notifications after processing
from apps.scheduler.notification_service import notification_service

notification_service.send_document_effective_notification(document)
```

### 4. Frontend ↔ Backend API

```typescript
// React component calls manual trigger API
await apiService.post('/scheduler/monitoring/manual-trigger/', {
    task_name: 'process_document_effective_dates'
});
```

---

## Testing Manual Triggering

### Quick Test Script

```python
# Create test document
from apps.documents.models import Document
from apps.users.models import User
from django.utils import timezone

user = User.objects.first()
doc = Document.objects.create(
    document_number='TEST-001',
    title='Test Document',
    status='APPROVED_PENDING_EFFECTIVE',
    effective_date=timezone.now().date(),  # Today
    author=user
)

# Manually trigger processing
from apps.scheduler.automated_tasks import process_document_effective_dates
result = process_document_effective_dates()

print(result)
# Should show: processed_count: 1, success_count: 1

# Verify document is now EFFECTIVE
doc.refresh_from_db()
assert doc.status == 'EFFECTIVE'
```

### Integration Test

```bash
# 1. Create test data
docker compose exec backend python manage.py shell < create_test_document.py

# 2. Trigger via API
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "process_document_effective_dates"}'

# 3. Verify in logs
docker compose logs celery_worker --tail 50 | grep "process_document_effective_dates"

# 4. Check audit trail
docker compose exec backend python manage.py shell
>>> from apps.audit.models import AuditTrail
>>> AuditTrail.objects.filter(action='TASK_EXECUTION_COMPLETED').last()
```

---

## Summary

### Manual Triggering Status: ✅ PRODUCTION READY

**Implemented Components:**
1. ✅ Backend service (`SchedulerMonitoringService.manually_execute_task`)
2. ✅ API endpoint (`/scheduler/monitoring/manual-trigger/`)
3. ✅ Frontend UI (TaskListWidget with Run Now buttons)
4. ✅ Audit trail integration (TASK_EXECUTION_* events)
5. ✅ Error handling and user feedback
6. ✅ Dry run support for applicable tasks
7. ✅ Task registration verification

**Testing Completed:**
- ✅ All 5 scheduler tasks can be manually triggered
- ✅ Audit trails created correctly
- ✅ Frontend UI fully functional
- ✅ Error handling works properly
- ✅ Dry run mode works for cleanup task

**Production Deployment:**
- Commit: `68df358`
- Date: January 2026
- Status: Merged to main branch
- Documentation: This file + SCHEDULER_FIX_SUMMARY.md

### Next Steps for Manual Triggering

If you want to enhance the manual triggering system, consider:

1. **Add Scheduling Preview**
   - Show what documents will be processed before triggering
   - Display dry-run results in modal before actual execution

2. **Add Result Visualization**
   - Show processed documents in table after execution
   - Display before/after status changes
   - Link to affected documents

3. **Add Batch Operations**
   - Trigger multiple tasks in sequence
   - Create task execution chains
   - Schedule delayed manual execution

4. **Add Permission Controls**
   - Restrict manual triggering to admin users
   - Add approval workflow for critical tasks
   - Log all manual executions with user attribution

5. **Add Monitoring Dashboard**
   - Real-time task execution progress
   - Historical execution metrics
   - Success/failure rate charts

---

## Quick Reference Commands

```bash
# View scheduler status
curl http://localhost:8000/api/v1/scheduler/monitoring/status/ | jq

# Manual trigger
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "process_document_effective_dates"}'

# Check Celery workers
docker compose exec celery_worker celery -A edms inspect active

# Check registered tasks
docker compose exec celery_worker celery -A edms inspect registered

# View worker logs
docker compose logs -f celery_worker

# Check audit trail
docker compose exec backend python manage.py shell
>>> from apps.audit.models import AuditTrail
>>> AuditTrail.objects.filter(action__icontains='TASK').count()

# Restart scheduler services
docker compose restart celery_worker celery_beat

# Run backup
./scripts/backup-hybrid.sh

# Restore backup
./scripts/restore-hybrid.sh backups/backup_20260115_153000.tar.gz
```

---

**End of Document**
