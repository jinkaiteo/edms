# ✅ Email Integration - SMTP Setup Complete

## Status: Ready to Configure

Email integration has been implemented using basic SMTP. Follow the steps below to activate it.

---

## What Was Implemented

### ✅ Backend Changes
1. **Updated `.env.example`** - Added detailed SMTP configuration examples
2. **Enabled email sending** in `notification_service.py` - All 4 notification types now send real emails
3. **Created test script** - `backend/test_email.py` for testing configuration

### ✅ Notification Types Enabled
- ✅ Task assignment emails
- ✅ Document effective date notifications
- ✅ Document obsolescence notifications  
- ✅ Workflow timeout/overdue alerts

---

## Quick Setup (10 Minutes)

### Step 1: Create App Password

**For Microsoft 365/Outlook:**
1. Go to https://account.microsoft.com/security
2. Click "Advanced security options"
3. Under "App passwords", click "Create a new app password"
4. Copy the generated password (e.g., `abcd efgh ijkl mnop`)

**For Gmail:**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "EDMS" as the name
4. Copy the generated password

### Step 2: Configure Environment Variables

Create or edit `backend/.env` file:

```env
# Email Configuration - Microsoft 365
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourcompany.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=your-email@yourcompany.com
```

**For Gmail, use:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Step 3: Restart Backend

```bash
docker compose restart backend
```

### Step 4: Test Email

```bash
docker compose exec backend python test_email.py
```

The test script will:
1. Show your current email configuration
2. Ask for a recipient email address
3. Send a test email
4. Confirm if it worked

---

## Verification

### Check Email Sent Successfully

**You should see:**
```
✅ Email sent successfully to recipient@example.com!
```

**Check the recipient inbox:**
- Subject: "EDMS Test Email"
- From: your configured email
- Message: "This is a test email from the EDMS system..."

### Common Issues

**Issue 1: "Authentication failed"**
- ✅ Verify App Password is correct (no spaces)
- ✅ Ensure App Password hasn't expired
- ✅ For Microsoft 365, account needs Exchange Online license

**Issue 2: "Connection refused"**
- ✅ Check firewall allows outbound port 587
- ✅ Test with: `telnet smtp.office365.com 587`

**Issue 3: "Email not received"**
- ✅ Check recipient's spam/junk folder
- ✅ Verify FROM address is valid
- ✅ Check email server logs

---

## How Email Works Now

### Automatic Notifications

**Task Assignment:**
When a reviewer or approver is assigned:
```
Subject: New Task Assigned: REVIEW - DOC-001
Body: A new review task has been assigned to you...
```

**Document Effective:**
When a document becomes effective:
```
Subject: Document Now Effective: DOC-001
Body: Document DOC-001 is now effective as of [date]...
```

**Document Obsolete:**
When a document becomes obsolete:
```
Subject: Document Now Obsolete: DOC-001
Body: Document DOC-001 is no longer valid...
```

**Workflow Timeout:**
When a workflow task is overdue:
```
Subject: Overdue Workflow: DOC-001
Body: This workflow is [X] days overdue...
```

### Manual Testing

Test notifications from Django shell:
```python
docker compose exec backend python manage.py shell

>>> from apps.scheduler.notification_service import notification_service
>>> from apps.users.models import User
>>> from apps.documents.models import Document

>>> user = User.objects.first()
>>> doc = Document.objects.first()

>>> # Test task assignment email
>>> notification_service.send_task_email(user, 'REVIEW', doc)
```

---

## Production Considerations

### Current Setup (Development)
- ✅ Using SMTP with App Password
- ✅ Emails sent immediately (synchronous)
- ⚠️ Development mode uses console backend (prints to console)
- ⚠️ No email queue (blocking operations)

### Production Recommendations

**For Production Deployment:**

1. **Switch to Production Settings**
   - Already configured in `backend/edms/settings/production.py`
   - Uses SMTP backend (not console)

2. **Consider Email Queue** (Optional)
   - Use Celery for async email sending
   - Prevents blocking on slow SMTP servers
   - Already have Celery configured in system

3. **Monitor Email Delivery**
   - Check backend logs for email errors
   - Monitor SMTP rate limits (30 emails/min for Office 365)

4. **Upgrade to Microsoft Graph API** (Recommended later)
   - See `EMAIL_INTEGRATION_ANALYSIS.md` for details
   - OAuth2 authentication (more secure)
   - Better rate limits and features

---

## Configuration Reference

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_HOST` | SMTP server hostname | `smtp.office365.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_USE_TLS` | Use TLS encryption | `True` |
| `EMAIL_HOST_USER` | SMTP username (email) | `edms@company.com` |
| `EMAIL_HOST_PASSWORD` | App Password | `abcd efgh ijkl mnop` |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@company.com` |

### Common SMTP Servers

**Microsoft 365:**
- Host: `smtp.office365.com`
- Port: `587`
- TLS: `True`
- Rate Limit: 30 emails/minute

**Gmail:**
- Host: `smtp.gmail.com`
- Port: `587`
- TLS: `True`
- Rate Limit: 100-500 emails/day

**Custom SMTP:**
- Host: Your SMTP server
- Port: Usually `587` (or `465` for SSL)
- TLS: `True` for port 587, `False` for port 465 with SSL

---

## Testing Checklist

- [ ] App Password created
- [ ] `.env` file configured
- [ ] Backend restarted
- [ ] Test email sent successfully
- [ ] Test email received in inbox
- [ ] Notifications working from system

---

## Next Steps

### Now (Basic Email Working):
1. Configure your `.env` file
2. Test with `test_email.py`
3. Verify emails are received

### Later (Production Enhancements):
1. Implement HTML email templates
2. Add email queue with Celery
3. Upgrade to Microsoft Graph API (OAuth2)
4. Add email analytics/tracking

---

## Files Modified

### Backend
- ✅ `backend/.env.example` - Added SMTP configuration examples
- ✅ `backend/apps/scheduler/notification_service.py` - Enabled email sending
- ✅ `backend/test_email.py` - Created test script

### Documentation
- ✅ `EMAIL_INTEGRATION_ANALYSIS.md` - Complete email integration guide
- ✅ `EMAIL_SMTP_SETUP_GUIDE.md` - This quick setup guide

---

## Support

**Having issues?**
1. Run the test script: `docker compose exec backend python test_email.py`
2. Check backend logs: `docker compose logs backend | grep -i email`
3. Verify App Password is active
4. Test SMTP connectivity: `telnet smtp.office365.com 587`

**For advanced features:**
See `EMAIL_INTEGRATION_ANALYSIS.md` for Microsoft Graph API integration.

---

**Status:** ✅ Ready to Configure
**Date:** December 21, 2024
**Estimated Setup Time:** 10 minutes
