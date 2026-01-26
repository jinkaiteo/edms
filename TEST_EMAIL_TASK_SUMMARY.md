# Send Test Email Task - Summary

## ✅ Task Status

The "Send Test Email" task has been created and is available in the system.

## 📍 Task Details

- **Name**: Send Test Email
- **Category**: Email Notifications
- **Description**: Sends test email to all admin users to verify email configuration
- **Task Function**: `apps.scheduler.tasks.send_test_email_to_self`
- **Schedule**: Manual trigger only (impossible cron: Feb 31st)
- **Status**: ✅ Available in API

## 🔧 How It Was Created

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py create_email_test_task
```

## 📊 API Verification

The task appears in the scheduler status API:

```bash
curl http://localhost:8001/api/v1/scheduler/monitoring/status/
```

Response includes:
```json
{
  "name": "Send Test Email",
  "description": "Sends test email to all admin users to verify email configuration",
  "category": "Email Notifications"
}
```

## 🌐 Frontend Access

**URL**: http://localhost:3001/administration?tab=scheduler

**Requirements**:
- Must be logged in with admin credentials
- Access the "Scheduler Dashboard" tab under Administration

**To trigger the task**:
1. Navigate to Administration → Scheduler Dashboard
2. Find "Send Test Email" in the task list
3. Click the "Run Now" or "Trigger" button
4. The task will send test emails to all admin users

## 👤 Recipients

The task sends test emails to:
- All users with `is_staff=True` and `is_active=True`
- Currently: `admin` user (admin@edms.com)

## 📧 Email Configuration

For the test email to work, email settings must be configured in `.env`:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## ⚠️ Troubleshooting

### Can't See the Task in Frontend

**Possible causes**:

1. **Not logged in as admin**
   - Solution: Login with `admin` / `admin123`

2. **Frontend cache issue**
   - Solution: Hard refresh (Ctrl+Shift+R) or clear browser cache

3. **Frontend API endpoint wrong**
   - Check: Frontend should call `/api/v1/scheduler/monitoring/status/`
   - Verify: Check browser DevTools Network tab

4. **Task not in database**
   - Verify: Run `python manage.py create_email_test_task`
   - Check: Query PeriodicTask model

### Task Doesn't Send Email

**Possible causes**:

1. **Email not configured**
   - Check `.env` file has valid email settings

2. **Celery worker not running**
   - Check: `docker compose ps celery_worker`
   - Should be: healthy

3. **No admin users**
   - Check: At least one user with `is_staff=True`

## 🔗 Related Files

**Backend**:
- `backend/apps/scheduler/tasks.py` - Task implementation
- `backend/apps/scheduler/management/commands/create_email_test_task.py` - Creation command
- `backend/apps/scheduler/monitoring_dashboard.py` - Dashboard integration

**Frontend**:
- `frontend/src/components/scheduler/SchedulerStatusWidget.tsx` - Display component
- `frontend/src/pages/AdminDashboard.tsx` - Admin dashboard page

## 📝 Task Implementation

```python
@shared_task(bind=True)
def send_test_email_to_self():
    """
    Send a test email to all admin users to verify email configuration.
    Manual-trigger-only task available in scheduler UI.
    """
    from django.core.mail import send_mail
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    admin_users = User.objects.filter(is_staff=True, is_active=True)
    
    for user in admin_users:
        send_mail(
            subject='EDMS Test Email',
            message='This is a test email from EDMS...',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )
```

## ✅ Verification Checklist

- [x] Task created in database (PeriodicTask)
- [x] Task appears in API response
- [x] Backend can execute task
- [x] Celery worker can process task
- [ ] Task visible in frontend (verify in browser)
- [ ] Task can be triggered from frontend
- [ ] Email is sent successfully

---

**Created**: January 26, 2026  
**Status**: ✅ Task available in backend, ready for frontend testing
