# 📊 Email Notification Monitoring Guide

**Purpose:** Monitor email notification system health, delivery rates, and identify issues

---

## 🎯 Monitoring Strategy Overview

### 3-Layer Monitoring Approach
1. **Real-time Logs** - Immediate issue detection
2. **Metrics & Counters** - Trend analysis
3. **Periodic Health Checks** - Proactive monitoring

---

## 1️⃣ Real-Time Log Monitoring

### A. Backend Email Logs

**What to Monitor:**
- Email send attempts
- SMTP connection status
- Delivery failures
- Exception traces

**Commands:**
```bash
# Monitor all email activity in real-time
docker compose logs -f backend | grep -i "email\|smtp"

# Monitor Celery worker email tasks
docker compose logs -f celery_worker | grep -i "email\|notification"

# Watch for errors only
docker compose logs -f backend celery_worker | grep -i "error\|failed\|exception" | grep -i email

# Monitor specific notification types
docker compose logs -f celery_worker | grep "send_test_email\|send_task_email"
```

**Example Output to Watch For:**
```
✅ GOOD:
celery_worker | [INFO] Email sent to user@example.com
celery_worker | [INFO] Task send_test_email_to_self[...] succeeded

❌ BAD:
celery_worker | [ERROR] SMTPAuthenticationError: Username and Password not accepted
celery_worker | [ERROR] Connection refused [Errno 111]
backend | [ERROR] Failed to send email to user@example.com
```

---

### B. Celery Task Monitoring

**Monitor Task Queue:**
```bash
# Check active tasks
docker compose exec celery_worker celery -A edms inspect active

# Check scheduled tasks
docker compose exec celery_worker celery -A edms inspect scheduled

# Check registered tasks (should include send_test_email_to_self)
docker compose exec celery_worker celery -A edms inspect registered | grep email
```

**Monitor Task Success/Failure:**
```bash
# View task statistics
docker compose exec backend python manage.py shell -c "
from celery.result import AsyncResult
from django_celery_results.models import TaskResult
import datetime

# Recent email tasks (last 24 hours)
cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
recent_tasks = TaskResult.objects.filter(
    task_name__icontains='email',
    date_done__gte=cutoff
)

print(f'Email tasks (last 24h): {recent_tasks.count()}')
print(f'Success: {recent_tasks.filter(status=\"SUCCESS\").count()}')
print(f'Failed: {recent_tasks.filter(status=\"FAILURE\").count()}')
print(f'Pending: {recent_tasks.filter(status=\"PENDING\").count()}')
"
```

---

## 2️⃣ Metrics & Counters

### A. Email Delivery Metrics

**Create Monitoring Script:**
```bash
# Save as: scripts/monitor-email-stats.sh
#!/bin/bash

echo "=== Email Notification Statistics ==="
echo ""

# Count emails sent today
TODAY=$(date +%Y-%m-%d)
docker compose logs backend celery_worker --since="$TODAY" | grep -c "Email sent" || echo "0"

# Count by notification type
echo ""
echo "By Notification Type:"
echo "- Task Assignments: $(docker compose logs celery_worker --since="$TODAY" | grep -c "send_task_email")"
echo "- Document Effective: $(docker compose logs celery_worker --since="$TODAY" | grep -c "send_document_effective")"
echo "- Document Obsolete: $(docker compose logs celery_worker --since="$TODAY" | grep -c "send_document_obsolete")"
echo "- Test Emails: $(docker compose logs celery_worker --since="$TODAY" | grep -c "send_test_email")"

# Count failures
echo ""
echo "Failures: $(docker compose logs backend celery_worker --since="$TODAY" | grep -i "failed.*email\|error.*email" | wc -l)"

# SMTP errors
echo "SMTP Errors: $(docker compose logs backend celery_worker --since="$TODAY" | grep -i "smtp.*error\|smtp.*failed" | wc -l)"
```

**Usage:**
```bash
chmod +x scripts/monitor-email-stats.sh
./scripts/monitor-email-stats.sh
```

---

### B. Database Monitoring

**Check Email-Related Data:**
```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.workflows.models import WorkflowTask
from apps.documents.models import Document
import datetime

User = get_user_model()

print('=== Email System Health ===')
print()

# Users with email addresses
users_with_email = User.objects.filter(email__isnull=False).exclude(email='')
print(f'Users with email: {users_with_email.count()} / {User.objects.count()}')
print(f'Users without email: {User.objects.filter(email__isnull=True).count() + User.objects.filter(email=\"\").count()}')

print()

# Recent workflow tasks (should trigger emails)
cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
recent_tasks = WorkflowTask.objects.filter(created_at__gte=cutoff)
print(f'Workflow tasks today: {recent_tasks.count()}')
print(f'  - PENDING: {recent_tasks.filter(status=\"PENDING\").count()}')
print(f'  - COMPLETED: {recent_tasks.filter(status=\"COMPLETED\").count()}')

print()

# Documents with status changes (trigger emails)
recent_effective = Document.objects.filter(status='EFFECTIVE', effective_date__gte=cutoff.date())
print(f'Documents became effective today: {recent_effective.count()}')
"
```

---

## 3️⃣ Periodic Health Checks

### A. Automated Health Check Script

**Create Health Check:**
```bash
# Save as: scripts/email-health-check.sh
#!/bin/bash

echo "========================================="
echo "  Email Notification System Health Check"
echo "========================================="
echo ""

# 1. Check SMTP Configuration
echo "1. SMTP Configuration"
docker compose exec backend python manage.py shell -c "
from django.conf import settings
backend = settings.EMAIL_BACKEND
if 'smtp' in backend.lower():
    print('   ✅ SMTP Mode Active')
else:
    print('   ❌ Console Mode (emails not sent!)')
    exit(1)
" || exit 1

# 2. Test SMTP Connection
echo ""
echo "2. SMTP Connection Test"
docker compose exec backend python manage.py shell -c "
from django.conf import settings
import smtplib
try:
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.quit()
    print('   ✅ SMTP Connection Successful')
except Exception as e:
    print(f'   ❌ SMTP Connection Failed: {e}')
    exit(1)
" || exit 1

# 3. Check Celery Workers
echo ""
echo "3. Celery Worker Status"
WORKER_STATUS=$(docker compose ps celery_worker --format json | jq -r '.State')
if [ "$WORKER_STATUS" = "running" ]; then
    echo "   ✅ Celery Worker Running"
else
    echo "   ❌ Celery Worker Not Running"
    exit 1
fi

# 4. Check Email Tasks Registered
echo ""
echo "4. Email Tasks Registration"
docker compose exec celery_worker celery -A edms inspect registered | grep -q "send_test_email_to_self"
if [ $? -eq 0 ]; then
    echo "   ✅ Email Tasks Registered"
else
    echo "   ❌ Email Tasks Not Registered"
    exit 1
fi

# 5. Check Recent Email Activity
echo ""
echo "5. Recent Email Activity (last 24h)"
EMAIL_COUNT=$(docker compose logs celery_worker --since="24h" | grep -c "Email sent" || echo "0")
echo "   Emails sent: $EMAIL_COUNT"
if [ $EMAIL_COUNT -gt 0 ]; then
    echo "   ✅ Email Activity Detected"
else
    echo "   ⚠️  No Email Activity (may be normal if no workflows)"
fi

# 6. Check for Errors
echo ""
echo "6. Error Check (last 24h)"
ERROR_COUNT=$(docker compose logs backend celery_worker --since="24h" | grep -i "error.*email\|failed.*email" | wc -l)
echo "   Email errors: $ERROR_COUNT"
if [ $ERROR_COUNT -eq 0 ]; then
    echo "   ✅ No Errors"
elif [ $ERROR_COUNT -lt 5 ]; then
    echo "   ⚠️  Few Errors (investigate if persistent)"
else
    echo "   ❌ High Error Rate (immediate investigation needed!)"
fi

echo ""
echo "========================================="
echo "  Health Check Complete"
echo "========================================="
```

**Run Health Check:**
```bash
chmod +x scripts/email-health-check.sh
./scripts/email-health-check.sh
```

**Schedule with Cron:**
```bash
# Run every hour
0 * * * * /path/to/edms/scripts/email-health-check.sh >> /var/log/edms-email-health.log 2>&1
```

---

### B. Test Email Cron Job

**Send Test Email Daily:**
```bash
# Add to crontab
0 9 * * * docker compose exec -T backend python manage.py shell -c "from apps.scheduler.tasks import send_test_email_to_self; send_test_email_to_self.delay()"
```

---

## 4️⃣ Alert System

### A. Email Delivery Failure Alerts

**Create Alert Script:**
```bash
# Save as: scripts/email-failure-alert.sh
#!/bin/bash

THRESHOLD=5  # Alert if more than 5 failures in last hour

FAILURE_COUNT=$(docker compose logs backend celery_worker --since="1h" | grep -i "failed.*email\|error.*smtp" | wc -l)

if [ $FAILURE_COUNT -gt $THRESHOLD ]; then
    echo "🚨 EMAIL ALERT: $FAILURE_COUNT email failures in last hour!"
    
    # Send alert (customize for your notification system)
    # Examples:
    # - Send to admin email
    # - Post to Slack
    # - Create Jira ticket
    
    docker compose logs backend celery_worker --since="1h" | grep -i "failed.*email\|error.*smtp" | tail -20
fi
```

**Run Periodically:**
```bash
# Check every 15 minutes
*/15 * * * * /path/to/edms/scripts/email-failure-alert.sh
```

---

## 5️⃣ Dashboard Monitoring

### A. Create Email Metrics Dashboard

**Django Admin Custom View:**
```python
# backend/apps/scheduler/admin.py
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django_celery_results.models import TaskResult
import datetime

@admin.register(EmailMetrics)
class EmailMetricsAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('email-metrics/', self.admin_site.admin_view(self.email_metrics_view)),
        ]
        return custom_urls + urls
    
    def email_metrics_view(self, request):
        # Last 7 days
        cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
        
        email_tasks = TaskResult.objects.filter(
            task_name__icontains='email',
            date_done__gte=cutoff
        )
        
        context = {
            'total': email_tasks.count(),
            'success': email_tasks.filter(status='SUCCESS').count(),
            'failed': email_tasks.filter(status='FAILURE').count(),
            'by_type': {
                'task_assignment': email_tasks.filter(task_name__contains='send_task_email').count(),
                'document_effective': email_tasks.filter(task_name__contains='send_document_effective').count(),
                'document_obsolete': email_tasks.filter(task_name__contains='send_document_obsolete').count(),
                'test_email': email_tasks.filter(task_name__contains='send_test_email').count(),
            }
        }
        
        return render(request, 'admin/email_metrics.html', context)
```

---

## 6️⃣ User Reporting

### A. User Feedback Collection

**Add "Report Email Issue" Link:**
```typescript
// frontend - in Email Notifications page
<div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded">
  <h4 className="font-semibold">Not receiving emails?</h4>
  <p className="text-sm text-gray-600 mt-1">
    If you're not receiving notification emails, please:
  </p>
  <ol className="text-sm text-gray-600 mt-2 ml-4 list-decimal">
    <li>Check your spam/junk folder</li>
    <li>Verify your email address in profile</li>
    <li>Contact system administrator if issue persists</li>
  </ol>
</div>
```

---

## 7️⃣ Key Metrics to Track

### Daily Metrics
- **Total emails sent**
- **Success rate** (%)
- **Failure count**
- **SMTP errors**
- **Average send time**

### Weekly Metrics
- **Emails by type** (task, effective, obsolete, etc.)
- **Most active users** (who triggers most emails)
- **Peak email hours**
- **Delivery failure patterns**

### Monthly Metrics
- **Total volume trends**
- **Error rate trends**
- **User engagement** (who opens/reads emails)
- **System reliability** (uptime %)

---

## 8️⃣ Troubleshooting Common Issues

### Issue 1: Emails Not Sending
**Check:**
```bash
# 1. Email backend
docker compose exec backend python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"

# 2. Celery workers running
docker compose ps celery_worker

# 3. SMTP credentials
docker compose exec backend python manage.py shell -c "from django.conf import settings; print(f'Host: {settings.EMAIL_HOST}, User: {settings.EMAIL_HOST_USER}')"
```

### Issue 2: High Failure Rate
**Investigate:**
```bash
# Check error patterns
docker compose logs celery_worker --since="1h" | grep -i "error.*email" | sort | uniq -c | sort -rn

# Common causes:
# - Invalid email addresses
# - SMTP quota exceeded
# - Network issues
# - Authentication failures
```

### Issue 3: Slow Email Delivery
**Check:**
```bash
# Monitor send times
docker compose logs celery_worker | grep "Email sent" | grep -oP '\[\d+\.\d+s\]'

# If consistently slow (>5s):
# - Check SMTP server performance
# - Consider email queue
# - Check network latency
```

---

## 9️⃣ Best Practices

### DO ✅
- Monitor logs regularly (daily at minimum)
- Run health checks automatically (hourly/daily)
- Track metrics over time (trends)
- Alert on failures (>threshold)
- Test email delivery weekly
- Keep SMTP credentials secure

### DON'T ❌
- Ignore warnings in logs
- Send too many test emails (spam risk)
- Use console backend in production
- Share SMTP credentials
- Skip monitoring during low activity

---

## 🔟 Quick Reference Commands

```bash
# Real-time monitoring
docker compose logs -f celery_worker | grep email

# Check email config
docker compose exec backend python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"

# Send test email
docker compose exec backend python test_email.py

# Check recent email activity
docker compose logs celery_worker --since="24h" | grep "Email sent" | wc -l

# Check for errors
docker compose logs backend celery_worker --since="24h" | grep -i "error.*email"

# Health check
./scripts/email-health-check.sh
```

---

## ✅ Summary

**3-Layer Monitoring:**
1. **Real-time** - Watch logs continuously
2. **Periodic** - Run health checks hourly/daily
3. **Metrics** - Track trends over time

**Key Indicators:**
- ✅ Emails being sent (count > 0)
- ✅ Low failure rate (<5%)
- ✅ SMTP connection stable
- ✅ Celery workers running
- ✅ No error spikes

**When to Investigate:**
- ❌ Zero emails sent (check if expected)
- ❌ Failure rate >10%
- ❌ SMTP connection errors
- ❌ Celery workers down
- ❌ Error count increasing

---

**Monitoring is ongoing! Set up automated checks and review metrics regularly.** 📊

