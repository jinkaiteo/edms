# 🔧 Staging Fix: Add "Send Test Email" Task

**Issue:** Staging server only shows 9 tasks (missing "Send Test Email")  
**Cause:** Task exists in local database but not in staging database  
**Solution:** Run management command to create the task

---

## 🎯 Quick Fix (On Staging Server)

### Step 1: SSH to Staging
```bash
ssh your-staging-server
cd /path/to/edms
```

### Step 2: Pull Latest Code
```bash
git pull origin main
```

### Step 3: Run Management Command
```bash
docker compose exec backend python manage.py create_email_test_task
```

**Expected Output:**
```
Creating "Send Test Email" task...
  Created impossible crontab schedule (manual trigger only)
✓ Successfully created task: Send Test Email
  Task function: apps.scheduler.tasks.send_test_email_to_self
  Schedule: Manual trigger only
  Description: Sends test email to verify email configuration. Manual trigger only.

✓ "Send Test Email" task is now available in Scheduler Dashboard
```

### Step 4: Restart Frontend (Clear Cache)
```bash
docker compose restart frontend
```

### Step 5: Verify in Browser
1. Clear browser cache (Ctrl+Shift+R)
2. Go to: Scheduler Dashboard
3. Should now see **10 tasks** including "Send Test Email"

---

## 📊 Why This Happened

### The Issue:
- **PeriodicTask** records are stored in the **database**, not code
- Local database has the task (created during testing)
- Staging database doesn't have it (fresh/older database)
- TaskMonitor now reads from database → missing task = only 9 tasks shown

### The Fix:
- Created management command to add the task
- Command is **idempotent** (safe to run multiple times)
- Task uses impossible schedule (Feb 31st) so it never runs automatically
- Only accessible via "Run Now" manual trigger

---

## 🚀 For Future Deployments

### Option 1: Include in Deployment Script (RECOMMENDED)
Add to `deploy-interactive.sh` or deployment scripts:
```bash
# After database migrations
python manage.py create_email_test_task
```

### Option 2: Add to Initialization Script
If you have a `scripts/initialize-database.sh`:
```bash
# Add after creating users/roles
python manage.py create_email_test_task
```

### Option 3: Manual After Each Deployment
Run the command manually after deploying to new environments.

---

## ✅ Verification

After running the command on staging:

```bash
# Check task was created
docker compose exec backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
task = PeriodicTask.objects.filter(name='Send Test Email').first()
if task:
    print(f'✅ Task exists: {task.name}')
else:
    print('❌ Task not found')
"

# Check API returns 10 tasks
docker compose exec backend python manage.py shell -c "
from apps.scheduler.task_monitor import TaskMonitor
monitor = TaskMonitor()
status = monitor.get_task_status()
print(f'Total tasks: {len(status[\"tasks\"])}')
"
# Should output: Total tasks: 10
```

---

## 📝 Summary

**Problem:** Staging shows 9 tasks, local shows 10  
**Cause:** Database record missing (not code issue)  
**Fix:** Run `create_email_test_task` management command  
**Time:** 30 seconds  
**Committed:** ✅ Yes (commit b5e8d27)  

---

**Run the command on staging now and you'll see all 10 tasks!** 🚀

