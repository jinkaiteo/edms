# Celery Not Executing Tasks - Diagnostic Guide

## Issue

All diagnostic commands return nothing:
- No task results in database
- No execution logs
- Tasks show as "Never run"
- But you received an email (?)

## Critical Diagnostics

### Step 1: Verify Celery Worker is Actually Running

```bash
# Check if celery_worker container is running
docker compose -f docker-compose.prod.yml ps celery_worker

# Should show: Up (healthy)
```

```bash
# Check worker logs
docker compose -f docker-compose.prod.yml logs celery_worker --tail=100

# Should see:
# "celery@... ready."
# "[tasks]" list of registered tasks
```

---

### Step 2: Verify django-celery-results is Installed

```bash
# Check if the app is in INSTALLED_APPS
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django.conf import settings

if 'django_celery_results' in settings.INSTALLED_APPS:
    print("✅ django_celery_results is installed")
else:
    print("❌ django_celery_results is NOT installed")
    
if 'django_celery_beat' in settings.INSTALLED_APPS:
    print("✅ django_celery_beat is installed")
else:
    print("❌ django_celery_beat is NOT installed")
PYTHON
```

---

### Step 3: Check if Result Backend is Configured

```bash
# Check Celery configuration
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from edms.celery import app

print("=== Celery Configuration ===")
print(f"Broker URL: {app.conf.broker_url}")
print(f"Result backend: {app.conf.result_backend}")
print(f"Task always eager: {app.conf.task_always_eager}")
print(f"Result extended: {app.conf.result_extended}")
PYTHON
```

**Expected:**
- `result_backend`: Should be set (e.g., 'django-db' or redis URL)
- `task_always_eager`: Should be False (True means synchronous, no worker)

---

### Step 4: Check if Tables Exist

```bash
# Check if django_celery_results tables exist
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%celery%'
""")

tables = [row[0] for row in cursor.fetchall()]
print("Celery tables:")
for table in tables:
    print(f"  • {table}")
    
if not tables:
    print("❌ No Celery tables found - migrations not run!")
PYTHON
```

**Expected tables:**
- `django_celery_beat_periodictask`
- `django_celery_beat_crontabschedule`
- `django_celery_results_taskresult`

---

### Step 5: Test Task Registration

```bash
# Check if send_test_email_to_self is registered
docker compose -f docker-compose.prod.yml exec celery_worker celery -A edms inspect registered | grep send_test_email

# Should show: apps.scheduler.tasks.send_test_email_to_self
```

---

### Step 6: Manually Trigger and Watch Logs

```bash
# Open two terminal windows

# Terminal 1: Watch worker logs
docker compose -f docker-compose.prod.yml logs celery_worker -f

# Terminal 2: Trigger task
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from apps.scheduler.tasks import send_test_email_to_self

print("Triggering task...")
result = send_test_email_to_self.delay()
print(f"Task ID: {result.id}")
PYTHON
```

**Watch Terminal 1 for:**
- Task received message
- Task execution
- Task success/failure

---

### Step 7: Check Celery Beat Logs

```bash
# Check if Beat is even scheduling tasks
docker compose -f docker-compose.prod.yml logs celery_beat --tail=200

# Look for:
# "Scheduler: Sending due task..."
# "DatabaseScheduler: Schedule changed"
# Task names being scheduled
```

---

### Step 8: Check Database Migrations

```bash
# Check if celery migrations are applied
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations django_celery_beat django_celery_results

# Should show all [X] checked, no [ ] empty boxes
```

**If migrations not applied:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate django_celery_beat
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate django_celery_results
```

---

### Step 9: Verify You Actually Received the Email

**Important Question:** Did you really receive an email, or are you seeing a frontend success message?

```bash
# Check your email inbox
# Look for: "EDMS Test Email" from the configured sender

# Check sent emails in Gmail
# Login to: jinkaiteo.tikva@gmail.com
# Check: Sent folder for "EDMS Test Email"
```

---

## Diagnostic Script (Run This First)

```bash
# Complete diagnostic on staging server
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from django.conf import settings
from edms.celery import app
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult
from django.db import connection

print("="*60)
print("CELERY DIAGNOSTIC REPORT")
print("="*60)

# 1. Check INSTALLED_APPS
print("\n1. Celery Apps Installed:")
print(f"   django_celery_beat: {'django_celery_beat' in settings.INSTALLED_APPS}")
print(f"   django_celery_results: {'django_celery_results' in settings.INSTALLED_APPS}")

# 2. Check Celery config
print("\n2. Celery Configuration:")
print(f"   Broker: {app.conf.broker_url}")
print(f"   Result backend: {app.conf.result_backend}")
print(f"   Beat scheduler: {app.conf.beat_scheduler}")
print(f"   Task always eager: {app.conf.task_always_eager}")

# 3. Check tables exist
print("\n3. Database Tables:")
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%celery%'")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"   ✅ {table}")

# 4. Check PeriodicTasks
print("\n4. Periodic Tasks:")
print(f"   Count: {PeriodicTask.objects.count()}")
for task in PeriodicTask.objects.all()[:5]:
    print(f"   • {task.name}: enabled={task.enabled}, last_run={task.last_run_at}")

# 5. Check TaskResults
print("\n5. Task Results:")
print(f"   Total: {TaskResult.objects.count()}")
recent = TaskResult.objects.order_by('-date_done')[:3]
for result in recent:
    print(f"   • {result.task_name}: {result.status} at {result.date_done}")

# 6. Check email config
print("\n6. Email Configuration:")
print(f"   Backend: {settings.EMAIL_BACKEND}")
print(f"   Host: {settings.EMAIL_HOST}")
print(f"   From: {settings.DEFAULT_FROM_EMAIL}")

print("\n" + "="*60)
PYTHON
```

---

## Next Steps

**Please run the diagnostic script above and send me the complete output.**

The output will tell us:
1. ✅ If Celery apps are installed
2. ✅ If result backend is configured
3. ✅ If database tables exist
4. ✅ If tasks are in database
5. ✅ If any tasks have executed

Based on the results, we can determine the exact issue.

---

**Date:** January 26, 2026  
**Issue:** Tasks appear to not execute (no results in database)  
**Action:** Run diagnostic script to identify root cause
