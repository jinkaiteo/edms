# 🎯 Existing Email Monitoring Tasks - Already Scheduled!

Great news! You already have **2 automated monitoring tasks** running:

---

## ✅ 1. System Health Check (Every 30 Minutes)

**Task:** `perform_system_health_check`  
**Schedule:** Every 30 minutes (*/30 * * * *)  
**Function:** `apps.scheduler.tasks.perform_system_health_check`

**What It Does:**
- Checks overall system health
- Monitors service status
- Tracks system metrics
- Logs health status

**Location:** `backend/apps/scheduler/tasks.py` (line 108)

**Health Service:** `backend/apps/scheduler/services/health.py`

---

## ✅ 2. Daily Health Report (Every Day at 7 AM)

**Task:** `send_daily_health_report`  
**Schedule:** Daily at 7:00 AM (0 7 * * *)  
**Function:** `apps.scheduler.tasks.send_daily_health_report`

**What It Does:**
- Runs comprehensive health check
- Sends email report to ALL admin users
- Includes system status
- Lists action items if issues found

**Location:** `backend/apps/scheduler/tasks.py` (line 278)

**Email Recipients:** All users with `is_staff=True` or `is_superuser=True`

---

## 📊 What's Already Monitored

Based on the health service, these tasks likely monitor:

1. **Service Health**
   - Database connectivity
   - Celery worker status
   - Redis/cache status

2. **System Metrics**
   - Task execution rates
   - Error counts
   - System load

3. **Application Status**
   - Background tasks running
   - Scheduled tasks active
   - System errors

---

## 💡 How to Enhance for Email Monitoring

### Option 1: Extend Existing Health Service (RECOMMENDED)

**Add email-specific checks to the health service:**

```python
# backend/apps/scheduler/services/health.py

def check_email_system_health(self):
    """Check email notification system health"""
    checks = {}
    
    # 1. Check SMTP configuration
    from django.conf import settings
    checks['smtp_configured'] = 'smtp' in settings.EMAIL_BACKEND.lower()
    
    # 2. Test SMTP connection
    try:
        import smtplib
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
        server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.quit()
        checks['smtp_connection'] = True
    except Exception as e:
        checks['smtp_connection'] = False
        checks['smtp_error'] = str(e)
    
    # 3. Count recent email tasks
    from django_celery_results.models import TaskResult
    import datetime
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
    email_tasks = TaskResult.objects.filter(
        task_name__icontains='email',
        date_done__gte=cutoff
    )
    checks['emails_sent_24h'] = email_tasks.filter(status='SUCCESS').count()
    checks['email_failures_24h'] = email_tasks.filter(status='FAILURE').count()
    
    # 4. Check users with email
    from django.contrib.auth import get_user_model
    User = get_user_model()
    checks['users_with_email'] = User.objects.filter(
        email__isnull=False
    ).exclude(email='').count()
    
    return checks
```

Then add it to the main health check method.

---

### Option 2: Create Dedicated Email Health Task (NEW)

**Add a new scheduled task specifically for email monitoring:**

```python
# backend/apps/scheduler/tasks.py

@shared_task(name='apps.scheduler.tasks.check_email_system_health')
def check_email_system_health():
    """
    Check email notification system health.
    Runs every hour.
    """
    from django.conf import settings
    from django.core.mail import send_mail
    import smtplib
    
    logger.info("Starting email system health check")
    
    issues = []
    
    # Check SMTP mode
    if 'console' in settings.EMAIL_BACKEND.lower():
        issues.append("⚠️ Email backend in CONSOLE mode - emails not being sent!")
    
    # Test SMTP connection
    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
        server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.quit()
        logger.info("✅ SMTP connection successful")
    except Exception as e:
        issues.append(f"❌ SMTP connection failed: {e}")
        logger.error(f"SMTP connection failed: {e}")
    
    # Check recent email activity
    from django_celery_results.models import TaskResult
    import datetime
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
    email_tasks = TaskResult.objects.filter(
        task_name__icontains='email',
        date_done__gte=cutoff
    )
    
    sent = email_tasks.filter(status='SUCCESS').count()
    failed = email_tasks.filter(status='FAILURE').count()
    
    logger.info(f"Email stats (24h): {sent} sent, {failed} failed")
    
    if failed > 10:
        issues.append(f"⚠️ High email failure rate: {failed} failures in last 24h")
    
    # Alert if critical issues
    if issues:
        logger.warning(f"Email health issues detected: {issues}")
        # Could send alert email to admins here
    
    return {
        'status': 'healthy' if not issues else 'degraded',
        'issues': issues,
        'emails_sent_24h': sent,
        'emails_failed_24h': failed
    }
```

Then add to beat schedule:
```python
# backend/edms/celery.py

app.conf.beat_schedule = {
    # ... existing tasks ...
    'check-email-system-health': {
        'task': 'apps.scheduler.tasks.check_email_system_health',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

---

## 🎯 Recommendation: Use Existing Tasks!

**Instead of creating new monitoring scripts, enhance the existing ones:**

### Pros of Using Existing Tasks:
1. ✅ Already scheduled and running
2. ✅ Already send email reports to admins
3. ✅ Integrated into system
4. ✅ No additional cron jobs needed
5. ✅ Centralized monitoring

### What to Do:
1. **Extend the health service** (`backend/apps/scheduler/services/health.py`)
2. **Add email-specific checks** to `check_email_system_health()` method
3. **Include in daily report** automatically
4. **Set alert thresholds** for email failures

---

## 📋 Current vs Enhanced Monitoring

### Current (What You Have Now):
```
✅ System Health Check (every 30 min)
   - General system health
   - Service status
   
✅ Daily Health Report (7 AM daily)
   - Email report to admins
   - System status summary
```

### Enhanced (Add Email Monitoring):
```
✅ System Health Check (every 30 min)
   - General system health
   - Service status
   + SMTP connection test
   + Email task success rate
   + Recent email activity
   
✅ Daily Health Report (7 AM daily)
   - Email report to admins
   - System status summary
   + Email delivery stats
   + Email failures (if any)
   + Action items for email issues
```

---

## ✅ Summary

**You Already Have:**
- ✅ System health check (every 30 min)
- ✅ Daily health report email (7 AM)
- ✅ Health service framework

**You Can Add:**
- 📧 Email-specific health checks
- 📊 Email delivery metrics
- 🚨 Email failure alerts

**No Need For:**
- ❌ Separate cron jobs
- ❌ External monitoring scripts
- ❌ Additional scheduled tasks

**Recommendation:**
Extend the existing `system_health_service` to include email monitoring checks. This gives you comprehensive monitoring without additional complexity!

