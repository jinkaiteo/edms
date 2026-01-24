# 📧 Email Notification System - Staging Deployment Guide

**Date:** January 24, 2026  
**Target:** Staging Server Deployment  
**Status:** Ready to Deploy

---

## 🎯 Prerequisites

### ✅ Completed (Local Testing)
- [x] SMTP mode tested and working locally
- [x] All 4 notification types verified
- [x] 8 test emails sent successfully
- [x] Configuration documented
- [x] Gmail SMTP credentials validated

### ⚠️ Required Before Deployment
- [ ] Staging server SSH access
- [ ] Git repository access on staging
- [ ] Docker and Docker Compose installed on staging
- [ ] Port 587 outbound allowed (SMTP)
- [ ] Gmail app password available

---

## 📋 Staging Deployment Checklist

### Phase 1: Preparation (5 minutes)

#### 1.1 Backup Current Configuration
```bash
# SSH to staging server
ssh your-staging-server

# Navigate to EDMS directory
cd /path/to/edms

# Backup current .env
cp backend/.env backend/.env.backup.$(date +%Y%m%d_%H%M%S)

# Backup current settings
cp backend/edms/settings/development.py backend/edms/settings/development.py.backup
```

#### 1.2 Verify Current State
```bash
# Check what's currently running
docker compose ps

# Check current email backend
docker compose exec backend python manage.py shell -c "
from django.conf import settings
print('Current backend:', settings.EMAIL_BACKEND)
"

# Note: If console backend, emails are NOT being sent
```

---

### Phase 2: Code Deployment (5 minutes)

#### 2.1 Pull Latest Code
```bash
# Ensure on correct branch
git branch

# Pull latest changes
git pull origin develop

# Verify changes pulled
git log --oneline -5
```

#### 2.2 Verify Files Updated
```bash
# Check if email notification files are present
ls -la backend/apps/scheduler/notification_service.py
ls -la backend/apps/workflows/author_notifications.py
ls -la backend/test_email.py

# Should all exist
```

---

### Phase 3: Configuration (10 minutes)

#### 3.1 Update Environment Variables
```bash
# Edit staging .env file
nano backend/.env

# Add or update these lines:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=jinkaiteo.tikva@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password_here
DEFAULT_FROM_EMAIL=EDMS System <jinkaiteo.tikva@gmail.com>

# Save and exit (Ctrl+O, Enter, Ctrl+X)
```

**Important Notes:**
- Use the **same Gmail app password** as local testing
- Do NOT use regular Gmail password - use app-specific password
- Ensure 2FA is enabled on the Gmail account

#### 3.2 Update Settings File (if needed)
```bash
# Check if development.py has console override
grep "EMAIL_BACKEND" backend/edms/settings/development.py

# If you see: EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Then edit the file:
nano backend/edms/settings/development.py

# Find line 68-69 and comment it out:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Commented to allow SMTP

# Save and exit
```

#### 3.3 Verify Configuration Files
```bash
# Verify .env has correct settings
grep "EMAIL_" backend/.env

# Should show:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=jinkaiteo.tikva@gmail.com
# EMAIL_HOST_PASSWORD=***
# DEFAULT_FROM_EMAIL=EDMS System <jinkaiteo.tikva@gmail.com>
```

---

### Phase 4: Deployment (10 minutes)

#### 4.1 Rebuild Backend Container
```bash
# Stop backend to ensure clean restart
docker compose stop backend

# Rebuild backend image with new settings
docker compose build backend

# Start backend
docker compose up -d backend

# Wait for backend to be healthy
sleep 15
docker compose ps backend
```

#### 4.2 Verify Backend Started Successfully
```bash
# Check backend logs for errors
docker compose logs --tail=50 backend

# Check backend health
curl -f http://localhost:8001/health/ || echo "Backend not responding"

# Verify email backend is SMTP
docker compose exec backend python manage.py shell -c "
from django.conf import settings
print('Email Backend:', settings.EMAIL_BACKEND)
assert 'smtp' in settings.EMAIL_BACKEND.lower(), 'ERROR: Not in SMTP mode!'
print('✅ SMTP Mode Active')
"
```

**Expected Output:**
```
Email Backend: django.core.mail.backends.smtp.EmailBackend
✅ SMTP Mode Active
```

---

### Phase 5: Testing (15 minutes)

#### 5.1 Test SMTP Connection
```bash
# Test basic SMTP connectivity
docker compose exec backend python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('✅ SMTP connection successful')
server.quit()
"
```

#### 5.2 Send Test Email
```bash
# Use built-in test script
docker compose exec backend python test_email.py

# Or manually via shell:
docker compose exec backend python manage.py shell <<'PYEOF'
from django.core.mail import send_mail
from django.conf import settings

try:
    result = send_mail(
        subject='🧪 EDMS Staging - Email Test',
        message='This is a test email from the EDMS staging environment to verify email notifications are working.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['jinkaiteo.tikva@gmail.com'],
        fail_silently=False,
    )
    print(f'✅ Test email sent! (return code: {result})')
    print('📬 Check inbox: jinkaiteo.tikva@gmail.com')
except Exception as e:
    print(f'❌ Failed: {e}')
PYEOF
```

#### 5.3 Test Notification Service Methods
```bash
docker compose exec backend python manage.py shell <<'PYEOF'
from apps.scheduler.notification_service import notification_service
from django.contrib.auth import get_user_model
from apps.documents.models import Document

User = get_user_model()

print('=== Testing Notification Service ===\n')

# Get test user and document
user = User.objects.filter(email__isnull=False).exclude(email='').first()
document = Document.objects.first()

if not user:
    print('❌ No users with email found')
    exit(1)

if not document:
    print('❌ No documents found')
    exit(1)

print(f'Test user: {user.username} ({user.email})')
print(f'Test document: {document.document_number}\n')

# Test 1: Task Assignment
result1 = notification_service.send_task_email(user, 'Test Review', document)
print(f'1. Task Assignment: {"✅" if result1 else "❌"}')

# Test 2: Document Effective
result2 = notification_service.send_document_effective_notification(document)
print(f'2. Document Effective: {"✅" if result2 else "❌"}')

# Test 3: Document Obsolete
result3 = notification_service.send_document_obsolete_notification(document)
print(f'3. Document Obsolete: {"✅" if result3 else "❌"}')

if result1 and result2 and result3:
    print('\n✅✅✅ All notification methods working!')
    print('📬 Check inbox for 3 test emails')
else:
    print('\n❌ Some notifications failed')
PYEOF
```

#### 5.4 Test Real Workflow (Manual)
1. **Open staging frontend** in browser
2. **Log in as author01**
3. **Create or edit a document**
4. **Submit for review**
5. **Check if reviewer receives email** (should arrive within 60 seconds)
6. **Log in as reviewer01**
7. **Approve or reject the document**
8. **Check if author receives email** with approval/rejection notice

---

### Phase 6: Verification (10 minutes)

#### 6.1 Monitor Logs
```bash
# Watch backend logs for email activity
docker compose logs -f backend | grep -i "email\|smtp"

# In another terminal, check for errors
docker compose logs backend | grep -i "failed\|error" | grep -i email
```

#### 6.2 Check Email Delivery
- [ ] Test email received in Gmail inbox
- [ ] Task assignment email received
- [ ] Document effective email received
- [ ] Document obsolete email received
- [ ] Workflow action emails received (if tested)

**If emails in spam folder:**
- Mark as "Not Spam"
- Add sender to contacts
- Future emails should go to inbox

#### 6.3 Verify Celery Tasks (Scheduled Notifications)
```bash
# Check Celery Beat is running
docker compose ps celery_beat

# Check scheduled tasks
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
tasks = PeriodicTask.objects.filter(enabled=True)
print(f'Active scheduled tasks: {tasks.count()}')
for task in tasks:
    print(f'  - {task.name}')
"

# Expected tasks:
# - process_effective_dates
# - process_obsolete_documents
# - check_workflow_timeouts
# (and others)
```

---

### Phase 7: Rollback Plan (If Needed)

If something goes wrong, use this rollback procedure:

#### 7.1 Restore Configuration
```bash
# Find backup file
ls -la backend/.env.backup.*

# Restore backup
cp backend/.env.backup.YYYYMMDD_HHMMSS backend/.env

# Restore settings if modified
cp backend/edms/settings/development.py.backup backend/edms/settings/development.py
```

#### 7.2 Rebuild and Restart
```bash
# Rebuild backend
docker compose build backend

# Restart services
docker compose restart backend

# Verify system is back to previous state
docker compose exec backend python manage.py shell -c "
from django.conf import settings
print('Email Backend:', settings.EMAIL_BACKEND)
"
```

#### 7.3 Verify Rollback
```bash
# Check backend is healthy
curl -f http://localhost:8001/health/

# Check frontend is accessible
curl -f http://localhost:3001/

# System should be back to console mode (emails to logs only)
```

---

## 📊 Post-Deployment Monitoring

### Day 1: Active Monitoring
```bash
# Monitor email activity (run in background)
docker compose logs -f backend | grep -i "email" > email_monitoring.log &

# Check every hour:
tail -50 email_monitoring.log

# Look for:
# - ✅ "Email sent to..." (success)
# - ❌ "Failed to send email" (failure)
# - ⚠️  SMTP errors
```

### Week 1: Daily Checks
1. **Check email delivery rate**
   ```bash
   docker compose logs backend | grep "Email sent" | wc -l
   docker compose logs backend | grep "Failed to send" | wc -l
   ```

2. **Monitor Celery tasks**
   ```bash
   docker compose logs celery_beat | grep notification
   docker compose logs celery_worker | grep email
   ```

3. **Check for errors**
   ```bash
   docker compose logs backend | grep -i "smtp error\|connection refused\|authentication failed"
   ```

---

## 🐛 Troubleshooting

### Issue 1: Backend Not Starting
**Symptom:** `docker compose up -d backend` fails

**Solution:**
```bash
# Check backend logs
docker compose logs backend

# Common issues:
# - Syntax error in settings file
# - Missing environment variable
# - Database connection issue

# Fix and rebuild
docker compose build --no-cache backend
docker compose up -d backend
```

---

### Issue 2: Still in Console Mode
**Symptom:** `EMAIL_BACKEND` shows console, not SMTP

**Solution:**
```bash
# Check if development.py overrides it
grep "EMAIL_BACKEND" backend/edms/settings/development.py

# If found, comment it out:
nano backend/edms/settings/development.py
# Comment the line

# Restart backend
docker compose restart backend

# Verify again
docker compose exec backend python manage.py shell -c "
from django.conf import settings
print(settings.EMAIL_BACKEND)
"
```

---

### Issue 3: SMTP Authentication Failed
**Symptom:** "Authentication failed" or "Username and password not accepted"

**Solution:**
```bash
# 1. Verify Gmail account has 2FA enabled
# 2. Generate new app password:
#    - Go to: https://myaccount.google.com/apppasswords
#    - Generate new password
#    - Update .env file

# 3. Update password in .env
nano backend/.env
# Update EMAIL_HOST_PASSWORD

# 4. Restart backend
docker compose restart backend
```

---

### Issue 4: Emails Going to Spam
**Symptom:** Emails sent but not in inbox

**Solution:**
1. Check **Spam/Junk** folder in Gmail
2. Mark EDMS emails as "Not Spam"
3. Add sender to contacts: `jinkaiteo.tikva@gmail.com`
4. For production, consider:
   - Using a custom domain
   - Setting up SPF records
   - Setting up DKIM signing

---

### Issue 5: No Emails Received
**Symptom:** Backend says "Email sent" but nothing received

**Checklist:**
```bash
# 1. Verify SMTP mode is active
docker compose exec backend python manage.py shell -c "
from django.conf import settings
print(settings.EMAIL_BACKEND)
"
# Must be: django.core.mail.backends.smtp.EmailBackend

# 2. Test SMTP connection
docker compose exec backend python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('Connection OK')
server.quit()
"

# 3. Check firewall allows outbound port 587
telnet smtp.gmail.com 587
# Should connect

# 4. Verify recipient email is correct
docker compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='author01')
print('Email:', user.email)
"

# 5. Check backend logs for actual error
docker compose logs backend | grep -i "email" | tail -50
```

---

## ✅ Success Criteria

Deployment is successful when:

- [ ] Backend starts without errors
- [ ] SMTP mode is active (`EMAIL_BACKEND` = smtp)
- [ ] Test email sent successfully
- [ ] All 3 notification methods work
- [ ] Real workflow triggers email (submit for review)
- [ ] Emails arrive in inbox within 60 seconds
- [ ] No errors in backend logs
- [ ] Celery tasks are running

---

## 📞 Support & References

### Quick Commands Reference
```bash
# Check email backend
docker compose exec backend python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"

# Send test email
docker compose exec backend python test_email.py

# Monitor email logs
docker compose logs -f backend | grep -i email

# Check for errors
docker compose logs backend | grep -i "failed.*email"

# Restart backend
docker compose restart backend

# Full rebuild
docker compose build backend && docker compose up -d backend
```

### Documentation Links
- Local test results: `EMAIL_NOTIFICATION_LOCAL_TEST_COMPLETE.md`
- Configuration guide: `EMAIL_SMTP_SETUP_GUIDE.md`
- Technical details: `EMAIL_NOTIFICATION_STATUS_SUMMARY.md`
- Integration analysis: `EMAIL_INTEGRATION_ANALYSIS.md`

### Support Contacts
- Email issues: Check Gmail settings at https://myaccount.google.com/
- SMTP issues: Verify port 587 is accessible
- App password: Generate at https://myaccount.google.com/apppasswords

---

## 🎯 Summary

This guide provides step-by-step instructions for deploying the email notification system to staging. Follow each phase carefully, verify success at each step, and use the troubleshooting section if issues arise.

**Estimated Total Time:** 45-60 minutes

**Phases:**
1. Preparation: 5 min
2. Code Deployment: 5 min
3. Configuration: 10 min
4. Deployment: 10 min
5. Testing: 15 min
6. Verification: 10 min
7. Rollback (if needed): 10 min

**Next Step:** Begin Phase 1 - Preparation

---

**Guide created by:** Rovo Dev  
**Date:** January 24, 2026  
**Version:** 1.0  
**Status:** Ready for Use  

