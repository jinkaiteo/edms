#!/bin/bash

################################################################################
# Scheduler Task Status Diagnostic Script
################################################################################
#
# Purpose: Diagnose why scheduler tasks show "Never run" despite executing
# Issue: Tasks execute successfully but dashboard shows "Warning" and "Never run"
#
# Usage: ./diagnose_scheduler_task_status.sh
#
################################################################################

set -e

echo "=================================="
echo "Scheduler Task Status Diagnostic"
echo "=================================="
echo ""
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# 1. Container Status Check
################################################################################

print_header "1. Docker Container Status"

echo "Checking if containers are running..."
docker compose ps

echo ""
echo "Checking Celery Beat health:"
docker compose exec celery_beat sh -c "ps aux | grep celery" || print_warning "Celery Beat process check failed"

echo ""
echo "Checking Celery Worker health:"
docker compose exec celery_worker sh -c "ps aux | grep celery" || print_warning "Celery Worker process check failed"

################################################################################
# 2. Celery Beat Schedule Check
################################################################################

print_header "2. Celery Beat Schedule Configuration"

echo "Checking if Celery Beat schedule is configured..."
docker compose exec backend python manage.py shell <<'PYEOF'
from django.conf import settings
import json

print("\n=== CELERY BEAT SCHEDULE ===")
print(f"Schedule configured: {hasattr(settings, 'CELERY_BEAT_SCHEDULE')}")

if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    schedule = settings.CELERY_BEAT_SCHEDULE
    print(f"\nTotal tasks configured: {len(schedule)}")
    print("\nConfigured Tasks:")
    for task_name, config in schedule.items():
        print(f"\n  Task: {task_name}")
        print(f"    - Celery Task: {config.get('task')}")
        print(f"    - Schedule: {config.get('schedule')}")
        print(f"    - Options: {config.get('options', {})}")
else:
    print("ERROR: CELERY_BEAT_SCHEDULE not configured!")
PYEOF

################################################################################
# 3. Django Celery Beat (Database) Check
################################################################################

print_header "3. Django Celery Beat Database Check"

echo "Checking PeriodicTask entries in database..."
docker compose exec backend python manage.py shell <<'PYEOF'
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from datetime import datetime

print("\n=== PERIODIC TASKS IN DATABASE ===")
periodic_tasks = PeriodicTask.objects.all()
print(f"Total PeriodicTask entries: {periodic_tasks.count()}")

if periodic_tasks.count() == 0:
    print("\n⚠ WARNING: No PeriodicTask entries found in database!")
    print("   This explains why tasks show 'Never run' in dashboard.")
    print("   Tasks may be configured in settings but not in database.")
else:
    print("\nPeriodic Tasks:")
    for task in periodic_tasks:
        print(f"\n  Task: {task.name}")
        print(f"    - Task Path: {task.task}")
        print(f"    - Enabled: {task.enabled}")
        print(f"    - Last Run: {task.last_run_at or 'Never'}")
        print(f"    - Total Runs: {task.total_run_count}")
        print(f"    - Interval: {task.interval}")
        print(f"    - Crontab: {task.crontab}")

print("\n=== INTERVAL SCHEDULES ===")
intervals = IntervalSchedule.objects.all()
print(f"Total IntervalSchedule entries: {intervals.count()}")
for interval in intervals:
    print(f"  - Every {interval.every} {interval.period}")

print("\n=== CRONTAB SCHEDULES ===")
crontabs = CrontabSchedule.objects.all()
print(f"Total CrontabSchedule entries: {crontabs.count()}")
for crontab in crontabs:
    print(f"  - {crontab}")
PYEOF

################################################################################
# 4. Task Execution History Check
################################################################################

print_header "4. Task Execution History (django-celery-results)"

echo "Checking if tasks have been executed..."
docker compose exec backend python manage.py shell <<'PYEOF'
from django_celery_results.models import TaskResult
from datetime import datetime, timedelta

print("\n=== TASK EXECUTION HISTORY ===")
recent_results = TaskResult.objects.all().order_by('-date_done')[:20]
print(f"Total task results in database: {TaskResult.objects.count()}")
print(f"Recent results (last 20):\n")

if recent_results.count() == 0:
    print("⚠ No task execution history found!")
    print("  Tasks may not be executing, or results backend not configured.")
else:
    for result in recent_results:
        status_emoji = "✓" if result.status == "SUCCESS" else "✗"
        print(f"{status_emoji} {result.task_name}")
        print(f"   Status: {result.status}")
        print(f"   Date: {result.date_done}")
        print(f"   Task ID: {result.task_id}")
        if result.status == "FAILURE":
            print(f"   Error: {result.result}")
        print()

# Check for specific scheduler tasks
print("\n=== SCHEDULER TASK RESULTS ===")
scheduler_tasks = TaskResult.objects.filter(
    task_name__icontains='scheduler'
).order_by('-date_done')[:10]

print(f"Scheduler task executions found: {scheduler_tasks.count()}")
for task in scheduler_tasks:
    print(f"  - {task.task_name}: {task.status} at {task.date_done}")
PYEOF

################################################################################
# 5. Celery Beat Scheduler Database File Check
################################################################################

print_header "5. Celery Beat Scheduler File Check"

echo "Checking if celerybeat-schedule file exists..."
docker compose exec celery_beat sh -c "ls -la /tmp/celerybeat-schedule 2>/dev/null || echo 'File not found'" || print_warning "Cannot access celerybeat-schedule file"

echo ""
echo "Checking Celery worker state DB..."
docker compose exec celery_worker sh -c "ls -la /tmp/celery_worker_state 2>/dev/null || echo 'File not found'" || print_warning "Cannot access worker state file"

################################################################################
# 6. Configuration Mismatch Check
################################################################################

print_header "6. Configuration Mismatch Detection"

echo "Checking if tasks are configured in settings vs database..."
docker compose exec backend python manage.py shell <<'PYEOF'
from django.conf import settings
from django_celery_beat.models import PeriodicTask

print("\n=== CONFIGURATION MISMATCH CHECK ===")

# Get tasks from settings
settings_tasks = set()
if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    for task_name, config in settings.CELERY_BEAT_SCHEDULE.items():
        settings_tasks.add(config.get('task'))

# Get tasks from database
db_tasks = set(PeriodicTask.objects.values_list('task', flat=True))

print(f"Tasks in settings.CELERY_BEAT_SCHEDULE: {len(settings_tasks)}")
print(f"Tasks in database (PeriodicTask): {len(db_tasks)}")

print("\n=== TASKS ONLY IN SETTINGS (Not in DB) ===")
only_in_settings = settings_tasks - db_tasks
if only_in_settings:
    print("⚠ These tasks won't show execution status in dashboard:")
    for task in only_in_settings:
        print(f"  - {task}")
else:
    print("✓ All settings tasks exist in database")

print("\n=== TASKS ONLY IN DATABASE (Not in Settings) ===")
only_in_db = db_tasks - settings_tasks
if only_in_db:
    print("⚠ These database tasks may not execute:")
    for task in only_in_db:
        print(f"  - {task}")
else:
    print("✓ All database tasks exist in settings")

print("\n=== RECOMMENDATION ===")
if only_in_settings:
    print("ISSUE IDENTIFIED:")
    print("  Tasks are configured in settings but NOT in database.")
    print("  This is why dashboard shows 'Never run' - it checks the database.")
    print("\nSOLUTION:")
    print("  Run: python manage.py setup_periodic_tasks")
    print("  This will sync settings tasks to database.")
PYEOF

################################################################################
# 7. Recent Logs Check
################################################################################

print_header "7. Recent Celery Beat Logs"

echo "Checking last 50 lines of Celery Beat logs..."
docker compose logs celery_beat --tail=50

echo ""
print_header "8. Recent Celery Worker Logs"

echo "Checking last 50 lines of Celery Worker logs..."
docker compose logs celery_worker --tail=50

################################################################################
# 9. Manual Task Trigger Test
################################################################################

print_header "9. Manual Task Trigger Test"

echo "Testing manual task execution..."
docker compose exec backend python manage.py shell <<'PYEOF'
from apps.scheduler.tasks import send_test_email
from celery import current_app
import time

print("\n=== MANUAL TASK TRIGGER TEST ===")
print("Attempting to trigger send_test_email task...")

try:
    # Trigger task asynchronously
    result = send_test_email.delay()
    print(f"✓ Task triggered successfully")
    print(f"  Task ID: {result.id}")
    print(f"  Task State: {result.state}")
    
    # Wait a bit and check status
    print("\nWaiting 5 seconds for task to complete...")
    time.sleep(5)
    
    print(f"  Final State: {result.state}")
    if result.successful():
        print(f"  Result: {result.result}")
    elif result.failed():
        print(f"  Error: {result.result}")
    
except Exception as e:
    print(f"✗ Failed to trigger task: {e}")
    import traceback
    traceback.print_exc()
PYEOF

################################################################################
# 10. Scheduler Dashboard Data Check
################################################################################

print_header "10. Scheduler Dashboard Data Source Check"

echo "Checking what data source the scheduler dashboard uses..."
docker compose exec backend python manage.py shell <<'PYEOF'
from apps.scheduler.monitoring_dashboard import get_task_status
from django_celery_beat.models import PeriodicTask

print("\n=== SCHEDULER DASHBOARD DATA SOURCE ===")
print("The dashboard gets task status from:")
print("  1. PeriodicTask model (django_celery_beat)")
print("  2. TaskResult model (django_celery_results)")
print("  3. Celery inspect API")

print("\n=== CHECKING DASHBOARD FUNCTION ===")
try:
    status = get_task_status()
    print(f"Dashboard task count: {len(status)}")
    
    print("\nTask Status from Dashboard:")
    for task_name, task_info in status.items():
        print(f"\n  {task_name}:")
        print(f"    - Status: {task_info.get('status', 'UNKNOWN')}")
        print(f"    - Last Run: {task_info.get('last_run', 'Never')}")
        print(f"    - Enabled: {task_info.get('enabled', False)}")
        
except Exception as e:
    print(f"✗ Error getting dashboard status: {e}")
    import traceback
    traceback.print_exc()
PYEOF

################################################################################
# Summary and Recommendations
################################################################################

print_header "DIAGNOSTIC SUMMARY"

echo "Collecting diagnosis results..."
docker compose exec backend python manage.py shell <<'PYEOF'
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult
from django.conf import settings

print("\n=== ROOT CAUSE ANALYSIS ===\n")

has_settings_schedule = hasattr(settings, 'CELERY_BEAT_SCHEDULE')
db_tasks_count = PeriodicTask.objects.count()
task_results_count = TaskResult.objects.count()

print(f"Settings Schedule Configured: {'✓' if has_settings_schedule else '✗'}")
print(f"Database Tasks (PeriodicTask): {db_tasks_count}")
print(f"Task Execution History: {task_results_count}")

print("\n=== LIKELY ISSUES ===\n")

if db_tasks_count == 0:
    print("🔴 ISSUE #1: No PeriodicTask entries in database")
    print("   Impact: Dashboard shows 'Never run' for all tasks")
    print("   Reason: Dashboard reads from PeriodicTask model, not settings")
    print("   Solution: Run setup_periodic_tasks management command")
    print()

if task_results_count == 0:
    print("🔴 ISSUE #2: No task execution history")
    print("   Impact: No proof that tasks have executed")
    print("   Reason: Results backend may not be configured")
    print("   Solution: Verify CELERY_RESULT_BACKEND setting")
    print()

if has_settings_schedule and db_tasks_count == 0:
    print("🔴 ISSUE #3: Settings vs Database mismatch")
    print("   Impact: Tasks execute but status not tracked")
    print("   Reason: Settings define tasks, but database tracks execution")
    print("   Solution: Sync settings to database with management command")
    print()

print("\n=== RECOMMENDED ACTIONS ===\n")

print("1. Create/sync periodic tasks to database:")
print("   docker compose exec backend python manage.py setup_periodic_tasks")
print()

print("2. Verify tasks are in database:")
print("   docker compose exec backend python manage.py shell -c \"from django_celery_beat.models import PeriodicTask; print(PeriodicTask.objects.count())\"")
print()

print("3. Restart Celery Beat to pick up changes:")
print("   docker compose restart celery_beat")
print()

print("4. Check dashboard after 5 minutes:")
print("   Visit: http://your-server:8000/admin/scheduler/monitoring/")
print()

print("5. Monitor logs for task execution:")
print("   docker compose logs -f celery_worker celery_beat")
print()
PYEOF

print_header "DIAGNOSTIC COMPLETE"

echo ""
echo "Next steps:"
echo "1. Review the output above to identify the root cause"
echo "2. Follow the recommended actions"
echo "3. Re-run this script after applying fixes to verify"
echo ""
echo "Common fixes:"
echo "  - Run: docker compose exec backend python manage.py setup_periodic_tasks"
echo "  - Restart: docker compose restart celery_beat celery_worker"
echo "  - Check: Visit /admin/scheduler/monitoring/ after 5 minutes"
echo ""
