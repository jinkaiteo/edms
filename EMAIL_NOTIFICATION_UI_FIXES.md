# 📧 Email Notification System - UI Documentation Fixes

**Date:** January 24, 2026  
**Issue:** Documentation references incorrect UI elements

---

## 🐛 Issues Found

### Issue 1: "Send Test Email" Button Missing in Scheduler
**Documentation Says:** "Go to Scheduler Dashboard → 'Send Test Email' → Click 'Run Now'"

**Reality:** 
- ✅ Task exists in backend code (`send_test_email_to_self`)
- ❌ Task was NOT created in database
- ❌ Frontend cannot display tasks that don't exist in database

**Fix Applied:**
Created the missing periodic task in database with manual-trigger-only schedule.

---

### Issue 2: Settings Tab Shows Blank Page
**Documentation Says:** "Go to Email Configuration → Settings tab"

**Reality:**
- URL: `http://localhost:3000/admin-dashboard?tab=settings`
- ✅ Route exists in code
- ✅ SystemSettings component loads
- ✅ Page is NOT blank - it shows email configuration guide

**Actual Content:**
The Settings tab shows a comprehensive guide with:
1. How to access the server via SSH
2. How to edit the .env file
3. All email configuration variables explained
4. Example configurations for Gmail/Office365
5. How to restart backend services
6. How to test email after configuration

**This is CORRECT behavior** - email settings are server-side environment variables, not database settings.

---

## ✅ Corrected Documentation

### How to Test Email Notifications

#### Option 1: Via Scheduler Dashboard (After Fix)
1. Go to **Admin Dashboard** (http://localhost:3000/administration)
2. Click **"Scheduler Dashboard"** in the sidebar OR quick links
3. Look for **"Send Test Email"** task in the task list
4. Click **"▶️ Run Now"** button next to the task
5. Check your email inbox (admin user's email)

#### Option 2: Via Command Line (Always Works)
```bash
docker compose exec backend python test_email.py
# Follow prompts to send test email
```

#### Option 3: Via Django Shell
```bash
docker compose exec backend python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
send_mail(
    'Test Email',
    'This is a test from EDMS',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@example.com']
)
print('Email sent!')
"
```

---

### How to Configure Email Settings

1. **Access the Settings Guide**
   - Go to: http://localhost:3000/admin-dashboard?tab=settings
   - Click the **"Notifications"** tab
   - Follow the step-by-step SSH instructions shown

2. **OR: Direct Server Access**
   ```bash
   # SSH to server
   ssh your-server
   
   # Edit .env file
   cd /path/to/edms
   nano backend/.env
   
   # Add/update these variables:
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=EDMS System <your-email@gmail.com>
   
   # Restart backend
   docker compose restart backend
   ```

---

## 📝 Updated Email Notification Guide Tab

The **Email Notifications Guide** tab (http://localhost:3000/administration?tab=emails) shows:

### Workflow Notifications (6 types)
1. Submit for Review → Reviewer gets email
2. Review Approved → Author gets email
3. Review Rejected → Author gets email
4. Route for Approval → Approver gets email
5. Document Approved → Author gets email
6. Approval Rejected → Author gets email

### Automated System Notifications (6 types)
1. Document Becomes Effective → Author gets email
2. Scheduled for Obsolescence → Author & stakeholders get email
3. Document Becomes Obsolete → Author & stakeholders get email
4. Document Superseded → Users of old version get email
5. Workflow Timeout → Current assignee gets email
6. Daily Health Report → All admins get email (7 AM daily)

### Test & Configuration Sections
- **Test Email:** "Go to Scheduler Dashboard → 'Send Test Email' → Click 'Run Now'"
- **Configuration:** "Settings → Notifications tab"

**Note:** After the fix, the "Send Test Email" task will now appear in the scheduler!

---

## 🔧 Fix Summary

### What Was Fixed
1. ✅ Created "Send Test Email" periodic task in database
2. ✅ Task now appears in Scheduler Dashboard UI
3. ✅ "Run Now" button is functional
4. ✅ Verified Settings tab is working (not blank)

### What Was NOT Broken
- ❌ Settings tab was never blank - it shows proper configuration guide
- ❌ Email configuration UI is intentionally server-side (correct design)

---

## 🎯 Current Status

### Scheduler Dashboard
- **URL:** http://localhost:3000/administration?tab=scheduler
- **Contains:** All scheduled tasks including "Send Test Email"
- **Action:** Click "▶️ Run Now" to trigger test email

### Settings Tab (Notifications)
- **URL:** http://localhost:3000/admin-dashboard?tab=settings (then click "Notifications" tab)
- **Contains:** Complete guide for configuring email via SSH/environment variables
- **Purpose:** Show admins HOW to configure server-side email settings

### Email Guide Tab
- **URL:** http://localhost:3000/administration?tab=emails
- **Contains:** List of all notification types and when they're sent
- **Purpose:** User-facing documentation of email notification behavior

---

## ✅ Verification Steps

1. **Check Scheduler Task Exists:**
   ```bash
   docker compose exec backend python manage.py shell -c "
   from django_celery_beat.models import PeriodicTask
   task = PeriodicTask.objects.filter(name='Send Test Email').first()
   print(f'Task exists: {task is not None}')
   if task:
       print(f'Name: {task.name}')
       print(f'Enabled: {task.enabled}')
   "
   ```

2. **Check Frontend Shows Task:**
   - Navigate to: http://localhost:3000/administration?tab=scheduler
   - Look for "Send Test Email" in the task list
   - Verify "▶️ Run Now" button is present

3. **Test Manual Trigger:**
   - Click "▶️ Run Now" next to "Send Test Email"
   - Confirm dialog appears
   - Click OK
   - Check email inbox for test email

4. **Verify Settings Tab:**
   - Navigate to: http://localhost:3000/admin-dashboard?tab=settings
   - Click "Notifications" tab at the top
   - Should see 5-step configuration guide

---

## 📋 Updated Documentation Notes

### For Future Documentation Updates

**Correct Phrasing:**
- ✅ "Go to Scheduler Dashboard to manually trigger tasks"
- ✅ "The Settings → Notifications tab shows configuration instructions"
- ✅ "Email settings are configured via environment variables on the server"

**Avoid:**
- ❌ "Go to Email Configuration tab" (tab is called "Notifications" inside Settings)
- ❌ "Settings page is blank" (it's not - it shows a comprehensive guide)
- ❌ "Configure emails in the UI" (emails are server-side configuration)

---

**Fix completed by:** Rovo Dev  
**Date:** January 24, 2026  
**Status:** ✅ Complete - Task created and UI verified

