#!/bin/bash

################################################################################
# Quick Fix for Scheduler Task Status - Staging Server
################################################################################
#
# Purpose: Fix "Never run" status by adding CELERY_BEAT_SCHEDULER to settings
# Root Cause: Missing CELERY_BEAT_SCHEDULER in settings/base.py
# Solution: Add DatabaseScheduler setting and restart Celery Beat
#
# Usage: ./fix_scheduler_staging_quick.sh
#
################################################################################

set -e

echo "=========================================="
echo "Scheduler Fix - Quick Solution"
echo "=========================================="
echo ""
echo "Date: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

################################################################################
# Step 1: Verify Current State
################################################################################

print_step "Step 1: Checking current scheduler configuration..."

CURRENT_SCHEDULER=$(docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
print(getattr(settings, 'CELERY_BEAT_SCHEDULER', 'NOT_SET'))
" 2>/dev/null | tail -1)

echo "Current CELERY_BEAT_SCHEDULER: $CURRENT_SCHEDULER"

if [[ "$CURRENT_SCHEDULER" == *"DatabaseScheduler"* ]]; then
    print_success "DatabaseScheduler already configured!"
    echo ""
    print_warning "If tasks still show 'Never run', Celery Beat may need restart."
    echo ""
    read -p "Restart Celery Beat anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. No changes made."
        exit 0
    fi
else
    print_warning "DatabaseScheduler NOT configured (found: $CURRENT_SCHEDULER)"
    echo "Will add the setting..."
fi

echo ""

################################################################################
# Step 2: Backup Current Settings File
################################################################################

print_step "Step 2: Creating backup of settings file..."

docker compose exec -T backend sh -c "
cp /app/edms/settings/base.py /app/edms/settings/base.py.backup.$(date +%Y%m%d_%H%M%S)
echo 'Backup created'
" || print_error "Backup failed"

print_success "Backup created"
echo ""

################################################################################
# Step 3: Add CELERY_BEAT_SCHEDULER Setting
################################################################################

print_step "Step 3: Adding CELERY_BEAT_SCHEDULER to settings..."

docker compose exec -T backend python manage.py shell <<'PYEOF'
import os

settings_file = '/app/edms/settings/base.py'

# Read current content
with open(settings_file, 'r') as f:
    content = f.read()

# Check if already exists
if 'CELERY_BEAT_SCHEDULER' in content:
    print('Setting already exists!')
else:
    # Find the line with CELERY_BEAT_SCHEDULE_FILENAME
    lines = content.split('\n')
    new_lines = []
    added = False
    
    for line in lines:
        new_lines.append(line)
        if "CELERY_BEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule'" in line and not added:
            # Add the new setting after this line
            new_lines.append("# Use DatabaseScheduler to track task execution in database")
            new_lines.append("CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'")
            added = True
            print('✓ Added CELERY_BEAT_SCHEDULER setting')
    
    if added:
        # Write back
        with open(settings_file, 'w') as f:
            f.write('\n'.join(new_lines))
        print('✓ Settings file updated')
    else:
        print('✗ Could not find insertion point')
PYEOF

print_success "Setting added"
echo ""

################################################################################
# Step 4: Verify Setting Was Added
################################################################################

print_step "Step 4: Verifying setting was added..."

docker compose exec -T backend sh -c "grep -A 1 'CELERY_BEAT_SCHEDULER' /app/edms/settings/base.py || echo 'Setting not found'"

echo ""

################################################################################
# Step 5: Restart Celery Beat
################################################################################

print_step "Step 5: Restarting Celery Beat to load new configuration..."

docker compose restart celery_beat

echo "Waiting 10 seconds for startup..."
sleep 10

print_success "Celery Beat restarted"
echo ""

################################################################################
# Step 6: Verify Celery Beat is Using DatabaseScheduler
################################################################################

print_step "Step 6: Verifying Celery Beat is using DatabaseScheduler..."

echo "Checking logs for scheduler type..."
docker compose logs celery_beat --tail=30 | grep -i "scheduler" || print_warning "No scheduler info in logs"

echo ""
echo "Checking via Django settings..."
docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
scheduler = getattr(settings, 'CELERY_BEAT_SCHEDULER', 'NOT SET')
print(f'CELERY_BEAT_SCHEDULER: {scheduler}')

if 'DatabaseScheduler' in scheduler:
    print('✓ DatabaseScheduler configured correctly')
else:
    print('✗ DatabaseScheduler NOT configured')
    print('  You may need to rebuild the container:')
    print('  docker compose stop celery_beat')
    print('  docker compose build celery_beat')
    print('  docker compose up -d celery_beat')
"

echo ""

################################################################################
# Step 7: Check Task Status
################################################################################

print_step "Step 7: Checking current task status..."

docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
from datetime import datetime

tasks = PeriodicTask.objects.all()
print(f'\nTotal tasks: {tasks.count()}')
print(f'Enabled tasks: {tasks.filter(enabled=True).count()}')

tasks_with_runs = tasks.filter(last_run_at__isnull=False).count()
print(f'Tasks with recorded runs: {tasks_with_runs}')

if tasks_with_runs == 0:
    print('\nℹ All tasks show \"Never run\" - this is normal immediately after fix')
    print('  Tasks will update as they execute on their schedules')
    print('  Check again in 30-60 minutes')
else:
    print(f'\n✓ {tasks_with_runs} tasks have already run')
    print('\nRecent executions:')
    for task in tasks.filter(last_run_at__isnull=False)[:5]:
        print(f'  {task.name}: {task.last_run_at}, runs: {task.total_run_count}')
"

echo ""

################################################################################
# Step 8: Show Next Scheduled Tasks
################################################################################

print_step "Step 8: Next tasks scheduled to run..."

docker compose exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
from datetime import datetime
import pytz

now = datetime.now(pytz.UTC)

print('\nUpcoming tasks (within next hour):')
print('  - perform-system-health-check: Every 30 minutes')
print('  - process-document-effective-dates: Every hour at :00')
print('  - process-document-obsoletion-dates: Every hour at :15')
print('')
print('Wait 30-60 minutes, then check dashboard or run:')
print('  docker compose exec -T backend python manage.py shell -c \"')
print('    from django_celery_beat.models import PeriodicTask')
print('    for t in PeriodicTask.objects.all()[:5]:')
print('        print(f\"{t.name}: {t.last_run_at or \\\"Never\\\"}\")\"')
"

echo ""

################################################################################
# Summary
################################################################################

echo "=========================================="
echo "Fix Complete - Summary"
echo "=========================================="
echo ""

print_success "CELERY_BEAT_SCHEDULER setting added"
print_success "Celery Beat restarted with new configuration"
echo ""

echo "Next Steps:"
echo "  1. Wait 30-60 minutes for tasks to execute"
echo "  2. Check dashboard: http://staging-server:8001/admin/scheduler/monitoring/"
echo "  3. Expected: Status changes from 'Warning' to 'Success'"
echo "  4. Expected: 'Last Run' shows timestamps instead of 'Never'"
echo ""

echo "Quick verification command:"
echo "  docker compose exec -T backend python manage.py shell -c \\"
echo "    \"from django_celery_beat.models import PeriodicTask; \\"
echo "    for t in PeriodicTask.objects.all()[:5]: \\"
echo "      print(f'{t.name}: {t.last_run_at or \\\"Never\\\"}, runs: {t.total_run_count}')\""
echo ""

echo "Monitor live updates:"
echo "  docker compose logs -f celery_beat celery_worker"
echo ""

print_warning "If tasks still show 'Never' after 1 hour, you may need to rebuild:"
echo "  docker compose stop celery_beat"
echo "  docker compose build celery_beat"
echo "  docker compose up -d celery_beat"
echo ""

echo "=========================================="
