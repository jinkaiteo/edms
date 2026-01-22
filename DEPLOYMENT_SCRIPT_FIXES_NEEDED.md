# Interactive Deployment Script - Missing Fixes Analysis

**Date:** January 17, 2026

## Issues Fixed Today vs Deploy Script Coverage

### ✅ Fixes in Git (Code Level)

| Fix | Files Changed | Status | In deploy-interactive.sh? |
|-----|---------------|--------|---------------------------|
| 1. Scheduler timeout (fire-and-forget) | `monitoring_dashboard.py` | ✅ In git | ✅ Auto (code change) |
| 2. Dashboard stats table names | `dashboard_stats.py` | ✅ In git | ✅ Auto (code change) |
| 3. Placeholders (32 total) | `setup_placeholders.py` | ✅ In git | ❌ **MISSING** |
| 4. Celery worker queues | `docker-compose.prod.yml` | ✅ In git | ✅ Auto (docker config) |
| 5. Celery result backend | `docker-compose.prod.yml` | ✅ In git | ✅ Auto (docker config) |

### ❌ Missing from Deploy Script

**1. Placeholder Initialization**
- **Command needed:** `python manage.py setup_placeholders`
- **Current status:** Script doesn't call this command
- **Impact:** Fresh deployments will have 0 placeholders instead of 32
- **Location to add:** After line 839 in `initialize_database()` function

**2. Scheduler PeriodicTask Initialization**  
- **Command needed:** Initialize Celery Beat schedule to create PeriodicTask records
- **Current status:** Script doesn't initialize scheduled tasks
- **Impact:** "Last Run" will show "Never" and no automatic scheduling until Beat runs first time
- **Location to add:** After line 849 in `initialize_database()` function

### ✅ Already Handled by Code Changes

These fixes are in the code/config files and deploy automatically:
- Scheduler timeout fix (Python code)
- Dashboard stats fix (Python code)
- Worker queue configuration (docker-compose.yml)
- Result backend fix (docker-compose.yml)

---

## Recommended Script Updates

Add these commands to `deploy-interactive.sh` in the `initialize_database()` function:

```bash
# After line 839 (after document sources)
echo ""
print_step "Initializing placeholders (32 standard placeholders)..."
echo ""

if docker compose -f docker-compose.prod.yml exec -T backend python manage.py setup_placeholders; then
    print_success "Placeholders initialized (32 placeholders)"
else
    print_warning "Placeholder initialization had warnings (may already exist)"
fi

# After line 849 (after workflow defaults)
echo ""
print_step "Initializing Celery Beat schedule..."
echo ""

if docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from edms.celery import app
beat_schedule = app.conf.beat_schedule
created = 0
for name, config in beat_schedule.items():
    task_path = config['task']
    schedule_config = config['schedule']
    if hasattr(schedule_config, 'minute'):
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=str(schedule_config.minute),
            hour=str(schedule_config.hour),
            day_of_week=str(schedule_config.day_of_week),
            day_of_month=str(schedule_config.day_of_month),
            month_of_year=str(schedule_config.month_of_year),
        )
        task, was_created = PeriodicTask.objects.get_or_create(
            name=name,
            defaults={'task': task_path, 'crontab': crontab, 'enabled': True}
        )
        if was_created:
            created += 1
print(f'Created {created} scheduled tasks')
print(f'Total scheduled tasks: {PeriodicTask.objects.count()}')
"; then
    print_success "Celery Beat schedule initialized (5 tasks)"
else
    print_warning "Scheduler initialization had warnings"
fi
```

---

## Current Workaround

For deployments done before script is updated, run manually after deployment:

```bash
# Initialize placeholders
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_placeholders

# Initialize scheduler
./fix_scheduler_issues.sh
```

---

## Impact if Not Fixed

**Without placeholder initialization:**
- Dashboard shows "Placeholders: 0" instead of "32"
- Document annotation won't work
- PDF generation will fail

**Without scheduler initialization:**
- Manual trigger works ✅
- But "Last Run" shows "Never" forever ❌
- Scheduled tasks won't auto-run until Beat initializes ❌

---

## Status

- [ ] Update `deploy-interactive.sh` with placeholder initialization
- [ ] Update `deploy-interactive.sh` with scheduler initialization
- [x] Document workaround for existing deployments
- [x] Test fixes work on staging server
