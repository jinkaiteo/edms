# EDMS Scheduler System - Architecture Diagrams

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EDMS APPLICATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Frontend   │◄────►│   Backend    │◄────►│  PostgreSQL  │ │
│  │  React:3000  │      │ Django:8000  │      │   Database   │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│                               │                                 │
│                               │                                 │
│                               ▼                                 │
│                        ┌─────────────┐                          │
│                        │    Redis    │                          │
│                        │   :6379     │                          │
│                        └─────────────┘                          │
│                               │                                 │
│                     ┌─────────┴─────────┐                       │
│                     │                   │                       │
│                     ▼                   ▼                       │
│            ┌─────────────────┐  ┌──────────────┐               │
│            │  Celery Worker  │  │ Celery Beat  │               │
│            │   (Executor)    │  │ (Scheduler)  │               │
│            └─────────────────┘  └──────────────┘               │
│                     │                   │                       │
│                     └─────────┬─────────┘                       │
│                               │                                 │
│                               ▼                                 │
│                    ┌────────────────────┐                       │
│                    │  Scheduler Module  │                       │
│                    │  apps/scheduler/   │                       │
│                    └────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Scheduler Module Internal Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    apps/scheduler/ Module                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  tasks.py (Celery Tasks)                      │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │ │
│  │  │   Effective    │  │   Obsoletion   │  │    Workflow    │ │ │
│  │  │  Date Process  │  │  Date Process  │  │    Timeouts    │ │ │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘ │ │
│  │          │                   │                   │           │ │
│  └──────────┼───────────────────┼───────────────────┼───────────┘ │
│             │                   │                   │              │
│             ▼                   ▼                   ▼              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              services/ (Business Logic Layer)                 │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  automation.py - DocumentAutomationService              │ │ │
│  │  │  • process_effective_dates()                            │ │ │
│  │  │  • process_obsoletion_dates()                           │ │ │
│  │  │  • check_workflow_timeouts()                            │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  health.py - SystemHealthService                        │ │ │
│  │  │  • perform_health_check()                               │ │ │
│  │  │  • _check_database(), _check_workflows(), etc.          │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  cleanup.py - CeleryResultsCleanupService               │ │ │
│  │  │  • cleanup(days_to_keep=7)                              │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
│             │                   │                   │              │
│             ▼                   ▼                   ▼              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │         Integration Layer (Models & Services)                 │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │ │
│  │  │ Documents  │  │ Workflows  │  │   Audit    │             │ │
│  │  │   Models   │  │   Models   │  │   Trail    │             │ │
│  │  └────────────┘  └────────────┘  └────────────┘             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              notification_service.py                          │ │
│  │  • send_document_effective_notification()                     │ │
│  │  • send_document_obsolete_notification()                      │ │
│  │  • send_workflow_timeout_notification()                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │         monitoring_dashboard.py + api_views.py                │ │
│  │  • Manual trigger UI                                          │ │
│  │  • Task execution status                                      │ │
│  │  • REST API endpoints                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## 3. Celery Beat Schedule Flow

```
┌────────────────────────────────────────────────────────────────┐
│              Celery Beat (Scheduler Service)                    │
└───────────────────────┬────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  Every Hour   │ │  Every Hour   │ │ Every 4 Hours │
│    XX:00      │ │    XX:15      │ │  00,04,08,... │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌────────────────┐ ┌──────────────┐ ┌─────────────────┐
│process_document│ │process_docum-│ │check_workflow_  │
│_effective_dates│ │ent_obsoletion│ │    timeouts     │
│                │ │    _dates    │ │                 │
└────────┬───────┘ └──────┬───────┘ └────────┬────────┘
         │                │                  │
         └────────────────┼──────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Redis Queue    │
                 │  (scheduler)    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Celery Worker   │
                 │  Picks up task  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   Execute &     │
                 │  Store Result   │
                 └─────────────────┘

Additional Schedules:
• Every 30 min → perform_system_health_check
• Daily 03:00  → cleanup_celery_results
```

## 4. Document Lifecycle Automation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Document Lifecycle States                      │
└─────────────────────────────────────────────────────────────────┘

    User Action                 Scheduler Automation
    
    ┌────────┐
    │ DRAFT  │
    └───┬────┘
        │ (submit for review)
        ▼
    ┌─────────────────┐
    │ PENDING_REVIEW  │
    └───┬─────────────┘
        │ (review approval)
        ▼
    ┌──────────────────┐
    │ PENDING_APPROVAL │
    └───┬──────────────┘
        │ (approval + future effective_date)
        ▼
    ┌──────────────────────────┐
    │APPROVED_PENDING_EFFECTIVE│◄─────┐
    └───┬──────────────────────┘      │
        │                             │
        │ When effective_date         │ process_document_
        │ <= today (midnight UTC)     │ effective_dates
        │                             │ (hourly at XX:00)
        ▼                             │
    ┌───────────┐                     │
    │ EFFECTIVE │─────────────────────┘
    └───┬───────┘
        │ (user marks for obsolescence + obsolescence_date)
        ▼
    ┌──────────────────────────────┐
    │SCHEDULED_FOR_OBSOLESCENCE    │◄─────┐
    └───┬──────────────────────────┘      │
        │                                 │
        │ When obsolescence_date          │ process_document_
        │ <= today (midnight UTC)         │ obsoletion_dates
        │                                 │ (hourly at XX:15)
        ▼                                 │
    ┌──────────┐                          │
    │ OBSOLETE │──────────────────────────┘
    └──────────┘
    (terminal state)
```

## 5. Task Execution Data Flow

```
┌────────────────────────────────────────────────────────────────┐
│              process_document_effective_dates()                 │
└────────────────────────────────────────────────────────────────┘

1. Query Database
   ───────────────────────────────────────────────────
   Document.objects.filter(
       status='APPROVED_PENDING_EFFECTIVE',
       effective_date__lte=timezone.now().date(),
       is_active=True
   )
   
2. For Each Document (in transaction.atomic()):
   ───────────────────────────────────────────────────
   ┌─────────────────────────────────────────┐
   │ Update Document                         │
   │ • status = 'EFFECTIVE'                  │
   └─────────────┬───────────────────────────┘
                 │
                 ▼
   ┌─────────────────────────────────────────┐
   │ Update Workflow (if exists)             │
   │ • current_state = 'EFFECTIVE'           │
   │ • Create DocumentTransition             │
   └─────────────┬───────────────────────────┘
                 │
                 ▼
   ┌─────────────────────────────────────────┐
   │ Create Audit Trail                      │
   │ • user = system_scheduler               │
   │ • action = 'DOC_EFFECTIVE_PROCESSED'    │
   │ • field_changes = {...}                 │
   └─────────────┬───────────────────────────┘
                 │
                 ▼
   ┌─────────────────────────────────────────┐
   │ Send Email Notification                 │
   │ • To: document.author.email             │
   │ • Subject: "Document Now Effective"     │
   └─────────────────────────────────────────┘

3. Return Results
   ───────────────────────────────────────────────────
   {
     'processed_count': 3,
     'success_count': 3,
     'error_count': 0,
     'processed_documents': [...],
     'errors': [],
     'timestamp': '2026-01-16T23:51:05Z'
   }
```

## 6. Queue Routing Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Celery Worker Process                       │
│  celery -A edms worker -Q celery,scheduler,documents,workflows │
└────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
        ┌──────────────┐  ┌──────────┐  ┌──────────┐
        │Queue: celery │  │Queue:    │  │Queue:    │
        │  (default)   │  │scheduler │  │documents │
        └──────────────┘  └──────────┘  └──────────┘
              │                 │              │
              ▼                 ▼              ▼
        ┌──────────┐  ┌──────────────────┐  ┌──────────┐
        │ General  │  │ Scheduler tasks: │  │ Document │
        │  tasks   │  │ • effective_dates│  │processing│
        └──────────┘  │ • obsoletion     │  └──────────┘
                      │ • timeouts       │
                      │ • health_check   │
                      └──────────────────┘
                      
        ┌──────────┐  ┌──────────────┐
        │Queue:    │  │Queue:        │
        │workflows │  │maintenance   │
        └──────────┘  └──────────────┘
              │              │
              ▼              ▼
        ┌──────────┐  ┌──────────────┐
        │ Workflow │  │ • cleanup    │
        │  tasks   │  │ • audit      │
        └──────────┘  └──────────────┘

Priority Levels:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High (8)     : Effective & Obsoletion processing
Medium (6)   : Workflow timeout monitoring
Low (4-5)    : Health checks, cleanup
```

## 7. System Health Check Architecture

```
┌────────────────────────────────────────────────────────────────┐
│            perform_system_health_check() Every 30 min           │
└────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  _check_     │     │  _check_     │     │  _check_     │
│  database()  │     │  workflows() │     │  audit_sys() │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ • user_count       │ • active_workflows │ • recent_audits
       │ • document_count   │ • completed_wf     │ • last 24h
       │ • workflow_count   │                    │
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  _check_     │     │  _check_     │     │   Create     │
│  doc_storage │     │ performance()│     │ Audit Trail  │
└──────┬───────┘     └──────┬───────┘     └──────────────┘
       │                    │
       │ • total_docs       │ • cpu_usage
       │ • storage_access   │ • memory_usage
       │                    │ • disk_usage
       │                    │
       └────────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  overall_status  │
          │  • HEALTHY       │
          │  • UNHEALTHY     │
          │  • CRITICAL      │
          └──────────────────┘
```

## 8. Error Handling & Retry Flow

```
Task Execution with Retry Logic
────────────────────────────────────────────

Start Task
    │
    ▼
Try Execute
    │
    ├─ Success? ─────────► Return Results ──► Store in DB
    │                      (TaskResult)
    ▼
  Failure
    │
    ▼
Check Retries
    │
    ├─ retries < max_retries (3)?
    │  │
    │  ▼ YES
    │  Retry with backoff
    │  • Attempt 1: wait 60s
    │  • Attempt 2: wait 120s
    │  • Attempt 3: wait 180s
    │  │
    │  └──────────┐
    │             │
    │  ▼ NO       │
    │  Fail       │
    │  Permanently│
    │             │
    └─────────────┴──────► Log Error
                            │
                            ▼
                          Send Alert
                          (if configured)
```

## 9. Monitoring Dashboard Integration

```
┌────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                         │
└────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Django     │     │     REST     │     │   React      │
│  Admin View  │     │     API      │     │  Dashboard   │
│              │     │              │     │   Widget     │
│ /scheduler/  │     │ /api/v1/     │     │ (Admin UI)   │
│  dashboard/  │     │  scheduler/  │     │              │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │ monitoring_dashboard.py│
                └────────┬───────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│View Task List│  │Manual Trigger│  │View Results  │
│• Next run    │  │POST /trigger/│  │• Last run    │
│• Schedule    │  │   <task>     │  │• Status      │
│• Status      │  │              │  │• Output      │
└──────────────┘  └──────────────┘  └──────────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  Execute task    │
                │  .apply_async()  │
                └──────────────────┘
```

---

## Summary

The EDMS Scheduler is a **multi-layered system** with:

1. **Celery Beat** - Cron-like scheduler that triggers tasks
2. **Celery Worker** - Executes tasks from 5 different queues
3. **Service Layer** - Encapsulates all business logic
4. **Integration Layer** - Interacts with Documents, Workflows, Audit
5. **Notification Layer** - Sends email alerts for automated events
6. **Monitoring Layer** - UI and API for manual control and visibility

**Key Design Patterns:**
- ✅ Separation of Concerns (tasks → services → models)
- ✅ Transaction Safety (atomic operations)
- ✅ Retry Mechanisms (exponential backoff)
- ✅ Queue Distribution (priority-based routing)
- ✅ Comprehensive Logging (audit trail integration)

