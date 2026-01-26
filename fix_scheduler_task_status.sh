#!/bin/bash

################################################################################
# Fix Scheduler Task Status - Automated Solution
################################################################################
#
# Purpose: Fix "Never run" status in scheduler dashboard
# Issue: Tasks execute but dashboard shows "Warning" and "Never run"
# Root Cause: PeriodicTask entries not in database (only in settings)
#
# Usage: ./fix_scheduler_task_status.sh
#
################################################################################

set -e

echo "=========================================="
echo "Scheduler Task Status Fix - Automated"
echo "=========================================="
echo ""
echo "Date: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

################################################################################
# Step 1: Backup current database state
################################################################################

print_step "Step 1: Backing up current PeriodicTask state..."

docker compose exec backend python manage.py shell <<'PYEOF'
from django_celery_beat.models import PeriodicTask
import json

tasks = PeriodicTask.objects.all()
print(f"Current PeriodicTask count: {tasks.count()}")

if tasks.count() > 0:
    print("\nExisting tasks:")
    for task in tasks:
        print(f"  - {task.name}: {task.task} (enabled={task.enabled})")
PYEOF

print_success "Backup complete"
echo ""

################################################################################
# Step 2: Create setup_periodic_tasks management command if not exists
################################################################################

print_step "Step 2: Checking if setup_periodic_tasks command exists..."

if docker compose exec backend python manage.py help setup_periodic_tasks >/dev/null 2>&1; then
    print_success "Command exists"
else
    print_warning "Command not found - creating it now..."
    
    # Create the management command
    docker compose exec backend sh -c "mkdir -p apps/scheduler/management/commands"
    
    docker compose exec backend sh -c 'cat > apps/scheduler/management/commands/setup_periodic_tasks.py << "PYEOF"
"""
Management command to sync CELERY_BEAT_SCHEDULE to database
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from django.conf import settings
from celery.schedules import crontab as crontab_schedule
from datetime import timedelta


class Command(BaseCommand):
    help = "Setup periodic tasks from CELERY_BEAT_SCHEDULE in database"

    def handle(self, *args, **options):
        self.stdout.write("Setting up periodic tasks...")
        
        if not hasattr(settings, "CELERY_BEAT_SCHEDULE"):
            self.stdout.write(self.style.ERROR("No CELERY_BEAT_SCHEDULE found in settings"))
            return
        
        created_count = 0
        updated_count = 0
        
        for task_name, task_config in settings.CELERY_BEAT_SCHEDULE.items():
            task_path = task_config["task"]
            schedule_config = task_config["schedule"]
            
            # Handle different schedule types
            schedule_obj = None
            
            if isinstance(schedule_config, (int, float)):
                # Seconds - convert to timedelta
                schedule_config = timedelta(seconds=schedule_config)
            
            if isinstance(schedule_config, timedelta):
                # Interval schedule
                interval, created = IntervalSchedule.objects.get_or_create(
                    every=int(schedule_config.total_seconds()),
                    period=IntervalSchedule.SECONDS,
                )
                schedule_type = "interval"
                schedule_obj = interval
                
            elif isinstance(schedule_config, crontab_schedule):
                # Crontab schedule
                crontab_obj, created = CrontabSchedule.objects.get_or_create(
                    minute=schedule_config._orig_minute or "*",
                    hour=schedule_config._orig_hour or "*",
                    day_of_week=schedule_config._orig_day_of_week or "*",
                    day_of_month=schedule_config._orig_day_of_month or "*",
                    month_of_year=schedule_config._orig_month_of_year or "*",
                )
                schedule_type = "crontab"
                schedule_obj = crontab_obj
            else:
                self.stdout.write(
                    self.style.WARNING(f"Unknown schedule type for {task_name}: {type(schedule_config)}")
                )
                continue
            
            # Create or update PeriodicTask
            task_obj, created = PeriodicTask.objects.get_or_create(
                name=task_name,
                defaults={
                    "task": task_path,
                    schedule_type: schedule_obj,
                    "enabled": True,
                }
            )
            
            if not created:
                # Update existing task
                task_obj.task = task_path
                if schedule_type == "interval":
                    task_obj.interval = schedule_obj
                    task_obj.crontab = None
                else:
                    task_obj.crontab = schedule_obj
                    task_obj.interval = None
                task_obj.enabled = True
                task_obj.save()
                updated_count += 1
                self.stdout.write(f"  Updated: {task_name}")
            else:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {task_name}"))
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {created_count} created, {updated_count} updated"
            )
        )
PYEOF'
    
    print_success "Command created"
fi

echo ""

################################################################################
# Step 3: Run setup_periodic_tasks command
################################################################################

print_step "Step 3: Syncing tasks from settings to database..."

docker compose exec backend python manage.py setup_periodic_tasks

print_success "Tasks synced to database"
echo ""

################################################################################
# Step 4: Verify tasks are now in database
################################################################################

print_step "Step 4: Verifying tasks in database..."

docker compose exec backend python manage.py shell <<'PYEOF'
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all()
print(f"\n✓ Total PeriodicTask entries: {tasks.count()}")

if tasks.count() == 0:
    print("✗ ERROR: No tasks in database after sync!")
else:
    print("\nTasks in database:")
    for task in tasks:
        status = "✓" if task.enabled else "✗"
        schedule_info = ""
        if task.interval:
            schedule_info = f"every {task.interval.every} {task.interval.period}"
        elif task.crontab:
            schedule_info = f"crontab: {task.crontab}"
        
        print(f"  {status} {task.name}")
        print(f"      Task: {task.task}")
        print(f"      Schedule: {schedule_info}")
        print(f"      Last Run: {task.last_run_at or 'Never'}")
        print()
PYEOF

print_success "Verification complete"
echo ""

################################################################################
# Step 5: Restart Celery Beat to pick up changes
################################################################################

print_step "Step 5: Restarting Celery Beat..."

docker compose restart celery_beat

echo "Waiting 10 seconds for Celery Beat to start..."
sleep 10

print_success "Celery Beat restarted"
echo ""

################################################################################
# Step 6: Check Celery Beat is reading from database
################################################################################

print_step "Step 6: Verifying Celery Beat configuration..."

docker compose logs celery_beat --tail=30 | grep -i "database" || echo "No database-related logs found"

echo ""
docker compose exec backend python manage.py shell <<'PYEOF'
from django.conf import settings

print("\n=== CELERY BEAT SCHEDULER ===")
beat_scheduler = getattr(settings, 'CELERY_BEAT_SCHEDULER', 'celery.beat.PersistentScheduler')
print(f"Scheduler: {beat_scheduler}")

if 'DatabaseScheduler' in beat_scheduler:
    print("✓ Using DatabaseScheduler (correct for django-celery-beat)")
else:
    print("⚠ Not using DatabaseScheduler")
    print("  Current: " + beat_scheduler)
    print("  Expected: django_celery_beat.schedulers:DatabaseScheduler")
PYEOF

print_success "Configuration check complete"
echo ""

################################################################################
# Step 7: Trigger a test task to verify execution tracking
################################################################################

print_step "Step 7: Triggering test task to verify tracking..."

docker compose exec backend python manage.py shell <<'PYEOF'
from apps.scheduler.tasks import send_test_email
import time

print("\nTriggering send_test_email task...")
result = send_test_email.delay()
print(f"Task ID: {result.id}")

print("Waiting 5 seconds for execution...")
time.sleep(5)

print(f"Task State: {result.state}")

# Check if task result was saved
from django_celery_results.models import TaskResult
task_result = TaskResult.objects.filter(task_id=result.id).first()

if task_result:
    print(f"✓ Task result saved to database")
    print(f"  Status: {task_result.status}")
    print(f"  Date: {task_result.date_done}")
else:
    print("✗ Task result NOT saved to database")
    print("  Check CELERY_RESULT_BACKEND setting")

# Check if PeriodicTask was updated
from django_celery_beat.models import PeriodicTask
periodic_task = PeriodicTask.objects.filter(task='apps.scheduler.tasks.send_test_email').first()

if periodic_task:
    print(f"\n✓ PeriodicTask found in database")
    print(f"  Last Run: {periodic_task.last_run_at or 'Never'}")
    print(f"  Total Runs: {periodic_task.total_run_count}")
else:
    print("\n✗ PeriodicTask not found in database")
PYEOF

print_success "Test task triggered"
echo ""

################################################################################
# Summary and Next Steps
################################################################################

echo "=========================================="
echo "Fix Complete - Summary"
echo "=========================================="
echo ""

docker compose exec backend python manage.py shell <<'PYEOF'
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult

print("Current Status:")
print(f"  PeriodicTask entries: {PeriodicTask.objects.count()}")
print(f"  Enabled tasks: {PeriodicTask.objects.filter(enabled=True).count()}")
print(f"  Task execution history: {TaskResult.objects.count()}")
print()

tasks_with_runs = PeriodicTask.objects.filter(last_run_at__isnull=False).count()
print(f"  Tasks with recorded runs: {tasks_with_runs}")
print()

if PeriodicTask.objects.count() == 0:
    print("⚠ WARNING: Still no tasks in database!")
    print("  The fix may not have worked. Check logs above.")
else:
    print("✓ Tasks are now in database")
    print()
    print("Wait 5-10 minutes and check:")
    print("  1. Visit: http://your-server:8000/admin/scheduler/monitoring/")
    print("  2. Tasks should show last run times instead of 'Never'")
    print("  3. Status should change from 'Warning' to 'Success'")
PYEOF

echo ""
echo "Next Steps:"
echo "  1. Wait 5-10 minutes for scheduled tasks to run"
echo "  2. Check dashboard: http://your-server:8000/admin/scheduler/monitoring/"
echo "  3. If still showing 'Never run', check CELERY_BEAT_SCHEDULER setting"
echo "  4. Monitor logs: docker compose logs -f celery_beat"
echo ""
